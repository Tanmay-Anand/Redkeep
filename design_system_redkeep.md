<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="resources/redkeep-logo/png/transparent/redkeep-lockup-light-1200w.png">
    <img alt="Redkeep" width="300" src="resources/redkeep-logo/png/transparent/redkeep-lockup-dark-1200w.png">
  </picture>
</p>

# Redkeep Design System

The visual language for Redkeep's surfaces — the launcher **UI** (`ui/index.html`), the
offline **report** (`reports/templates/report.html.j2`), the **logo kit**
(`resources/redkeep-logo/`), and the README. Every token below is the one actually in the
code; this document is the single source of truth, so change the code and this file
together.

Design goals: calm, dense, utilitarian. Redkeep is a security tool for focused work, not a
marketing site — the UI stays quiet so findings and status read first. The launcher is
light, with **one dark surface** (the live-output panel, "the keep"), square-cornered, and
speaks in **two voices**: JetBrains Mono for what the machine says, Inter for what people
read. It is dependency-light (Inter + JetBrains Mono 400/500/700 from Google Fonts for the
app; the offline report base64-embeds the same two families so it renders identically with
no network; system fallbacks, inline SVG).

---

## 1. Brand

**Name / concept.** *Redkeep* — a "keep" is the fortified core of a castle. The product is
the hardened, isolated place from which you test your own stack. The mark is a castle keep
with battlements; the "red" is the single accent, not the mark's colour.

**Mark.** A monochrome battlements/keep glyph, drawn as a single stroked path:

```
viewBox="-7 -4 96 96"
d="M5 83 V5 H15 V19 H36 V5 H46 V19 H67 V5 H77 V83 H56 V60 A15 15 0 0 0 26 60 V83 Z"
fill="none"  stroke-width="10"  stroke-linejoin="miter"
stroke = ink (#262626 on light, #F2F2F0 on dark)
```

The arch (`A15 15 0 0 0 26 60`) is the gate. Keep it stroked, never filled; keep the miter
joins (no rounded corners).

**Wordmark.** "redkeep", set in **Space Grotesk Medium (500)**, letter-spacing **-0.04em**,
all lowercase. In the shipped assets the wordmark is converted to outlines, so no font file
is required to render the logo.

**Variants** (in `resources/redkeep-logo/`):

| Need | Use |
|------|-----|
| On a light background | `*-dark` (dark ink) — `svg/redkeep-lockup-dark.svg` |
| On a dark background | `*-light` (light ink) — `svg/redkeep-lockup-light.svg` |
| Square avatar / icon | `png/transparent/redkeep-mark-{256,512,1024}.png` |
| On brand background | `png/solid/*-on-light`, `*-on-dark` |
| Favicon | `favicons/favicon.svg` (auto-swaps ink in dark mode), `.ico`, `apple-touch-icon.png` |

Lockups come at 1200 / 2400 / 4800 px wide; marks at 256 / 512 / 1024 px square.

**Logo do / don't.**
- **Do** pick the variant by background: dark-ink on light, light-ink on dark.
- **Do** give it clear space ≈ the height of one battlement on all sides.
- **Do** render the header lockup at 30px tall (UI) / ~300px wide (README).
- **Don't** recolour the mark to red — the mark is ink; red is the UI accent only.
- **Don't** fill the mark, round its corners, add effects, or stretch it.

---

## 2. Colour

### 2.1 Core palette (brand constants)

Defined canonically in the logo kit; everything else is a surface tint of these.

| Token | Hex | Role |
|-------|-----|------|
| Ink | `#262626` | Primary text / mark on light |
| Light ink | `#F2F2F0` | Primary text / mark on dark |
| Light background | `#FAFAF8` | Brand light surface |
| Dark background | `#18181A` | Brand dark surface |
| **Accent (keep red)** | `#b4232a` brand · `#c01f28` UI | Danger, Critical severity |

The accent is the one saturated colour in the whole system (brand crimson `#b4232a` = the
Critical severity; the UI `--accent` is a hair brighter, `#c01f28`). Spend it sparingly —
**danger and severity only**: the "Docker offline" status, the failed state (`--keep-bad` is
the same red lifted for the dark panel), and Critical severity. The primary button is
**ink-filled, not red**, and no hover is red. If everything is red, nothing is. The dark
background `#18181A` and light ink `#F2F2F0` are the keep's `--keep` / `--keep-ink`.

### 2.2 Surface tokens (CSS variables)

The launcher (`ui/index.html`) and the offline report (`report.html.j2`) share the light
surface below. The launcher adds **one dark surface**: the live-output panel,
called **the keep** — the isolated place where the job runs. Corners are **square**
(`border-radius:0`, matching the logo's miter joins). Structure comes from hairlines; there are
no shadows, no pills and no chips. Add a new surface by copying these blocks.

The report carries only the light tokens it uses (`--bg --panel --card --ink --muted --line
--line2 --hatch` and the severity ramp); it has no live output, so no keep tokens.

**Light surface**

| Variable | Value | Role |
|----------|-------|------|
| `--bg` | `#f6f6f5` | Page background (warm off-white) |
| `--panel` | `#ffffff` | Panels, the metric strip, controls |
| `--card` | `#fbfbfa` | Row hover / linked-run highlight; base under disabled hatch |
| `--ink` | `#111113` | Primary text; fills the primary button |
| `--muted` | `#60636b` | All secondary text and every label |
| `--line` | `#e2e2de` | Outer hairline borders, chart gridlines |
| `--line2` | `#eeeeeb` | Inner dividers (strip cells, table rows, targets block) |
| `--edge` | `#cfcfca` | Border of buttons and selects at rest |
| `--soft` | `#b9bbc1` | Decorative only: the `/` in `1/3`, link underline at rest |
| `--ink-hover` | `#2b2b30` | Primary button hover |
| `--accent` | `#c01f28` | Red — danger only (Docker offline) |
| `--ok` | `#1f8a4c` | Docker up; the scanning progress bar |
| `--ok-tint` | `#dcefe3` | Scanning progress fill behind ink text |
| `--focus` | `#111113` | Keyboard focus ring on light surfaces (= ink) |
| `--hatch` | `135°` 1px ink lines at 14% every 6px | "Nothing here" (§5 Hatch) |

**`--faint` is retired as a text colour.** `#9b9ea6` is about 2.6:1 on white, below the 4.5:1
small text needs; every label moved to `--muted`. **`--warn` is retired from the launcher.**
Running is shown by shape and motion (§2.5), which also removes the clash between "job
running" amber and Medium-severity amber.

**The keep (dark live-output panel)**

| Variable | Value | Role |
|----------|-------|------|
| `--keep` | `#18181A` | Panel background (brand dark background, §2.1) |
| `--keep-ink` | `#F2F2F0` | Text, state square, cursor, focus ring (brand light ink, §2.1) |
| `--keep-line` | `#3a3a40` | Borders inside the keep |
| `--keep-muted` | `#a6a6ac` | Labels, idle text |
| `--keep-dim` | `#8a8a92` | Disabled text. Lowest text colour allowed on `--keep` |
| `--keep-ok` | `#46c489` | Done (`--ok` lifted for the dark surface) |
| `--keep-bad` | `#f0565c` | Failed (`--accent` lifted for the dark surface) |
| `--keep-hatch` | `135°` 1px light lines at 13% every 6px | "Nothing here" on the keep |

**Keep colours are used only inside the live-output panel, and the severity ramp is never
placed on `--keep`** — Critical there is about 2.7:1.

### 2.3 Severity scale (the semantic core)

The product's most important colour system. Order is always **Critical → High → Medium →
Low → Info** (CVSS v3.1 bands), rendered as a **severity mark** (§5): a 3px colour bar plus the
uppercase mono code. The code is `--ink` (never reversed on a fill), so contrast is always high;
the colour is carried by the bar. The same five colours fill the chart bars and mark the
reports-table count columns.

| Severity | Mark | Variable | Colour |
|----------|------|----------|--------|
| Critical | `▏ CRIT` | `--crit` | `#b4232a` crimson |
| High | `▏ HIGH` | `--high` | `#c0461f` orange-red |
| Medium | `▏ MED` | `--med` | `#d99400` amber |
| Low | `▏ LOW` | `--low` | `#2f6fa8` blue |
| Info | `▏ INFO` | `--info` | `#6b7280` grey |

The ramp stays visually ordered — crimson → orange-red → amber → blue → grey, with High
nudged toward orange so it reads apart from Critical. Never reorder the scale and never swap a
severity's colour. Nothing outside this scale is amber.

### 2.4 State colours

| Meaning | Token | Where |
|---------|-------|-------|
| Docker up | `--ok` | Header state square. The label stays `--ink`: green text on the page is ~4:1, so the square carries the colour |
| Docker offline | `--accent` | Header state square **and** label |
| Job done | `--keep-ok` | Keep state square (filled) |
| Job failed | `--keep-bad` | Keep state square (filled) |
| Neutral | `--muted` / `--keep-muted` | Labels, secondary text, checking state |

Red appears in exactly four places: Docker offline, the failed state, Critical severity, and a
non-zero Critical number in the metric strip. A hover is never red.

### 2.5 Job-state matrix (launcher)

**Shape first, colour second.** The keep's state square is 10px with a 1.5px border; the label
text comes from the runner. Because the square differs in every state (and done vs failed
differ in fill and in label), the state is readable without colour and without motion.

| State | Square | Label | Battlements | Start scan | Stop job |
|---|---|---|---|---|---|
| Idle | hollow, border `--keep-ink` | `idle` | hidden | enabled | disabled |
| Running | left half filled `--keep-ink` | `<job> [running]` | visible, marching | disabled; a scan shows estimated progress (§5) | enabled |
| Done (rc 0) | filled `--keep-ok` | `<job> [done]` | hidden | enabled | disabled |
| Failed (rc ≠ 0) | filled `--keep-bad` | `<job> [failed (exit <code>)]` | hidden | enabled | disabled |

The script sets the square's class (`.run` / `.done` / `.fail`) and `body[data-state]`
(`idle` / `running` / `done` / `failed`) from `/api/job`. The marching battlements and the
blinking log cursor live inside `@media (prefers-reduced-motion: no-preference)`; with reduced
motion the battlements are visible but still, so running stays obvious.

The report has two display states: **has-findings** (summary + findings table) and
**zero-findings** (a hatched "no parsed findings" note). In the launcher `—` means "not
scored" and `0` means "nothing parsed"; neither implies "secure".

---

## 3. Typography

**Two voices.** **JetBrains Mono** carries everything the machine says: labels, metric
numbers, status text, chart axis and totals, the reports table (except the scope column), the
targets block, and the log. **Inter** carries everything written for people: body prose,
button text, select values, the scope column and the footer. The app loads both from Google
Fonts (Inter 400–700, JetBrains Mono 400/500/700). The offline report base64-embeds both —
Inter variable (`resources/fonts/inter.woff2`) and JetBrains Mono latin 400/500/700
(`resources/fonts/jetbrains-mono-{400,500,700}.woff2`, SIL OFL 1.1, licence in
`OFL-JetBrainsMono.txt`) — adding ~150 KB per report. A missing file is skipped and that
voice falls back to the system stack.

| Role | Family |
|------|--------|
| People (`--font-sans`) | `'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif` |
| Machine (`--font-mono`) | `'JetBrains Mono', ui-monospace, 'SF Mono', Consolas, monospace` |

**Labels are lowercase mono.** One style replaces every heading, field label, metric label,
table header and status label:

```css
.lbl{font:500 11.5px/1.2 var(--font-mono);color:var(--muted);letter-spacing:.01em}
```

**Uppercase is reserved for severity codes** (`CRIT HIGH MED LOW INFO`), written in uppercase
in the markup — nothing in the launcher uses `text-transform:uppercase` or wide tracking. That
alone makes the codes stand out without adding colour.

**Base:** Inter `14.5px / 1.55`. Numbers are tabular. **Type floor is 11px** (chart axis only);
labels are 11.5px. **Type scale in use (launcher):**

| px | Usage |
|----|-------|
| 32 | Metric-strip number (mono 700, `-.03em`) |
| 14.5 | Body |
| 14 | Button text, select values |
| 13.5 | Prose in the rail, scope column |
| 13 | Reports table (mono) |
| 12.5 | Log and idle card (mono) |
| 12 | Header status, targets block, chart totals (mono) |
| 11.5 | Labels, severity codes, chart time labels (mono) |
| 11 | Chart axis (mono) — the floor |

---

## 4. Layout, spacing & shape

| Property | Value |
|----------|-------|
| Content max-width | `1160px` (app) · `980px` (report), centred |
| Body padding | `28px 20px` (app) · `44px 20px` (report) |
| Panel / section padding | `20px` |
| Main grid | `360px minmax(0,1fr)`, two paired rows — `"lab chart" "scan keep"` — column gap `18px`, row gap `9px`, `align-items:stretch`, so each box matches the height of its neighbour |
| Row rhythm | 9px row gap + 9px battlements = 18px; the scan box takes `margin-top:9px` so its top lines up with the keep's dark panel, not its battlements |
| Narrow (≤860px) | one column: lab, scan, chart, keep (the chart takes `margin-top:9px` to keep 18px gaps) |
| Metric strip | four cells; two columns at **≤640px** |
| Button / field gap | `8px` |
| Control height | `40px` (`34px` small, `36px` on the keep) |

Order, top to bottom: header, metric strip, main grid (lab · chart, then scan · keep),
reports, footer.

**Radius:** `0` everywhere in the launcher — nothing is rounded.

**Borders & elevation:** `1px solid var(--line)` outer borders, `--line2` inner dividers,
`--edge` on controls at rest. **No shadows.** The keep has no panel border; its dark fill is the
boundary.

---

## 5. Components

**Panel** — `background:var(--panel); border:1px solid var(--line)`. Content sits in `.sec`
blocks (`padding:20px`) divided by full-width `--line` hairlines.

**Control boxes** — two panels, numbered in order of use, each paired with the box to its
right. **`01 / lab`** (prose, `Start lab` lead, `Stop lab`) sits beside the chart.
**`02 / scan`** (scope and profile selects, full-width `Start scan` primary, targets block) sits
beside the keep, with a last section holding only a full-width `Stop everything`, pushed to the
bottom of the box (`margin-top:auto`) so a global stop is not mistaken for a scan or lab
control. Content stays top-aligned; extra height from the pairing is empty space. The number is `--ink` 700;
the rest of the label is `.lbl`. Buttons sit next to what they act on: `Stop job` in the keep
header, `Rebuild report` in the reports header (**`03 / reports`**).

**Lab state & gating** — the `01 / lab` header carries the lab's state on the right, mono 500
12px with a 10px square, from `lab` in `/api/status` (a read-only `docker compose ps` of the
six target services; the toolbox's scan containers and anything started outside the compose
project don't count): `lab up` (filled `--ok`, ink label), `lab partial 2/6` (left half
`--ok`), `lab down` (hollow, `--muted`). `unknown` hides it.
- **Start lab** is disabled while the lab is up or any job runs (one job at a time).
- **Stop lab** is disabled only when the lab is down and nothing runs; it stays enabled during
  a Start lab job so a slow start can be interrupted.
- With `unknown`, only the job gates them.
- **Stop lab** and **Stop everything** interrupt a running job, so during a **scan** they ask
  first: "This will stop the running scan (<job>). Continue?" (native `confirm`). Interrupting
  a Start lab job needs no confirmation.

**Button** (`.btn`) — `border-radius:0; font:500 14px/1 Inter; border:1px solid var(--edge);
background:var(--panel); padding:0 14px; min-height:40px`; hover sets the border to `--ink`.
- **Primary** (`.primary`): ink fill, `--panel` text, 600; hover `--ink-hover`. One per view
  (Start scan) — **never red**.
- **Lead** (`.lead`): `--ink` border, 600 — the leading action of a section (Start lab).
- **Secondary:** the default `--edge` outline.
- **Disabled:** **hatched** — `--muted` text, `--line` border, `background:var(--hatch),
  var(--card)`. Reads as "not available right now" and stays legible (replaces `opacity:.5`).
- **Scanning** (`.scanning`, Start scan only, while a scan job runs): still disabled, but busy
  rather than unavailable, so no hatch. `--ok` border, `--panel` base, `--ink` text; a
  `--ok-tint` fill and a 3px `--ok` bar along the bottom both grow from the left to `--p`.
  Text: `Scanning 37% · ~8 min left`, then `Scanning · 52 min, longer than usual` once past the
  estimate. **The progress is an estimate** (the runner reports none): elapsed time over the
  median of this browser's last five successful scans with that profile (`localStorage`
  `redkeep.scanDurations`), or a default (quick 5, api 10, web 15, network 30, full 45 min).
  It is linear to 95%, then creeps toward 99%, so an overrun never looks finished. The start
  time is `started` from `/api/job`, else the run folder the runner prints (`out=…`, UTC),
  else when the page first saw the job. A tooltip says it is estimated and from what. The width
  eases (`1.4s linear`) only when motion is allowed. Other jobs (Start lab) leave the button
  hatched.

**Select** — `appearance:none; border-radius:0; min-height:40px; padding:0 34px 0 12px;
border:1px solid var(--edge); background:var(--panel)`, value in Inter 14px. The chevron is
drawn in CSS (`.selwrap::after`, `--ink` borders) so no colour lives outside a token. Hover
sets the border to `--ink`.

**Targets block** — a bordered key/value block built from the status data: `web` and `api`
rows (plus `dojo  on` when DefectDojo is enabled). Mono 12px, 58px key column in `--muted`
with a `--line2` divider, outer `--line`. Several targets join with `, `. An empty list renders
`no targets` in `--muted` on `var(--hatch)` — never `[]`. No config yet shows the setup hint in
a hatched note.

**Status** (`.stat`) — the header's right side, mono 500 12px: `127.0.0.1 only` in `--muted`,
then a 10px state square + lowercase label (`docker running` / `docker offline`). Up: square
`--ok`, label `--ink`. Offline: square and label `--accent`.

**Metric strip** (`.summary` / `.mcard`) — **not cards**: one bordered row, four cells divided
by `--line2` (Docker · latest scan findings · latest critical / high · reports). Each cell is a
`.lbl` over a mono 700 32px number. The Critical/High cell colours each number separately —
Critical `--crit`, High `--high`, `/` in `--soft` weight 400 — and a `0` stays `--ink`. `—` is
"no scored run"; `0` is a clean scan. Numbers come from `summary.json` (§9).

**Severity mark** (`.sev`) — a `3px × 13px` colour bar (`::before`, colour from `--c`, set by
`.s-crit` … `.s-info`) plus the uppercase code in mono 500 11.5px, `letter-spacing:.05em`. Used
in the chart legend and as the reports-table column headers, which double as the legend.

**Severity chart** — the focal region. Header: `findings by severity` · `last 8 scans`.
**Eight fixed slots**, oldest → newest, left to right; each scored scan is a stacked bar
(Critical on top, Info at the bottom), its total above in mono 500 12px, its time below in mono
11.5px (`--muted`; the newest is `--ink` 700). A slot with no scan is a full-height block of
`var(--hatch)` with no label, so the chart shows how much it holds. Y axis: a `--line`
gridline and mono 11px label every 5 findings (widened to a larger multiple of 5 only for very
large scans), maximum = busiest scan rounded up, minimum 5. Legend: the five marks, then,
pushed right, a hatched swatch labelled `no scan yet`. Hovering a bar outlines it (`2px` ink,
offset 2px) and highlights its reports row; hovering the row does the same to the bar (shared
`data-run`). Empty state: "No scored scans yet. Run a scan to populate this chart."

**Hatch** — the single "nothing here" pattern: empty chart slots, an empty target list,
disabled buttons, the idle log. `--hatch` on light, `--keep-hatch` on the keep.

**The keep (live output)** — `background:var(--keep); color:var(--keep-ink); padding:16px 20px
20px`, no panel border. Header row: `live output` (`.lbl` in `--keep-muted`), then pushed
right the job state (10px square + label, mono 500 12px), then **Stop job** — transparent,
`1px var(--keep-line)`, `min-height:36px`, enabled only while a job runs (disabled =
`--keep-dim` on `var(--keep-hatch)`). Focus ring inside the keep is `--keep-ink`.
- **Battlements** — a 9px strip of `--keep` merlons sitting on top of the panel, replacing the
  old progress bar and pulsing dot. It always takes its height (no layout jump), is visible only
  while running, and marches (`1.1s`) only when motion is allowed.
- **Idle card** — at idle the log is replaced by a compact card: `1px var(--keep-line)`,
  `var(--keep-hatch)`, `--keep-muted`, mono 12.5px. Copy: "No job running. Start the lab, then
  run a scan. Output streams here."
- **Log** — mono 12.5px / 1.8, `--keep-ink`, no border or background of its own,
  `min-height:214px; max-height:340px; overflow:auto; white-space:pre-wrap`. It appears only
  once a job has produced output, and renders the runner's output as plain text (no invented
  parsing). While running, an 8×15px `--keep-ink` block cursor follows the last line and blinks
  (`1s steps(1)`) when motion is allowed.

**Reports table** — inside the panel, wrapped in `overflow-x:auto` so it scrolls in its own box
on narrow screens. Columns: `run`, `scope`, `CRIT` `HIGH` `MED` `LOW` `INFO` (marks), `total`,
and an unlabelled link column. Mono 13px, tabular; headers are `.lbl` with a `--line` rule
above and below; rows divided by `--line2`; cells `15px 12px`, 20px on the outer edges.
- **run** — `YYYYMMDD-HHMMSS-<scope>` split into the date in `--muted` and the time in `--ink`
  700; the newest row adds a bordered `latest` tag (11px, `1px var(--edge)`). Other names show
  raw.
- **scope** — the rest of the name with `-` shown as ` + `, Inter 13.5px `--muted`.
- **counts** — fixed columns, **zeros shown** as a `--muted` 400 `0` with a transparent bar so
  digits align between rows. An unscored run shows `—` in every count and in total.
- **total** — right-aligned, 700.
- **link** — `open report` plus an inline-SVG arrow, `--ink`, underlined in `--soft` (offset
  4px), `--ink` underline on hover. A run without a report shows `no report`.
- **Row hover** is `background:var(--card)` (rows stay clickable, opening the report). Never
  red.

**Focus ring** — `:focus-visible{outline:2px solid var(--focus);outline-offset:2px}` on light
surfaces, `--keep-ink` inside the keep. Keyboard-only; never accent.

**Report (offline file)** — same light surface, square corners and two voices; no dark
surface, no motion, and one four-line script (below).
- **Back to launcher** — above the header, a mono 500 12px `back to launcher` link with an
  inline-SVG left arrow, styled like `open report` (`--ink`, `--soft` underline). It points
  to `/` and is shown only when the launcher served the file (`http(s):` and a path under
  `/report/`); opened from disk, emailed or printed, it stays hidden. The launcher's
  `open report` link still asks for a new tab; this covers windows that open it in place.
- **Header** — the mark (inline SVG, `--ink`) and the Inter 700 23px title, then a row of
  `.lbl` facts: `engagement <b>…</b>`, `generated <b>…</b>`, `source <code>…</code>`.
- **Severity strip** — one bordered panel of five cells divided by `--line2`: a severity mark
  over a mono 700 32px number. Non-zero Critical and High numbers take `--crit` / `--high`
  (Medium's amber is under 3:1 as text, so the ramp stays on the marks); a `0` is `--muted`
  400, as in the reports table. Three columns at ≤640px.
- **Findings table** — panel header `findings` · `<b>N</b> rows`; lowercase mono headers
  (`severity finding tool count detail / reference`) over a `--line` rule; rows divided by
  `--line2`. Severity is a mark; finding and detail are Inter (detail `--muted` 13.5px); tool
  is mono `--muted`; count is mono 700, right-aligned; references are `<code>` on `--line2`.
  The table keeps a 640px minimum and scrolls in its own box on phones.
- **Zero findings** — a hatched note (`var(--hatch)` on `--card`, mono, `--muted`) in place of
  the table.
- **Print** — `print-color-adjust:exact`, so the severity bars and hatching survive printing.

---

## 6. Iconography

The keep mark from §1 is the only symbol. The launcher header uses the lockup asset
(`<img>`); the report inlines the mark as SVG stroked with `--ink`. Inline SVG is used for the
`open report` arrow (`currentColor`, 1.4 stroke); the select chevron is drawn in CSS. No icon
set.

---

## 7. Theming

Themes are pure CSS custom properties. The launcher ships **light, with one dark surface** —
`:root` defines everything and there is no `prefers-color-scheme` override, so a dark-mode OS
still renders light. Rules:

- Author every colour as a `var(--token)` — never a raw hex in a rule (hexes live only in
  `:root`).
- Give `body` an explicit `background:var(--bg)` and `color:var(--ink)`.
- **Keep colours (`--keep*`) are used only inside the live-output panel, and the severity ramp
  is never placed on `--keep`.**
- Keyboard focus uses `--focus` (ink) on light surfaces and `--keep-ink` on the keep — never
  `--accent`.
- Every animation sits inside `@media (prefers-reduced-motion: no-preference)`.
- To add a surface, copy the token blocks (§2.2) rather than inventing new greys.

---

## 8. Voice & tone

Plain, exact, safety-first — the language of an operator, not a brand.

- State what's true and what's isolated: "Nothing idles — the toolbox runs only during a
  scan.", "Local control panel on 127.0.0.1 only.", "an authorised test of an isolated lab
  copy of the target only."
- Lowercase, terse labels ("live output", "findings by severity", "open report"); buttons in
  sentence case ("Start lab", "Start scan"). Uppercase only for severity codes.
- No hype, no exclamation marks, no emoji in product surfaces.
- Always frame scope and authorisation when describing what Redkeep does.

---

## 9. Where it lives

| Surface | File |
|---------|------|
| App tokens + components | `ui/index.html` |
| Report tokens + severity scale | `reports/templates/report.html.j2` |
| Lab state (01 box, button gating) | `ui/server.py` `_lab_state()` → `lab` in `/api/status` |
| Per-run summary (cards / chart / badges) | `runner/vapt/report.py` writes `summary.json`; `ui/server.py` reads it |
| Report font inlining | `runner/vapt/report.py` (`_font_b64`, `_mono_fonts_b64`, `MONO_WEIGHTS`) |
| Embedded report fonts | `resources/fonts/inter.woff2`, `resources/fonts/jetbrains-mono-{400,500,700}.woff2` (the app loads the same families via Google Fonts) |
| Logo kit + brand colours | `resources/redkeep-logo/` (`README.md`) |
| README lockup | `README.md` |

When you touch any of these, update this document in the same change so the design system
and the code never drift.
