# TERRA UI-2.5a — Numeric craft targets

Designer half of TERRA globe craft APPLY. Extracted from locked **UI-1e C3 Soft Hollow** (`render_terra_ui1e.py` `variant_params("C3")`) and **UI-2** (`render_terra_ui2.py` `C3` dict + overlay constants).  
Baseline: **Pale IOR Veil** light · C3 Soft Hollow · faint far-side · whisper borders · internal glow + fresnel spill.  
Do **not** freestyle a new globe family. If a number fights a locked board, stop and escalate to CoS — do not invent a third value.

Sources:

- `/workspace/terra/phase-ui-1e/assets/render_terra_ui1e.py`
- `/workspace/terra/phase-ui-2/assets/render_terra_ui2.py`
- `/workspace/terra/phase-ui-2/docs/state-matrix.md`
- `/workspace/terra/phase-ui-2/docs/mock-data-legend.md`
- `/workspace/terra/phase-ui-1e/docs/proof-notes.md`

---

## 1. C3 Soft Hollow shell (locked base — all states)

UI-2 copies the UI-1e C3 dict **verbatim**. These are APPLY constants.

| Dial | Value | Feel |
|---|---|---|
| `glass_thick` | **0.62** | Thinner shell than C0/C2 (those were 1.0 / 1.18). Hollow read, not solid bar. |
| `ocean_body_a` | **0.20** | Low body density (C0 was 0.36, C2 was 0.52). Soft hollow, not dense glass brick. |
| `ocean_tint_a` | **0.10** | Whisper ocean tint |
| `rim_gain` | **0.92** | Stronger rim than C0 (0.72) |
| `shell_rim_boost` | **1.35** | Hollow shell sold by rim, not by far-map |
| `tunnel_clarity` | **1.15** | Slightly opener ocean transmit than C0 (1.0) |
| `ior_bend` | **0.16** | Softer far refraction than C0 (0.24) |
| `fresnel_pow` | **2.15** | |
| `spec_gain` | **0.24** | |
| `near_land_a` | **0.30** | |
| `near_coast_boost` | **0.40** | |
| `land_fill` | **0.06** | Light land fill (C0 was 0.10) |
| `through_land` | **0.12** | |
| `coast_etch` | **0.42** | |
| `land_rgb` | **(0.70, 0.76, 0.82)** | Pale cool land |
| `far_land_rgb` | **(0.58, 0.66, 0.76)** | |
| `ocean_rgb` | **(0.54, 0.72, 0.86)** | |

Rim ring (renderer): Gaussian bump at `radial ≈ 0.92 + 0.04·glass_thick` (= **0.9448** at C3), sigma² = `0.0018 + 0.001·glass_thick`. Glass edge ring at `radial ≈ 0.985`.

Light dir (locked): **(0.35, −0.42, 0.84)** normalized.

---

## 2. Far-side fade — stay at C3 levels

**Must stay faint.** Elevated glow is near-side / limb only. Do not add a far glow map.

| Dial | C3 / UI-2 value | Do not use |
|---|---|---|
| `far_land_gain` | **0.15** | C0 loud 0.42 · C1 0.11 |
| `far_coast_gain` | **0.22** | C0 0.58 |
| `far_blur_px` | **3** | C0 = 2 · C1/C2 = 4 |
| `far_path_atten` | **0.65** | C0 = 1.0 · C1 = 0.55 |
| `far_limb_suppress` | **0.45** | C0 = 0.25 |

Honesty gate (UI-1e C3 measured):

| Metric | Front | Orbit (~115° C3 proof) |
|---|---|---|
| far-weight mean | 0.01254 | 0.02387 |
| far-weight **p95** | 0.07821 | **0.09017** |

**APPLY fail:** far p95 **> 0.30** (loud second map).  
**Flag:** far p95 **< 0.025** (may fail to prove 3D at a glance).  
Target stay-near **C3 ≈ 0.09 p95 on orbit**, not C0 ≈ 0.39.

Blur implementation in the lock: 6 multi-samples when `far_blur_px=3` (`n_off = min(3*2, 8) = 6`) with offset scale `1 + bend + 0.35*(far_blur_px/4)`.

---

## 3. Extrusion (S3 / S5 MVP; S4 later)

Renderer: `R_ext = 1.0 + max(mock_height) * extrude_scale`.

| Context | `extrude_scale` | Resulting max lift |
|---|---|---|
| In-app / boards (APPLY) | **0.085** | height 1.0 → **+8.5%** radius |
| Review closeups only | 0.095 | height 1.0 → +9.5% (do **not** ship this as the app cap) |

State-matrix language: “~max **+7–9%** radius.” That is the **scale family**, not S3’s current tallest island.

Measured board `R_ext` (`proof_meta.json`):

| State | max mock height | `R_ext` | % of radius |
|---|---|---|---|
| S3 | 0.80 (India) | 1.068 | **+6.8%** |
| S4 / boarded S5 | 0.88 (China) | 1.0748 | **+7.48%** |

**Hard cap:** never exceed **+9.5%** of radius (even if a future mock hits 1.0).  
**Fail:** chunky toy bars, or islands that read as a 3D bar chart.

### Height tiers (MOCK 0–1) — from `mock-data-legend.md`

| Mock height | Visual |
|---|---|
| **0.30–0.45** | Slight crystal lift |
| **0.45–0.65** | Clear island extrusion |
| **0.65–0.90** | Tallest islands — still sleek glass, not bars |

Island body (renderer, keep the ratios):

- Trigger: `elev > 0.05` and `land > 0.25`
- Crystal lift add: `thick * 0.55 * 0.35` · `crystal_col = (0.88, 0.94, 1.0)`
- Denser fill alpha: `thick * 0.28`
- Soft side walls: `border * thick * (0.55 + 0.45 * fresnel)` · `wall_col = (0.70, 0.82, 0.95)`
- Extruded ring wall thickness ≈ `0.012 + elev * 0.02` (in unit-sphere radii)
- Roof alpha: `0.55 + 0.25 * elev` · `roof_col = (0.82, 0.90, 0.98)`
- Side col: `(0.65, 0.78, 0.92)`

---

## 4. S1 border feel (default data mode)

Borders are a **soft-dilated ID-discontinuity field** (`geo_rasters.npz` → `border`, 0–1), **not** a 1 px vector stroke.

| Mode | `line_a` | `line_col` |
|---|---|---|
| **S1** (default) | `border * land *` **0.22** | **(0.42, 0.50, 0.60)** |
| S3 / S4 / S5 | `border * land *` **0.14** | same |
| S2 (deferred) | `border * land *` **0.10** | same (quieter under tint) |

Never harsh black. Fail if S1 ≈ S0 **or** if it reads as a political atlas.

---

## 5. S2 continent tint (deferred — specify for later)

Do **not** build in MVP. Locked so a later slice cannot freestyle.

Tint alpha: `land *` **0.34** (apply only where `continent_id > 0` and `land > 0.3`).  
Pale IOR family — **not** a saturated choropleth.

| ID | Group | `CONT_TINT` RGB |
|---|---|---|
| 1 | Africa | **(0.78, 0.68, 0.52)** warm sand |
| 2 | Americas (NA+SA merged) | **(0.55, 0.72, 0.64)** sage |
| 3 | Europe | **(0.62, 0.68, 0.82)** lavender-blue |
| 4 | Asia | **(0.78, 0.62, 0.68)** rose |
| 5 | Oceania | **(0.52, 0.74, 0.76)** aqua |
| 6 | Antarctica | **(0.82, 0.86, 0.92)** cool |

Continent seams (clearer than country lines):

- `seam_col = (0.34, 0.44, 0.58)`
- `seam_a = cont_border * land *` **0.48**

Saturation / alpha limits: keep the RGB above (already desaturated). Do not raise tint alpha above **0.34**. Do not invert to a political-map chroma.

NE tags **Russia as Europe** (`continent_id = 3`) — accepted for this mock; not a political claim.

---

## 6. Glow — internal emission, not outline

Hue set from `mock-data-legend.md` + renderer constants:

| Code | EXAMPLE category | RGB | Used in |
|---|---|---|---|
| **A** | EXAMPLE Activity Index | **(0.25, 0.85, 0.95)** cyan / teal | S3, S4, S5 |
| **B** | EXAMPLE Flow Volume | **(1.00, 0.55, 0.28)** amber / coral | S3, S4, S5 |
| **C** | EXAMPLE Density Signal | **(0.72, 0.42, 1.00)** violet | S4, S5 only (deferred with S4) |

MVP uses **A + B only**.

Emission (keep ratios; this is the “inside the ball” read):

- Core: `thick * (1 − border*0.7) * (0.55 + 0.45*nz)` — stronger **away from** the country outline
- Add core `* 0.55 * glow_rgb`
- Fresnel bleed: `core * (0.35 + 0.90*fresnel) * (0.7 + 0.3*thick)` added `* 0.70 * glow_rgb`
- Extruded-volume glow: `elev * 0.50 * (0.4 + 0.6*fr) * glow_rgb`

### Bloom

| Pass | Radius | Mix |
|---|---|---|
| Tight | **Gaussian 14** | 0.55 |
| Soft | **Gaussian 28** | 0.85 |
| Composite add | `(tight*0.55 + soft*0.85) * 0.85` | limb-masked |

Limb mask: bloom lives inside `radial ≤ R_ext + 0.04`, fade over **0.08** beyond `R_ext`.  
Not a card-shaped halo. Not an outline stroke.

**Fail:** glow as neon country outline; glow painted on the far side; bloom ignoring the sphere limb.

---

## 7. Light theme stage

C3 / UI-2 use **cool_glass** (not the warmer C0–C2 stage).

| Token | Value |
|---|---|
| `stage_rgb` (globe composite) | **(0.96, 0.95, 0.93)** |
| Content canvas | **1170 × 2080** |
| Globe radius on stage | **470** px (S0/S1); **490** px when extrusion is on (S3/S5) |
| Globe center | `(585, 1076)` = `(W/2, H/2 + 36)` |
| Stage gradient (cool_glass) | top ≈ rgb(248, 252, 240) → bottom cooler / slightly bluer (see `gradient_bg("cool_glass")`) |
| Studio fill | radial strength **18**, radius **900**, cool (`0.92, 1.0, 1.1`) — not warm |
| Phone-chrome surround | rgb(236, 238, 242) |
| Ground shadow | ellipse under globe, rgb(40, 50, 70) @ alpha 50, blur 34 |
| Reflection | flipped globe, brightness 0.32, alpha fade |

**Light theme only.** No dark mode in this APPLY.

---

## 8. Dual platform — status bar / safe area only

Same globe model on iOS and Android. **No extra chrome.**

| | iOS | Android |
|---|---|---|
| Status fill | rgba(28, 32, 38, 230) | same |
| Time | “9:41” @ x=52, y≈22, 28pt bold | “9:41” @ x=36, y≈20, 26pt |
| Center | Dynamic Island 126×36, radius 18, black | (none) |
| Trailing | battery + wifi | battery + signal bars + wifi |
| Home indicator | 140×6 pill, y = content−18 | 120×5 bar, y = content−16 |
| Safe area | keep globe clear of island + home indicator | keep globe clear of status icons + home bar |

Do not add tab bars, drawers, legends, or filter chips in this APPLY.  
Optional S6 (not boarded): soft select rim + EXAMPLE label chip only.

---

## 9. Camera / framing

| Pose | Yaw | Pitch | Notes |
|---|---|---|---|
| Home / S0–S3 front | **100.0°** | **−16.0°** | Same as UI-1e C3 / UI-1d C |
| S5 orbit proof | **210.0°** | **−12.0°** | Home + **110°** (UI-2 lock) |
| UI-1e C3 far-side proof | 215.0° | −12.0° | Home + 115°. Reference only — **do not** use 115° for S5 |

Pitch clamp in-app: **≈ ±35°** (UI-1e gesture contract).

---

## 10. Conflicts logged (do not invent a third number)

1. **`extrude_scale` 0.085 (boards) vs 0.095 (closeups).** APPLY = **0.085**. Closeup 0.095 is review-detail only.
2. **S3 max lift +6.8% vs state-matrix “~7–9%”.** 7–9% is the scale family (`0.085–0.095` at height 1.0). S3’s tallest MOCK is 0.80 → 6.8%. Keep both; do not raise India to manufacture 9%.
3. **S5 boards used MOCK_S4; MVP S5 orbits S3.** Same craft, fewer islands. Pixel-match to S5 boards would pull S4 into MVP — CoS call, not a Designer invent.
4. **Orbit 110° (UI-2 S5) vs 115° (UI-1e C3).** APPLY S5 = **110°**.

No other number-vs-board fights found. C3 dict in UI-2 matches UI-1e C3 exactly.
