# Redkeep desktop app — Tauri migration plan

Status: **plan only — not started.** Nothing in this document has been implemented.
Written 13 Nov 2026 against the launcher as it stands (`ui/server.py`, 292 lines; `ui/index.html`,
659 lines; uncommitted Keep redesign included).

## 1. Goal and non-goals

**Goal.** Ship Redkeep as an installable desktop application (`.exe`/`.msi` on Windows first,
then `.dmg` and AppImage/`.deb`) that replaces the "run `start-redkeep.bat`, a Python server opens
a browser tab" launcher with a native window — while keeping the isolated-lab design, the
command whitelist, the no-idle rule and the Keep UI.

**Non-goals.**
- **Not** porting the scanner. The `vapt` runner stays Python inside the Kali toolbox image;
  nmap/ZAP/nuclei/nikto/schemathesis/newman are external tools and gain nothing from Rust.
- **Not** redrawing the UI. `ui/index.html` stays the UI; Tauri hosts it in the system webview.
  No pure-Rust GUI toolkit (egui/iced/Slint) — that would throw away the Keep design.
- **Not** bundling a container runtime. The app requires a Docker-compatible runtime and guides
  the user to install/start one (§7).
- **Not** adding a tray icon, background service, autostart, telemetry or auto-scan. Closing
  the window quits the app (the no-idle rule).

## 2. What exists today (the thing being replaced)

| Piece | Today | Fate |
|---|---|---|
| Launcher server | `ui/server.py` — stdlib `ThreadingHTTPServer` on 127.0.0.1:8765, opens the browser | **Ported to Rust** (Tauri backend) |
| UI | `ui/index.html` — fetches `/api/status`, `/api/job`, posts `/api/exec`, `/api/stop`; polls every 1.5 s (job) / 15 s (status) | **Kept**, behind a small API adapter |
| Reports | served at `/report/<run>/report.html`; opened in a new tab | **Opened in their own app window** |
| Static assets | `/resources/*` (logo, favicon); fonts from Google Fonts | **Bundled**; fonts become local `@font-face` |
| Start scripts | `start-redkeep.bat` / `.sh` | Kept for dev mode; the installed app replaces them |
| Runner | `runner/vapt` (Python) in `redkeep/kali-toolbox:latest`, repo mounted at `/redkeep` | **Unchanged code**; image published + runner baked in (§6) |
| Lab | `lab/docker-compose.yml` (project `redkeep-lab`, six `target-*` services, `kali` behind profile `tools`) | Unchanged services; mount paths parameterised (§5) |

Server routes and functions to port, one to one:

| Python | Purpose | Rust replacement |
|---|---|---|
| `GET /api/status` → `_docker_ok`, `_lab_state`, `_profiles`, `_targets`, `_runs` | Header, metric strip, chart, reports, lab gating | `#[tauri::command] get_status()` |
| `GET /api/job` → `_job_view` (status, label, started, returncode, last 8000 chars of log) | Keep panel, Scanning button | `get_job()` for initial state **+ events** `job:state`, `job:log` |
| `POST /api/exec` → `_start_job` / `_command_for` (whitelist: `lab-up`, `lab-down`, `down-all`, `report`, `scan{domain,profile}`) | Every button | `exec(action: JobRequest)` with a typed enum |
| `POST /api/stop` | Stop job | `stop_job()` |
| `TEARDOWN_ACTIONS` + `_terminate_running` | Stop lab / Stop everything pre-empt a job | Same rule in `job.rs` |
| `GET /report/<run>/report.html` | Open a report | `open_report(run)` → new `WebviewWindow` via a custom `report://` protocol |
| `GET /resources/*` | Logo, favicon | Bundled into `frontendDist` |

## 3. Target architecture

```
┌──────────── Redkeep.exe (Tauri v2) ─────────────┐
│  Webview: ui/index.html  ──invoke/events──┐     │
│                                           ▼     │
│  Rust core: commands · job runner · status ·    │
│             docker detection · paths · reports  │
└──────────────────────┬──────────────────────────┘
                       │ spawns (whitelisted argv only)
                       ▼
        docker / docker compose  (user's runtime)
                       │
     ┌─────────────────┴──────────────────┐
     ▼                                    ▼
 redkeep-lab targets               kali toolbox (ephemeral, --rm)
 (target-db, target-api, …)        vapt runner → reports in workspace
```

Principles:
- **CLI, not the Engine API.** Keep shelling out to `docker` / `docker compose` with fixed argv
  (as today). This works unchanged with Docker Desktop, Rancher Desktop, Podman's Docker shim
  and Docker Engine, and keeps the whitelist auditable. (The `bollard` crate is an option later
  only for richer image-pull progress — see §6.)
- **No shell.** `std::process::Command`/`tokio::process::Command` with an argv vector; no
  `cmd /c`, no string interpolation, no Tauri shell plugin.
- **One job at a time**, same as today.

## 4. Repository layout

```
redkeep/
  desktop/
    src-tauri/
      Cargo.toml
      tauri.conf.json          # frontendDist: "../../ui", identifier, bundle targets
      capabilities/default.json # only Redkeep's own commands + opener for reports folder
      icons/                    # generated from resources/redkeep-logo (cargo tauri icon)
      src/
        main.rs                 # thin: calls lib::run()
        lib.rs                  # builder, state, command registration, window-close handling
        paths.rs                # dev vs installed mode; resource dir; workspace dir (§5)
        docker.rs               # detect runtime, compose v2 check, start Docker Desktop (§7)
        status.rs               # profiles, targets (YAML), runs (summary.json), lab state
        job.rs                  # JobRequest enum → argv, spawn, log streaming, stop, teardown pre-emption
        reports.rs              # report:// protocol, open_report window, reveal folder
        image.rs                # toolbox image present? pull with progress (§6)
      tests/                    # whitelist, parsing, lab state
  ui/
    index.html                  # unchanged look; gains api.js adapter
    api.js                      # NEW: invoke() in Tauri, fetch() in browser dev mode
    fonts/ (or reuse resources/fonts) # local @font-face, no Google Fonts in the app
  ui/server.py                  # kept as the dev / headless launcher (decision D3)
```

No Node toolchain: Tauri can serve a static `frontendDist`, and the CLI installs with
`cargo install tauri-cli` (`cargo tauri dev|build`). This keeps Redkeep dependency-light.

## 5. Paths: dev mode vs installed mode

Today everything assumes the **repo root**: `config.yaml`, `lab/docker-compose.yml`,
`runner/profiles`, `reports/output`, `reports/output/.jobs`, and the toolbox mounts `../` at
`/redkeep`. An installed app has no repo, so split into two roots:

| Root | Dev mode (repo checkout) | Installed mode | Contents |
|---|---|---|---|
| **Resource dir** (read-only, ships with the app) | repo root | Tauri resource dir (install folder) | `lab/docker-compose.yml`, `lab/kali/` (build context, optional), `runner/profiles/*.yaml`, `config.example.yaml`, `lab/*.env.example` |
| **Workspace** (user data, writable) | repo root | `%APPDATA%\Redkeep` · `~/Library/Application Support/Redkeep` · `~/.local/share/redkeep` | `config.yaml`, `lab/.env`, `lab/target/.env`, `reports/output/**`, `reports/output/.jobs/*.log` |

Mode detection (`paths.rs`): `REDKEEP_HOME` env var wins; else, if the executable sits inside a
checkout containing `lab/docker-compose.yml` and `runner/vapt`, use dev mode; else installed mode.

Compose change (works for both modes, keeps `make` and the Python launcher working):

```yaml
  kali:
    image: ${REDKEEP_TOOLBOX_IMAGE:-redkeep/kali-toolbox:latest}
    volumes:
      - ${REDKEEP_WORKSPACE:-..}:/redkeep-work:rw
    working_dir: /redkeep-work
    environment:
      REDKEEP_CONFIG: /redkeep-work/config.yaml
```

Plus, in dev mode only, a second mount of the repo's `runner/` over the baked-in copy so code
edits apply without a rebuild (today's behaviour). The runner already honours `REDKEEP_CONFIG`
(`runner/vapt/config.py:21`) and `output_dir` (`config.py:54`, default `reports/output`,
relative to the working dir) — so no runner change is needed for paths.

The app passes `REDKEEP_WORKSPACE`, `REDKEEP_TOOLBOX_IMAGE` and `--project-directory` explicitly
on every compose call, so nothing depends on the process's current directory.

**First run in installed mode:** create the workspace; copy `config.example.yaml` →
`config.yaml` and the two `.env.example` files; open a "Configure targets" screen (or the file,
see D6). The runner's target allowlist (`targets.py`, 18 tests) stays the only safety gate.

**Watch out:** the Windows user profile path can contain spaces (e.g. `C:\Users\First Last\…`).
Every mount and argv must be passed as a separate argument, never concatenated; add a test with
a spaced workspace path. Docker Desktop (WSL2 backend) shares all drives by default; Rancher
and Podman need the path inside their shared mounts — the onboarding check (§7) should verify a
mount works with a tiny `docker run --rm -v <workspace>:/w alpine ls /w` (alpine is small; or
reuse the toolbox image once pulled).

## 6. The toolbox image: publish instead of build

A new user must not build a 5.9 GB image (it takes long and has failed before on network and
template downloads). Plan:

1. **Bake the runner into the image.** Dockerfile copies `runner/`, `reports/templates/` and
   `resources/fonts/` to `/opt/redkeep` and sets `PYTHONPATH=/opt/redkeep/runner`. The report
   code finds templates/fonts relative to the package (`report.py` uses `parents[2]`), so the
   copied layout must mirror the repo (`/opt/redkeep/{runner,reports/templates,resources/fonts}`).
   Dev mode overlays the live `runner/` via a mount.
2. **Publish to GHCR** from CI on tag: `ghcr.io/<owner>/redkeep-kali-toolbox:<app-version>` and
   `:latest`; amd64 first, arm64 later (Apple Silicon) after checking nuclei/ZAP/Kali arm64.
   This is the deferred "Tier 4" CI item; add SBOM + provenance + cosign signing there.
3. **Pin per app version.** The app knows its matching tag (`REDKEEP_TOOLBOX_IMAGE`), so an app
   release and its runner never drift — which is exactly the `defusedxml` failure we hit
   (image built before a runner dependency was added).
4. **First-run pull with progress.** `image.rs` runs `docker image inspect <tag>`; if missing,
   shows a download screen and runs `docker pull <tag>`, parsing its per-layer progress lines
   (or, if that proves too fragile, uses `bollard`'s structured pull stream for this one call).
   Show size up front ("about 6 GB download") and allow cancel.
5. **Updates:** a new app version references a new tag → pull on next launch; offer
   "remove old toolbox images" to reclaim disk.

## 7. Container runtime onboarding

`docker.rs` resolves a state machine on launch and on "Check again":

| State | Detection | Screen |
|---|---|---|
| **No CLI** | `docker` not on PATH (also check Docker Desktop's default install path on Windows/macOS, since GUI apps may not inherit the shell PATH) | "Redkeep needs a container runtime" — links: Docker Desktop, Rancher Desktop, Podman Desktop, Docker Engine (Linux), Colima (macOS); note on Docker Desktop licensing for larger companies; Windows: WSL2 + virtualisation prerequisite link. **Check again** button. |
| **CLI, no engine** | `docker version` fails to reach the server | "Docker is installed but not running" — **Start Docker** (Windows: launch `Docker Desktop.exe`; macOS: `open -a Docker`), then poll `docker info` up to ~90 s with a spinner. |
| **No compose v2** | `docker compose version` fails | "Docker Compose v2 is required" + link. |
| **Mount check fails** | test mount of the workspace (§5) fails | Explain file sharing for the detected runtime. |
| **No toolbox image** | `docker image inspect` fails | Download screen (§6). |
| **Ready** | all pass | The normal launcher. |

Lab and scan buttons stay disabled until Ready. The existing `docker offline` header state
stays for runtime loss mid-session. The app never installs a runtime itself.

## 8. Rust core in detail

**Crates (pin exact versions at implementation time):** `tauri` v2, `tokio` (process, io,
sync, time), `serde`/`serde_json`, a maintained YAML crate for reading `config.yaml` (evaluate
the current state of the `serde_yaml` successors before choosing), `thiserror`,
`dirs`/Tauri path API, `tauri-plugin-opener` (reveal reports folder), `tauri-plugin-updater`
(optional, §10). No `tauri-plugin-shell`.

**Commands** (all `async`, all returning typed results; errors as `{error: string}` like today):

| Command | Returns / does |
|---|---|
| `get_status()` | `{docker, lab:{state,running,total}, profiles, targets, runs}` — identical JSON shape to `/api/status`, so the UI code barely changes |
| `get_job()` | `{status, label, started, returncode, log}` (log tail ≤ 8000 chars, same as now) |
| `exec(req)` | `req` is `#[serde(tag="action")] enum JobRequest { LabUp, LabDown, DownAll, Report, Scan{domain: Domain, profile: Profile} }`; `Domain` is an enum (`run/network/web/api`), `Profile` validated against `runner/profiles/*.yaml` names (stricter than today's `isalnum`) |
| `stop_job()` | stops the running job (see below) |
| `open_report(run)` | validates `run` is a direct child of `reports/output` with a `report.html`, opens a `WebviewWindow` titled "Report — <run>" at `report://<run>/report.html` |
| `reveal_reports()` | opens the workspace `reports/output` in Explorer/Finder |
| `runtime_state()` / `start_runtime()` / `pull_toolbox()` | onboarding (§7, §6) |

**Job runner (`job.rs`):**
- `Mutex<JobState>` in Tauri managed state; `status`, `label`, `started` (epoch secs),
  `returncode`, `child`, `logfile`, `container_name`.
- Spawn with piped stdout/stderr merged; a task reads lines, appends to the log file in
  `.jobs/`, and emits `job:log` events (batched every ~200 ms) and `job:state` on transitions.
  The UI keeps a 1.5 s `get_job()` poll as a fallback for the first release.
- **Stopping actually stops the container.** Killing the `docker compose run` client does not
  reliably stop the container it started (especially on Windows, where today's
  `proc.terminate()` is `TerminateProcess` on the CLI). Name every toolbox run
  (`run --rm --name redkeep-job-<id> kali …`); `stop_job()` sends `docker stop -t 10
  redkeep-job-<id>`, then kills the CLI process, then `docker rm -f` if needed. Verify the same
  gap in the current Python launcher and fix it there too.
- Teardown pre-emption (`lab-down`, `down-all` interrupt a job) stays, using the same stop path.
- **Window close / app quit:** if a job runs, ask "A scan is running. Quit and stop it?" (Stop &
  quit / Cancel). On quit, stop the job as above. Nothing survives the app (no-idle rule).

**Status (`status.rs`):** straight ports of `_profiles` (glob `*.yaml`), `_targets` (YAML: names
of web/api/network targets + `defectdojo.enabled`; no more "install pyyaml" note), `_runs`
(25 newest dirs, `report.html` exists, `summary.json` counts/total), `_lab_state` (`docker compose
ps --services --status running` ∩ the six targets → up/partial/down/unknown). Run the docker
calls concurrently and cache `get_status` for ~2 s so overlapping polls don't fan out.

## 9. UI changes (`ui/index.html`)

Small and mechanical; the Keep design is untouched.
1. **`api.js` adapter** — `api.status()`, `api.job()`, `api.exec(req)`, `api.stop()`,
   `api.openReport(run)`, `api.onJob(cb)`. In Tauri (`window.__TAURI__` present) it uses
   `invoke`/`listen`; otherwise `fetch` against `server.py`. The five `getJSON` call sites
   (`index.html` ~lines 341–627) switch to it.
2. **Live log via events**, with the existing poll as fallback. The Scanning estimate keeps
   working (it already prefers `started` from the job).
3. **Reports:** `open report` and row click call `api.openReport(run)` instead of
   `window.open`; the report's "back to launcher" link stays hidden there automatically (it
   only shows under an `http(s):` `/report/…` path) — verify on Windows, where custom
   protocols are served as `http://report.localhost/…`.
4. **Fonts local:** replace the Google Fonts `<link>` with `@font-face` for
   `resources/fonts/inter.woff2` and `jetbrains-mono-{400,500,700}.woff2` (already in the repo).
   The app then works offline and makes no third-party request.
5. **Copy:** header `127.0.0.1 only` → `local app` (Tauri) / unchanged (browser); footer text
   about "close its window or press Ctrl+C" → "Closing Redkeep stops it; nothing keeps running."
6. **Onboarding screens** (§7) and the **download screen** (§6) — new sections in the same
   page, shown instead of the main grid until Ready; built from existing components (panel,
   `.lbl`, buttons, hatch, battlements for "working").
7. `localStorage` (scan durations, last scope/profile) keeps working — the webview has its own
   persistent origin.

## 10. Security

- **Capabilities:** the window may call only Redkeep's commands; report windows get **no**
  command access (they are static HTML). No shell plugin, no `fs` plugin exposed to JS.
- **CSP** in `tauri.conf.json`: `default-src 'self'; style-src 'self' 'unsafe-inline';
  font-src 'self' data:; img-src 'self' data:; script-src 'self'` (inline scripts move into
  `index.js` so `'unsafe-inline'` isn't needed for scripts). Report windows: `script-src
  'unsafe-inline'` only for the four-line back-link script, or drop that script in-app.
- **Whitelist preserved** as Rust enums; nothing from the UI reaches argv except validated enum
  values and a profile name checked against the shipped profile list.
- **`report://` protocol** resolves only inside the workspace `reports/output`, canonicalises
  the path and rejects anything outside (same check as `server.py` today).
- **No network listener** — the app no longer opens port 8765 at all. This closes a gap in
  the launcher as it was: `server.py` accepted any POST to `/api/exec` and `/api/stop` with no origin,
  token or content-type check (it `json.loads`-ed the raw body), so any local process — and any web
  page open in the user's browser, via a "simple" cross-site `text/plain` POST — could start a
  scan or tear the lab down. **Fixed in `server.py` on 13 Nov 2026, ahead of this migration:**
  every request must name `127.0.0.1:<port>`/`localhost:<port>` in `Host` (stops DNS
  rebinding); POSTs must have a matching `Origin` (when sent), must not be marked
  `Sec-Fetch-Site: cross-site|same-site`, must be `Content-Type: application/json`, and are
  capped at 64 KB. Tests: `ui/tests/test_server_guard.py` (run in CI). The Tauri app has no
  listener, so these guards apply only to the dev/headless launcher (D3).
- **Updater** (optional): signed manifests with a Tauri updater key; the private key lives in CI
  secrets only.
- **Code signing:** Windows (OV/EV certificate or Azure Trusted Signing) to avoid SmartScreen
  warnings; macOS Developer ID + notarisation (Apple Developer Program). Unsigned builds are
  fine for personal use and testing.

## 11. Packaging and CI

- **Bundles:** Windows NSIS `.exe` (+ optional MSI), WebView2 via the downloader bootstrapper
  (Windows 11 already has it); macOS `.dmg` (universal or per-arch); Linux AppImage + `.deb`.
- **Bundled resources:** `lab/docker-compose.yml`, `lab/kali/**` (only needed for "build image
  locally" in dev; can be excluded from release bundles), `runner/profiles/*.yaml`,
  `config.example.yaml`, `lab/.env.example`, `lab/target/.env.example`.
- **CI additions** (`.github/workflows/`):
  - `ci.yml`: new job `desktop` — `cargo fmt --check`, `cargo clippy -D warnings`, `cargo test`
    (Ubuntu with webkit2gtk deps), plus the existing Python jobs unchanged.
  - `release.yml` (on tag `v*`): build/publish toolbox image to GHCR (§6), then a Windows/macOS/
    Linux matrix with `tauri-apps/tauri-action` producing signed bundles and a draft GitHub
    Release with the updater manifest.
  - `image-smoke.yml` keeps probing tools, now against the published tag.
- Version source of truth: `desktop/src-tauri/tauri.conf.json` `version`, mirrored into the
  image tag.

## 12. Testing

**Automated (Rust):**
- Whitelist: every `JobRequest` → exact argv; invalid domain/profile rejected; profile not in
  the shipped list rejected (mirrors the intent of `runner/tests/test_targets.py`'s safety focus).
- Lab state parsing: `kali` + one-off containers ignored; up/partial/down/unknown.
- Runs listing: dotted dirs skipped, missing/corrupt `summary.json` tolerated, 25-cap, ordering.
- Paths: dev vs installed detection; workspace with spaces; report path traversal rejected.
- Label parsing for the Scanning estimate stays in JS (already covered by manual checks).

**Manual matrix (per release, Windows first):**

| Case | Expected |
|---|---|
| No Docker installed | "needs a container runtime" screen; buttons disabled |
| Docker installed, stopped | Start Docker works; app becomes Ready |
| Rancher Desktop instead of Docker Desktop | Ready; scan works |
| No toolbox image | download screen with progress; cancel works; resume works |
| Quick scan vs Juice Shop stand-in | live log streams; Scanning bar; report appears; report opens in its own window |
| Stop job mid-scan | container really gone (`docker ps -a` shows no `redkeep-job-*`) |
| Close window mid-scan | confirm dialog; on quit, nothing left running |
| Stop lab during a scan | confirmation (current behaviour) |
| Workspace path with spaces | scans and reports work |
| Offline after image pulled | app and fonts load; scans against the lab work |

## 13. Phases, estimates and exit criteria

Estimates are focused working days for one developer familiar with the codebase. (Porting the
backend alone is ~2–4 days; the rest is onboarding, distribution and packaging.)

| # | Phase | Est. | Exit criteria |
|---|---|---|---|
| 0 | **Spike** — Tauri v2 window loading `ui/index.html`; one `get_status` command | 0.5 d | Native window shows the launcher with live status on Windows 11 |
| 1 | **Paths + compose** — resource/workspace split, compose env vars, dev-mode overlay | 0.5–1 d | `make scan` and `server.py` still work unchanged; app finds compose in both modes |
| 2 | **Rust backend parity** — status, job runner, exec/stop, teardown pre-emption, named containers, quit handling | 1.5–2 d | Every launcher action works from the app; Rust tests green; stop really removes the container |
| 3 | **UI adapter + events** — `api.js`, event log, report windows, local fonts, copy | 0.5–1 d | Same UI works in the app and in a browser via `server.py` |
| 4 | **Runtime onboarding** — state machine + screens + Start Docker | 0.5–1 d | All §7 rows reproduced manually |
| 5 | **Toolbox image publishing** — bake runner, GHCR workflow, pinned tag, pull screen | 1 d | Fresh machine: install app → pull → quick scan, no local build |
| 6 | **Packaging + CI + signing** — bundles, release workflow, (cert lead time is extra) | 1–2 d | Tagged release produces installers; Windows installer runs on a clean VM |
| 7 | **Docs** — README install section, `docs/running-an-engagement.md`, design doc (§9 copy, onboarding screens, report windows), retire or keep `start-redkeep.*` | 0.5 d | Docs match the app; screenshots regenerated |
| | **Total** | **~6–9 d** | plus code-signing certificate procurement |

Phases 0→3 are sequential. Phase 5 (image publishing) can run in parallel with 2–4 (different
files: Dockerfile, workflows). Phase 6 needs 3 and 5.

## 14. Decisions needed before starting

| # | Decision | Recommendation |
|---|---|---|
| D1 | Platforms for the first release | Windows only; macOS/Linux in a later release |
| D2 | App identifier / product name | `Redkeep`, identifier like `io.github.<owner>.redkeep` (reverse-DNS you control) |
| D3 | Keep `ui/server.py` + start scripts? | Keep as the dev/headless launcher (same UI via the adapter); revisit after one release |
| D4 | Runner baked into the image vs mounted | Baked + version-pinned for releases; mounted overlay in dev mode |
| D5 | Code signing now or later | Ship unsigned builds to testers first; buy/set up signing before any public release |
| D6 | Editing targets | First release: "Open config.yaml" + validation errors shown in-app; a form editor later |
| D7 | Auto-update | Off in the first release; add the signed updater once releases are regular |
| D8 | arm64 toolbox image | After the amd64 release, once tool availability is confirmed |
| D9 | DefectDojo hub in the app | Out of scope for v1 (stays `make hub-up`) |

## 15. Risks

| Risk | Mitigation |
|---|---|
| Users without Docker / unfamiliar with WSL2 | Onboarding screens (§7); clear docs; supported-runtime list |
| Docker Desktop licensing for larger companies | Support Rancher/Podman/Engine; state the licensing note on the onboarding screen |
| 6 GB first download | Publish once, pin per version, show progress/size, allow cancel/resume |
| Image/app drift (the `defusedxml` incident) | Pinned image tag per app version; image smoke test in CI |
| Stop not stopping containers | Named job containers + `docker stop` (§8); manual test row |
| SmartScreen / Gatekeeper warnings | Code signing (D5) before public release |
| Podman compose differences | Test the lab compose file under Podman before claiming support; otherwise list it as "experimental" |
| Antivirus heuristics on an app that orchestrates offensive tooling | The app itself contains no tools (they live in the image); sign the binary; document what it does |
| Paths with spaces / non-ASCII user names | argv-only process spawning; explicit test (§12) |

## 16. Out of scope for this migration (follow-ups)

- Mobile testing module (deferred project-wide).
- A target editor UI and engagement management.
- DefectDojo inside the app.
- Report redesign or PDF export.
- Merging the two reds (`#b4232a` / `#c01f28`) — a design-system item, independent of this.
