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
marketing site — the UI stays quiet so findings and status read first. It is dark-first,
theme-aware (`prefers-color-scheme`), and dependency-light (one display typeface, system
fallbacks, inline SVG).

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
- **Do** render the header lockup at ~42px tall (UI) / ~300px wide (README).
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
| **Accent (keep red)** | `#b4232a` | Primary actions, danger, Critical |

The accent `#b4232a` is the one saturated colour in the whole system. Spend it sparingly —
**danger and severity only**: the "Docker: not running" pill border, the error/`.fail` state,
and the Critical severity badge. The primary button is **ink-filled, not red**. If everything
is red, nothing is.

### 2.2 Surface tokens (CSS variables)

**One shared, near-black surface set** drives both surfaces — the launcher **app**
(`ui/index.html`) and the offline **report** (`reports/templates/report.html.j2`). The app is
the source of truth; the report sits on the same tokens so the two read as one product. Add a
new surface by copying this block, not by inventing a third near-black.

| Variable | Dark (default) | Light (`prefers-color-scheme: light`) | Role |
|----------|----------------|----------------------------------------|------|
| `--bg` | `#0a0a0b` | `#FAFAF8` | Page background (near-black) |
| `--panel` | `#141417` | `#ffffff` | Panel surface (lighter than bg) |
| `--card` | `#1a1a1e` | `#ffffff` | Inner card (summary cards, buttons) |
| `--ink` | `#F2F2F0` | `#262626` | Primary text |
| `--muted` | `#9aa3b2` | `#5b6473` | Secondary text, labels |
| `--line` | `#26262b` | `#e4e7ec` | Hairline borders (the depth source) |
| `--accent` | `#b4232a` | `#b4232a` | Keep-red — fills / borders only |
| `--accent-ink` | `#e2565c` | `#b4232a` | Red **as text** on dark (AA-safe) |
| `--ok` | `#3fae63` | `#3fae63` | Success / Docker-up / done |
| `--warn` | `#e0a800` | `#e0a800` | Job running |
| `--term-bg` | `#000` | `#0b0b0b` | Terminal/log background |
| `--term-fg` | `#d6f5d6` | `#d6f5d6` | Terminal/log text |
| `--focus` | `#F2F2F0` | `#262626` | Keyboard focus ring (= ink) |

**Near-black, not black.** Pure `#000` collapses the depth model and halates in long
sessions, so `--bg` is `#0a0a0b` with `--panel`/`--card` *lighter* and separation carried by
`--line`. True `#000` is reserved for the terminal `pre` only. Every text/surface pair was
re-verified ≥ WCAG AA after darkening: ink 15–18:1, muted 6.8–7.8:1, ok 6.5:1, warn 8.6:1.

**`--accent-ink` (the one subtlety).** On near-black, the keep-red used **as text** (the
"Docker: not running" pill, run-row hover) drops to ~2.8:1 — fails AA. So red text on dark
uses `--accent-ink` `#e2565c` (**5.0:1**), while `--accent` `#b4232a` stays for fills and
borders. Red is still spent only on danger/severity; it just has a text-safe shade on dark.

Both surfaces also carry the **severity tokens** (§2.3) — the app now uses them for the
summary cards, the chart, and the report-row badges — and both inline **Space Grotesk** (§3):
the app serves the self-hosted `.woff2`, the report base64-embeds it so a saved report keeps
its type offline. *(The old app/report dark divergence is resolved — one token set now.)*

### 2.3 Severity scale (the semantic core)

The product's most important colour system. Order is always **Critical → High → Medium →
Low → Info** (CVSS v3.1 bands), rendered as the **squared severity tag** (§5). Tag text is
`--badge-fg` (white) except Medium, which uses `--badge-fg-med` (`#1b1f27`). **Every pair
meets WCAG AA (≥4.5:1) at the tag's 11px:**

| Severity | Tag | Variable | Fill | Text | Contrast |
|----------|-----|----------|------|------|----------|
| Critical | `CRIT` | `--crit` | `#b4232a` | white | 6.53:1 |
| High | `HIGH` | `--high` | `#c0461f` | white | 5.08:1 |
| Medium | `MED` | `--med` | `#e0a800` | `#1b1f27` | 7.68:1 |
| Low | `LOW` | `--low` | `#2f6fa8` | white | 5.30:1 |
| Info | `INFO` | `--info` | `#5b636b` | white | 6.10:1 |

The ramp stays visually ordered — crimson → orange-red → amber → blue → grey, with High
nudged toward orange so it reads apart from Critical crimson. **Tuned 2026-10-29** to the
AA-safe set above (earlier passes: High `#d9534f`→`#c2410c`→`#c0461f`, Low
`#3a86c8`→`#2c6aa0`→`#2f6fa8`, Info `#6c757d`→`#5b636b`). Never reorder the scale and never
swap a severity's colour.

### 2.4 State colours

| Meaning | Token | Hex | Where |
|---------|-------|-----|-------|
| OK / success / running Docker | `--ok` | `#3fae63` | status pill, "done" dot |
| Warning / job running | `--warn` | `#e0a800` | "running" dot, progress bar |
| Danger — fills / borders | `--accent` | `#b4232a` | "bad" pill border, Critical tag (danger / severity only) |
| Danger — text on dark | `--accent-ink` | `#e2565c` · `#b4232a` light | "bad" pill text, `.fail` dot, run-row hover |
| Neutral / idle | `--muted` | `#9aa3b2` | idle dot, secondary text |

### 2.5 Job-state matrix (launcher)

The "Live output" panel reflects one running job. Each state sets the status **dot**, the
label, and whether the indeterminate progress **bar** shows:

| State | Dot | Bar | Label | Scan button |
|-------|-----|-----|-------|-------------|
| Idle | `--muted` (solid) | hidden | `idle` | enabled |
| Running | `--warn` (pulsing) | visible (`--warn` sweep) | `<job> [running]` | disabled |
| Done (rc 0) | `--ok` (solid) | hidden | `<job> [done]` | enabled |
| Failed (rc ≠ 0) | `--accent-ink` (solid) | hidden | `<job> [failed (exit <code>)]` | enabled |

The pulse and bar animations are wrapped in `@media (prefers-reduced-motion: no-preference)`,
so they are static for users who ask for reduced motion. The report has two display states:
**has-findings** (summary cards + findings table) and **zero-findings** (a muted "no parsed
findings" note) — the count never implies "secure", only "nothing parsed from this run".

---

## 3. Typography

**Space Grotesk** is the display/UI face on **both** surfaces. It is self-hosted (SIL OFL
1.1) as a variable `.woff2` at `resources/fonts/space-grotesk.woff2` — the app serves it via
`@font-face`, the report base64-embeds it so a saved file renders offline. No CDN, no network
call. The system stack is the fallback if the font is ever absent.

| Role | Family | Notes |
|------|--------|-------|
| Display / UI | **Space Grotesk** `300 700`, then `-apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif` | App + report; also the wordmark face (Medium 500, -0.04em) |
| Mono (`--font-mono`) | `ui-monospace, Menlo, Consolas, monospace` | terminal log, inline `code`, the squared severity tag |

**Base:** `15px / 1.5`. **Type floor is 12px** for body/label text. The one exception is the
**squared severity tag at 11px** — allowed because it is uppercase mono with `.06em` tracking,
which stays legible. **Type scale in use:**

| px | Usage |
|----|-------|
| 26 | Report summary card number (`.card .n`, 700) |
| 22 | Report H1 |
| 15 | Body |
| 14 | Table body; H2 (uppercased) |
| 13 | Secondary / labels / `.muted` |
| 12 | Status pill, table headers, mono log |
| 11 | Severity tag only (uppercase mono, tracked) |

**Section headings (`h2`)** are `14px`, `text-transform:uppercase`, `letter-spacing:.05em`,
coloured `--muted` — labels, not titles. Table/card micro-labels use the same uppercase +
`.03–.04em` tracking at 12px.

---

## 4. Layout, spacing & shape

| Property | Value |
|----------|-------|
| Content max-width | `1000px` (app) · `980px` (report), centred |
| Body padding | `28px 16px` (app) · `32px 16px` (report) |
| Panel padding | `18px 20px` |
| Grid | 2 columns `1fr 1fr`, gap `18px`; collapses to 1 column at **≤760px** |
| Button/field gap | `8px` (`.btns` wrap) |
| Card min-width | `120px` (summary cards flex-wrap) |

**Radii:** panels `14px` (app) / `12px` (report) · cards `10px` · buttons & selects `9px` ·
log `10px` · inline `code` `5px` · status pill `999px` · **severity tag `3px`** (squared).

**Borders:** `1px solid var(--line)` everywhere — hairline separation, no shadows. The whole
system is flat: depth comes from `--panel` vs `--bg`, not elevation.

---

## 5. Components

**Panel** — the base container. `background:var(--panel); border:1px solid var(--line);
border-radius:14px; padding:18px 20px`. Everything lives in a panel.

**Button** — `padding:9px 14px; radius:9px; 1px var(--line) border; background:var(--card)`.
Three flat tiers, no shadows:
- **Primary** (`.primary`): `background/border:var(--ink); color:var(--bg); weight:600`. The one
  filled action per view (Start scan) — **ink-filled, not red**. *Decision 2026-10-29 (revised):*
  red was pulled off the button so the accent is spent strictly on danger/severity; the primary
  now leads by value contrast (an ink fill) instead of hue.
- **Lead** (`.lead`): `border-color:var(--ink); weight:600` — non-accent emphasis for a
  region's leading action (Start lab) so it isn't inert, without spending red.
- **Secondary:** the default hairline outline (Stop lab, Rebuild report, Stop job).
- **Disabled:** `opacity:.5; cursor:not-allowed`.

**Pill** (status) — `12px; padding:4px 11px; radius:999px; 1px border; color:var(--muted)`.
Modifiers: `.ok` (green text+border), `.bad` (accent text+border). Used for the Docker
status chip.

**Severity tag** (`.sev`) — the single component for every severity surface (findings table,
report summary cards, launcher report-row counts). **Squared**, console-grade:
`border-radius:3px` (never 999px), `var(--font-mono)`, UPPERCASE `11px`, `letter-spacing
.06em`, `weight 600`, `padding 3px 8px`, `min-width 46px` so a column of them aligns. Fill =
severity colour (`.sev-crit`…); text = `--badge-fg` white, except Medium `--badge-fg-med`.
Flat — no border, no shadow. Labels are fixed/abbreviated: `CRIT HIGH MED LOW INFO`. Variants:
`.sev.ct` (count-tag — tighter, no min-width, for `C1 H3 M4…` clusters, zeros omitted) and
`.sev.zero` (neutral outline chip for a clean "0 findings" run).

**Select** — full-width, `padding:8px 10px; radius:9px; 1px var(--line); background:var(--bg)`.

**Terminal / log (`pre`)** — black console: `background:var(--term-bg); color:var(--term-fg)`
(phosphor green), mono, `radius:10px; padding:12px; min-height:120px; max-height:360px;
overflow:auto`, `white-space:pre-wrap`. It stays dark in both themes — a console reads as a
console — but the light theme softens `--term-bg` from pure `#000` to `#0b0b0b`. **At idle the
console is replaced by a compact dashed idle card (`.idlecard`)** so the panel is never a tall
empty void; the `pre` appears (growing with output) only once a job has produced output.

**Summary card** (`.mcard`) — a flat metric tile on `--card`: a big number (`26px/700`) over an
uppercase micro-label (`12px --muted`). Four across the top (Docker · latest-scan findings ·
latest Critical / High · total reports); collapses to two columns ≤640px. Numbers come from the
runner's per-run `summary.json` (§9); a metric with no scored run shows `—`, a clean scan shows
`0` (never implies "secure").

**Severity chart** (`.chart`) — the focal region and the **only app surface that uses the
severity colours**. A dependency-free inline-SVG stacked bar per recent scan (up to 8, oldest →
newest), each segment `fill:var(--crit|--high|…)`, scaled to the busiest scan; `viewBox` +
`width:100%` keeps it responsive. A legend maps colour → severity. Empty state: "No scored
scans yet."

**Reports row** — name, non-zero **severity count-tags** (`.sev.ct`, letter + count:
`C1 H3 M4 L2 I2`), and `open report ↗`. A zero-finding run shows the neutral `.sev.zero` chip.

**Status dot** — `8px` circle. Default `--muted` (idle); `.run` → `--warn` (pulsing);
`.done` → `--ok`; `.fail` → `--accent-ink`. See the state matrix (§2.5).

**Progress bar** (`.bar`) — a `3px` hairline track (`--line`) with a `--warn` segment that
sweeps while a job runs; hidden otherwise. Animation respects `prefers-reduced-motion`.

**Focus ring** — `:focus-visible { outline:2px solid var(--focus); outline-offset:2px }`. The
ring is **ink, not accent**, so keyboard focus never reads as an error/critical cue and stays
visible on every surface. Keyboard-only (does not fire on mouse click).

**Summary card** (report) — centred, big number (`26px/700`, in `--ink`) over a squared
severity **tag** label (`.sev`). One card per severity, flex-wrapped. *(Decision 2026-10-29:
the number stays ink and the colour lives in the tag; rendering the number itself in the
severity colour fails AA on the near-black panel — e.g. Critical `#b4232a` text is 2.8:1.)*

**Findings table** — `width:100%`, hairline row borders, `vertical-align:top`. Columns:
Severity (`.sev` tag) · Finding · Tool (`.tool`, muted 12px) · Count · Detail/reference
(inline `code` for CWE/WASC/template IDs). Headers are uppercased muted 12px.

**Run list** — rows are full-width links: name, severity count-tags, and the `open report ↗`
tag (muted 12px); hairline divider; hover → `--accent-ink`.

---

## 6. Iconography

One inline SVG — the keep mark from §1 — rendered at `32×34` beside headings, stroked with
`currentColor`/`--ink` so it inherits the theme. Prefer inline SVG over an `<img>` for the
mark inside content so it recolours with the theme; use the PNG/`<picture>` lockup for the
header and README. No other icon set; text labels and the `↗`/`·` glyphs carry the rest.

---

## 7. Theming

Themes are pure CSS custom properties. Dark is the default (declared on `:root`); light is a
`@media (prefers-color-scheme: light)` override of the same variables. Rules:

- Author every colour as a `var(--token)` — never a raw hex in a rule (the severity/state
  hexes live only in `:root`).
- Give `body` an explicit `background:var(--bg)` and `color:var(--ink)`.
- The log `pre` stays dark in both themes via `--term-bg`/`--term-fg` (light softens it to
  `#0b0b0b` rather than pure `#000`).
- Keyboard focus uses `--focus` (ink), never `--accent`.
- To add a surface, copy the shared variable block (§2.2) rather than inventing new darks.

---

## 8. Voice & tone

Plain, exact, safety-first — the language of an operator, not a brand.

- State what's true and what's isolated: "Nothing idles — the toolbox runs only during a
  scan.", "Local control panel on 127.0.0.1 only.", "an authorised test of an isolated lab
  copy of the target only."
- Lowercase, terse labels ("Start lab", "Run a scan", "open report").
- No hype, no exclamation marks, no emoji in product surfaces.
- Always frame scope and authorisation when describing what Redkeep does.

---

## 9. Where it lives

| Surface | File |
|---------|------|
| App tokens + components | `ui/index.html` |
| Report tokens + severity scale | `reports/templates/report.html.j2` |
| Per-run summary (cards / chart / badges) | `runner/vapt/report.py` writes `summary.json`; `ui/server.py` reads it |
| Report font inlining | `runner/vapt/report.py` (`_font_b64`) |
| Display font (self-hosted) | `resources/fonts/space-grotesk.woff2` (+ `OFL.txt`) |
| Logo kit + brand colours | `resources/redkeep-logo/` (`README.md`) |
| README lockup | `README.md` |

When you touch any of these, update this document in the same change so the design system
and the code never drift.
