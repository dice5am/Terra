# TERRA UI-2.5a — Asset contract (geo + Earth)

Prefer pack assets under `/workspace/terra/phase-ui-2/assets/` (NE-derived rasters, mock tables, topo) unless CoS points elsewhere. Document approximations (110m coarseness, Russia-as-Europe NE tag) — honesty, not politics. Freestyle new globe family after C3 lock is a hard fail.

## Must reuse (do not substitute a different ID scheme)

| Asset | Path | What it is |
|---|---|---|
| Country / continent rasters | `/workspace/terra/phase-ui-2/assets/src/geo_rasters.npz` | 2048×1024 equirect fields used by the locked boards |
| ID + name table | `/workspace/terra/phase-ui-2/assets/src/geo_meta.json` | 176 countries, ids **1–176**, continent map |
| Earth topo | `/workspace/terra/phase-ui-2/assets/src/earth_topo.jpg` | Same file as UI-1e `assets/src/earth_topo.jpg` (land mask + coasts) |
| Geo preview (review only) | `/workspace/terra/phase-ui-2/assets/src/geo_preview.png` | Not a runtime asset |

### `geo_rasters.npz` fields

| Key | Shape | Dtype | Range | Use |
|---|---|---|---|---|
| `country_id` | 1024 × 2048 | int16 | 0–176 | 0 = ocean / unset; else NE country id |
| `continent_id` | 1024 × 2048 | uint8 | 0–6 | 0 unset; 1–6 groups below |
| `border` | 1024 × 2048 | float32 | 0–1 | Soft-dilated country-ID discontinuities |
| `cont_border` | 1024 × 2048 | float32 | 0–1 | Soft-dilated continent-ID discontinuities |

### `geo_meta.json`

```
{
  "width": 2048,
  "height": 1024,
  "source": "Natural Earth 110m admin_0_countries (public domain)",
  "continents": {
    "1": "Africa",
    "2": "Americas",
    "3": "Europe",
    "4": "Asia",
    "5": "Oceania",
    "6": "Antarctica"
  },
  "countries": [ { "id", "name", "iso", "continent", "continent_id" }, ... ]
}
```

MOCK tables in the renderer and in `example-mock-data.json` key off these **numeric ids** (USA=5, Brazil=29, …). Changing the id space breaks S3.

---

## Source vectors (present — regenerate only if needed)

| File | Path | Role |
|---|---|---|
| **Primary source** | `/workspace/terra/phase-ui-2/assets/src/ne_110m_admin_0_countries.geojson` | Natural Earth 110m admin_0 countries (public domain). This is what was rasterized. |
| Companion | `/workspace/terra/phase-ui-2/assets/src/ne_110m_admin_0_map_units.geojson` | Not the raster source of record. |
| Companion | `/workspace/terra/phase-ui-2/assets/src/ne_110m_land.geojson` | Land polygons; coasts in the globe come from **topo land-mask ∩ NE**, not this file alone. |

There is **no** checked-in rasterize script in the UI-2 pack. If Implementer must regenerate:

1. Start from `ne_110m_admin_0_countries.geojson` (not a different scale, not map_units).
2. Equirect **2048×1024**.
3. Preserve `geo_meta.json` ids 1–176 and the 6-group continent map (Americas merged; Russia = Europe).
4. Borders = soft-dilated ID discontinuities, **not** vector strokes burned as 1 px lines.
5. Re-diff against the locked `geo_rasters.npz` before replacing it.

**Prefer reuse of the locked npz.** Regeneration is allowed only to port the same fields into an engine format (e.g. GPU texture). Do not silently switch to 50m / 10m / a different Natural Earth edition.

---

## Honesty — 110m is coarse

From `state-matrix.md`, still binding:

- 110m **simplifies** small islands and intricate coasts (fjords, island chains, city-states).
- Borders are **soft-dilated discontinuities in the ID raster**, not hairline vector strokes on the sphere.
- Coastal alignment = NE polygons ∩ land mask from Earth topo. Some mismatch at tiny islands is expected.
- **Russia is tagged Europe** by Natural Earth — accepted for this mock; not a political claim.
- Continent groups: Africa · Americas (NA+SA merged) · Europe · Asia · Oceania · Antarctica. Six groups, not seven.

Do not “fix” Russia, split the Americas, or swap in a higher-res coastline in this APPLY. That would be a new globe, not C3 + UI-2.

---

## Earth sampling (unchanged from UI-1e)

- Equirectangular topo, bilinear sample.
- Sphere: near `z = +√(1−r²)`, far `z = −√(1−r²)`; yaw/pitch rotate; `lon = atan2(x,z)`, `lat = arcsin(y)`.
- Land mask heuristic (renderer): `((R+G) > B*1.35) & ((R+G+B) > 0.18)` plus ice `(R,G,B > 0.55)`.
- **No intentional continent warp.**

---

## May generate (engine-side)

- GPU / runtime textures derived **from** the locked npz (same ids, same 2048×1024 content).
- Mesh / SDF / extrusion geo derived from `country_id` + MOCK heights.
- Bloom / glass as engine equivalents of the numeric targets.

Do **not** generate a new country-id atlas, a new topo, or a new continent grouping.
