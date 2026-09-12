# TERRA UI-2.5a — MOCK data file contract

> **MOCK fence:** Every magnitude, glow hue, and category in this pack is **EXAMPLE / MOCK** for craft review.  
> They are **not** real demographics, GDP, population, traffic, or any measured statistic.  
> Do not cite, ship, or imply as truth. Any on-globe label in a later sandbox must carry an EXAMPLE / MOCK banner.

Aligned with:

- `/workspace/terra/phase-ui-2/docs/mock-data-legend.md`
- `/workspace/terra/phase-ui-2/assets/render_terra_ui2.py` (`MOCK_S3`, `MOCK_S4`, `GLOW_A/B/C`)
- `/workspace/terra/phase-ui-2/assets/src/geo_meta.json` (country ids 1–176)

Loadable table: `example-mock-data.json` (this directory).

---

## Schema (Implementer can load)

```json
{
  "disclaimer": "EXAMPLE / MOCK — not real demographics",
  "glow_types": {
    "A": { "name": "EXAMPLE Activity Index", "rgb": [0.25, 0.85, 0.95] },
    "B": { "name": "EXAMPLE Flow Volume",    "rgb": [1.00, 0.55, 0.28] },
    "C": { "name": "EXAMPLE Density Signal", "rgb": [0.72, 0.42, 1.00] }
  },
  "height_tiers": [
    { "min": 0.30, "max": 0.45, "feel": "slight crystal lift" },
    { "min": 0.45, "max": 0.65, "feel": "clear island extrusion" },
    { "min": 0.65, "max": 0.90, "feel": "tallest islands — still sleek glass, not bars" }
  ],
  "sets": {
    "S3": { "mvp": true,  "items": [ /* { country_id, name, iso, height, glow } */ ] },
    "S4": { "mvp": false, "items": [ /* S3 ∪ extras */ ] }
  }
}
```

| Field | Type | Rule |
|---|---|---|
| `country_id` | int | **Must** match `geo_meta.json` / `geo_rasters.npz` (`USA=5`, `BRA=29`, …). Do not invent ids. |
| `name` | string | NE 110m name (honesty label only) |
| `iso` | string | ISO from geo_meta |
| `height` | float 0–1 | MOCK magnitude → radial extrusion. Tiers above. |
| `glow` | `"A"` \| `"B"` \| `"C"` | Hue set. MVP S3 = A+B only. C arrives with deferred S4. |

`sets.S4.items` = `sets.S3.items` ∪ extras (same ids never appear twice with different heights).

---

## S3 set (MVP — 7 islands, 2 hues)

| country_id | NE name | iso | height | glow | tier |
|---|---|---|---|---|---|
| 5 | United States of America | USA | 0.72 | A Activity | tallest |
| 29 | Brazil | BRA | 0.58 | B Flow | clear |
| 121 | Germany | DEU | 0.48 | A Activity | clear |
| 98 | India | IND | 0.80 | B Flow | tallest |
| 155 | Japan | JPN | 0.55 | A Activity | clear |
| 25 | South Africa | ZAF | 0.42 | B Flow | slight |
| 137 | Australia | AUS | 0.50 | A Activity | clear |

S3 max height **0.80** → `R_ext = 1 + 0.80 × 0.085 = 1.068` (**+6.8%** radius) at board `extrude_scale`.

---

## S4 extras (deferred — 3rd hue)

Do not load into the MVP sandbox unless CoS pulls S4 forward. Boarded S5 used this denser set.

| country_id | NE name | iso | height | glow |
|---|---|---|---|---|
| 139 | China | CHN | 0.88 | C Density |
| 56 | Nigeria | NGA | 0.62 | B Flow |
| 27 | Mexico | MEX | 0.45 | A Activity |
| 43 | France | FRA | 0.40 | A Activity |
| 143 | United Kingdom | GBR | 0.38 | A Activity |
| 9 | Indonesia | IDN | 0.70 | C Density |
| 163 | Egypt | EGY | 0.35 | B Flow |
| 10 | Argentina | ARG | 0.44 | B Flow |
| 4 | Canada | CAN | 0.36 | A Activity |
| 158 | Saudi Arabia | SAU | 0.52 | C Density |
| 14 | Kenya | KEN | 0.33 | B Flow |
| 132 | Spain | ESP | 0.34 | A Activity |
| 141 | Italy | ITA | 0.37 | A Activity |
| 19 | Russia | RUS | 0.60 | C Density |
| 124 | Turkey | TUR | 0.41 | B Flow |
| 32 | Colombia | COL | 0.39 | B Flow |

S4 max height **0.88** (China) → `R_ext = 1.0748` (**+7.48%**). Still under the +9.5% cap.

---

## Caption / badge rule

Every review board, sandbox label, and decision brief carries **EXAMPLE / MOCK** labeling. No board or runtime chrome may present these as real stats.

Heights and hues here **are** the lock (copied from the render script). Do not retune “for taste.”
