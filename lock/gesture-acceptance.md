# TERRA UI-2.5a — Gesture acceptance (what PASS looks like)

Pulled from:

- `/workspace/terra/phase-ui-2/docs/gesture-ux.md`
- `/workspace/terra/phase-ui-1e/docs/gesture-ux.md`

Design intent only — no production-stack lock. S6 select is optional / not boarded.

**Sandbox minimum (skill):** orbit + pinch. Dual Android+iOS. Glow craft is not PASS until S5 volume spill reads *inside* the ball.


---

## Core gestures (MVP)

| Gesture | Behavior | PASS | FAIL |
|---|---|---|---|
| **One-finger drag (H)** | Yaw the globe. Near / far land swap via **back-face sample** (volumetric, not a painted sticker). | After a ~110° orbit, S3 islands show **thickness + side walls**; glow **spills in volume**; far-side continents are a **C3 ghost**, not a second map. | Orbit looks like a flat texture spinning. Far-side as loud as near. Glow as a 2D decal that just slides. |
| **One-finger drag (V)** | Pitch. | Pitch **clamps ≈ ±35°**. Globe never tumbles over the poles. | Free tumble / upside-down Earth / no clamp. |
| **Inertia** | Light settle after release. | Short coast, then rest. Same heading the user left it on. | Endless spin, or a dead stop with no settle. |
| **Pinch** | Zoom toward limb / elevated islands. | Extrusion **and internal glow hold under scale**. Islands stay sleek glass (not bars). Full globe remains readable (do not crop to a single country). Limb fresnel still present. | Glow becomes an outline at zoom. Islands become chunky bars. Globe cropped so C3 shell is lost. |
| **Double-tap** | Ease to home pose. | Animates to yaw **100°**, pitch **−16°** (C3 / UI-2 front). | Snaps with no ease, or home pose drifts from the locked framing. |

---

## Data-mode contract

| Rule | PASS |
|---|---|
| Default data mode | **S1 country lines on** at launch. |
| S2 continent grouping | A **toggle**, not a second app — **deferred** this slice. Do not ship S2 as the default. |
| Magnitude read | Height of the crystal island **+ glow intensity**. No separate legend panel required for glance craft. (Legend exists only in review docs.) |

---

## Depth contract (holds during every gesture)

From UI-1e, still binding:

- Far-side stays a **faint** cue at **C3 levels** (see `numeric-craft-targets.md`).
- Near coasts stay accurate (no artistic warp).
- Limb fresnel always present.
- Light theme only.
- Same model iOS + Android.

S5 is the honesty check: if the orbited globe still reads as flat paint, extrusion / glow craft has **not** PASSed — do not call the slice done.

---

## Optional S6 (not boarded — do not build in MVP)

Chrome-light only, if a later slice asks:

- **Tap country** → soft select rim + EXAMPLE label chip (never real stats).
- **Long-press continent** → soft continent highlight in S2 tint language.
- No heavy drawers, no dashboard chrome, no filters, no time scrubbers.

---

## Out of scope

Real APIs, auth, filters, time scrubbers, production analytics, dark mode.
