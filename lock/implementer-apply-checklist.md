# Implementer APPLY checklist — TERRA UI-2.5a

**Status: UNLOCKED** — Designer half of Tech APPLY (Phase UI-2.5a). Implementer remains **IDLE** this phase.  
**Cavin lock:** PASS UI-2 craft + Option B.  
**Skill:** TERRA globe craft (sandbox accept tests; does **not** unlock production architecture or real demographics).

### Locked craft baseline (do not revise)

- **Pale IOR Veil** light theme; transparent soft crystal; no dark regress
- **C3 Soft Hollow** shell — soft rim; faint far-side depth cue only (not loud through-globe continents)
- **Geography:** accurate Earth; **whisper-thin** country borders (theme greys/blues, never harsh black atlas)
- **Continent grouping:** soft tint mode (Africa, Americas, Europe, Asia, Oceania, Antarctica) — **toggle** vs country-lines default (**S2 later**)
- **Data-on-globe:** elevated **crystal islands** (radial extrusion); magnitude → height; glow = **internal** emission + fresnel/limb spill — not stickers, neon outlines, or chunky bars
- **Orbit proof:** side/limb must prove volume before “glow craft PASS”
- **Chrome:** globe-first / chrome-light; no heavy dashboard chrome unless Cavin asks
- **MOCK fence:** all magnitudes / hues / categories are EXAMPLE — never real demographics

**MVP cut (DEFAULT):** **S0 → S1 → S3 → S5**. S2 / S4 later unless CoS unlocks earlier.  
**Out of scope this APPLY:** production stack lock (Compose / SwiftUI / KMP / Flutter), real APIs, dark theme, architecture creep.

Numeric targets, gesture PASS, asset + mock contracts live beside this file. Do not freestyle a new globe family.

---

## DoD 0 — Preconditions (before any state)

- [ ] Read locked boards + this pack; do **not** invent a new glass / glow family
- [ ] Reuse C3 Soft Hollow params from `numeric-craft-targets.md` (copied from UI-1e + UI-2 `C3` dict)
- [ ] Reuse `geo_rasters.npz` + `geo_meta.json` + `earth_topo.jpg` per `asset-contract.md` (do not swap in a different country-ID scheme)
- [ ] Load MOCK via `example-mock-data.json` (S3 set for MVP). Never invent real demographics
- [ ] Volumetric **near + far** sphere sampling (UI-1e / UI-2), **not** front-face-only
- [ ] Light theme only; status bar / safe area only; same globe model iOS + Android
- [ ] Clip / saturate before 8-bit (`lime-wrap = 0`)
- [ ] Gesture contract per `gesture-acceptance.md`

**S0 PASS gate:** quiet Pale IOR glass ball; accurate coasts; hollow shell + rim; far-side ghost at C3 levels; **no borders, no islands, no glow**.

---

## DoD 1 — S0 Globe only (control)

Locked boards: `/workspace/terra/phase-ui-2/boards/S0-globe-only-{ios,android}.png`  
C3 orbit reference (far-side honesty): `/workspace/terra/phase-ui-1e/boards/C3-soft-hollow-{ios,android}-orbit.png`

- [ ] Port C3 Soft Hollow: `glass_thick=0.62`, `ocean_body_a=0.20`, `rim_gain=0.92`, `shell_rim_boost=1.35`
- [ ] Far-side **C3 faintness** (must not become a second map):
  - `far_land_gain=0.15` · `far_blur_px=3` · `far_path_atten=0.65` · `far_limb_suppress=0.45`
  - Honesty: far-weight p95 stays **well below 0.30** (C3 orbit p95 ≈ **0.09**). Fail if far reads as a loud second map
- [ ] Equirect topo + land mask; no intentional coast warp
- [ ] Front home pose: yaw **100°**, pitch **−16°**
- [ ] Cool-glass light stage (`stage_rgb = 0.96, 0.95, 0.93`); status bar only
- [ ] Dual platform parity (same globe; iOS island / Android status icons only)

**S0 PASS (skill accept):** calm C3 Soft Hollow shell. Glance-match to S0 boards. Pale IOR Veil light; faint far; no data overlays.

---

## DoD 2 — S1 Country lines (default data mode)

Locked boards: `/workspace/terra/phase-ui-2/boards/S1-country-lines-{ios,android}.png`

- [ ] Sample `border` from `geo_rasters.npz` on the **near** sphere (land-masked)
- [ ] Line color theme grey-blue **rgb(0.42, 0.50, 0.60)** — never harsh black
- [ ] Line alpha **0.22 × border × land** (S1). Whisper-thin etched-in-glass, not a political atlas
- [ ] Fail if S1 ≈ S0 (too faint) **or** if lines read as a textbook political map (too loud / too black / too thick)
- [ ] Country lines are the **default on** data mode

**S1 PASS (skill accept):** borders readable, not harsh. Glance-match to S1 boards. Whisper greys/blues on unchanged C3 globe.

---

## DoD 3 — S3 Elevated glow (hero craft, sparse)

Locked boards: `/workspace/terra/phase-ui-2/boards/S3-elevated-glow-{ios,android}.png`  
Closeup: `/workspace/terra/phase-ui-2/closeups/S3-elevated-island.png`

- [ ] Load **S3 MOCK only** (7 countries) from `example-mock-data.json` — EXAMPLE heights / 2 glow hues
- [ ] Keep S1-family borders but quieter: alpha **0.14 × border × land**
- [ ] Crystal islands = sleek glass extrusion along normals, **not** chunky bars, **not** flat stickers
- [ ] `extrude_scale = 0.085` (in-app / boards). Island radial lift = `mock_height × 0.085 × radius`
  - S3 max (India 0.80) → **+6.8%** radius. Never exceed **+9.5%** even at height 1.0
- [ ] Height tiers (MOCK 0–1): 0.30–0.45 slight lift · 0.45–0.65 clear island · 0.65–0.90 tallest (still sleek glass)
- [ ] **Glow = internal emission**, not a country outline
  - A Activity cyan `(0.25, 0.85, 0.95)` · B Flow amber `(1.00, 0.55, 0.28)`
  - Core emit stronger toward island interior; fresnel bleed at island/sphere limb
  - Bloom: two-pass Gaussian **r=14 then r=28**, limb-respecting (fade outside extruded disk)
- [ ] No loud far-side glow map — elevation + glow are **near-side / limb** craft
- [ ] Far-side stays at **C3 Soft Hollow** faintness

**S3 PASS (skill accept):** islands glass, not bars; glow = internal emission + fresnel/limb spill (reads *inside* the ball). Glance-match to S3 boards + island closeup.

---

## DoD 4 — S5 Orbit proof (volume honesty, MVP uses S3 set)

Locked boards (for grammar, not pixel-match): `/workspace/terra/phase-ui-2/boards/S5-orbit-glow-{ios,android}.png`  
Closeup: `/workspace/terra/phase-ui-2/closeups/S5-orbit-volume-spill.png`

> Locked S5 boards used the **S4 dense MOCK**. MVP S5 orbits the **S3 sparse set** so S4 can stay deferred. Same extrusion / internal-glow / bloom grammar. If CoS later requires pixel-match to S5 boards, that pulls S4 into scope.

- [ ] Orbit pose: yaw **210°** (home 100° + **110°**), pitch **−12°**
- [ ] Same S3 islands + 2 glow hues hold under orbit: visible **side walls**, **roof/cap**, **through-glass spill**
- [ ] Bloom respects sphere limb (not a flat halo card)
- [ ] Far-side remains C3-faint (ghost depth cue, not a second glowing map)
- [ ] Fail if orbit still looks like flat paint / stickers — extrusion/glow craft is not done

**S5 PASS (skill accept):** volume spill on side/limb — glow craft is **not** PASS without this. Far-side stays C3-faint. (MVP orbits S3 set; see note above.)

---

## DoD 5 — Gesture acceptance (MVP)

See `gesture-acceptance.md` for the full PASS table.

- [ ] One-finger drag = orbit (yaw + clamped pitch). Inertia light-settles; no endless spin
- [ ] Pitch clamp ≈ **±35°**
- [ ] Pinch zoom: extrusion + internal glow **hold under scale**; full globe stays readable
- [ ] Double-tap eases to home yaw/pitch **100° / −16°**
- [ ] Far-side stays faint while orbiting (C3 contract)
- [ ] Default data mode = S1 lines; S2 toggle is **not** MVP

S6 select chrome (tap country / long-press continent) is **optional / not boarded** — do not build drawers.

---

## Deferred (do not build in this slice)

| State | Why deferred | When |
|---|---|---|
| **S2** continent grouping | Alternate **toggle**, not default. Extra tint/seam work. Does not prove hero extrusion/glow. | Later APPLY |
| **S4** dense data | Density **stress-test** of S3. 3rd hue + more islands can muddy coasts. | Later APPLY |
| **S6** select chrome | Not boarded. Chrome-light callouts only if asked. | Later |

Numeric targets for S2 / S4 are written in `numeric-craft-targets.md` so a later slice does not freestyle.

---

## Anti-patterns (hard fail — any state)

Skill language. Any one of these is a fail, even if a checkbox above is ticked:

- **Political-map borders** — harsh black / atlas-thick / too-loud country lines
- **Flat painted “glow”** — stickers, neon **outlines**, card-shaped halos, far-side glow maps
- **Toy bar charts** — chunky extrusion, or lift **> ~9.5%** of radius
- **Dark theme** — Pale IOR Veil light only; no dark regress
- **Real APIs** — no live demographics, rankings, or production metrics
- **Treating MOCK as truth** — missing EXAMPLE / MOCK fence on any label
- **Freestyle new globe family** after C3 lock
- **Architecture creep** / production stack lock (Compose / SwiftUI / KMP / Flutter)
- HTML-primary Cavin review (proof is the sandbox + PNG/PDF boards)
- Lime-wrap (unclipped 8-bit wrap)
- Loud far-side continents (second map through the glass)

---

## Sandbox craft PASS (skill DoD — quote)

> Cavin can orbit a soft hollow glass Earth with faint borders and elevated internal-glow islands that read as *inside* the ball; both platforms proven as required; no real demographic claims.

Accept tests the later Implementer sandbox must prove (orbit + pinch at minimum; dual Android+iOS; one proof artifact set). Stack choice is **sandbox only** and does **not** lock production.

| Accept | Looks like |
|---|---|
| S0 | Calm C3 Soft Hollow shell |
| S1 | Borders readable, not harsh |
| S3 | Islands glass, not bars; glow internal + fresnel spill |
| S5 | Volume spill on limb / side — glow craft is not PASS without this |
| MOCK | Banner / disclaimer if any labels |

---

## Companion files (this pack)

| File | Role |
|---|---|
| `numeric-craft-targets.md` | Locked numbers (C3 + overlays + glow + stage) |
| `gesture-acceptance.md` | What PASS looks like for orbit / inertia / pinch / select |
| `asset-contract.md` | `geo_rasters.npz` / Natural Earth reuse vs regenerate |
| `mock-data-contract.md` | MOCK schema + honesty |
| `example-mock-data.json` | Loadable EXAMPLE table (S3 MVP + S4 deferred) |
| `decision-brief.md` | CoS TLDR |
| `locked-references.md` | Absolute paths to locked boards / scripts |
