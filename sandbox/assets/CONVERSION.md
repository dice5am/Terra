# Asset conversion notes

Source (locked, do not substitute ID scheme):
- `/workspace/terra/phase-ui-2/assets/src/geo_rasters.npz`
- `/workspace/terra/phase-ui-2/assets/src/earth_topo.jpg`
- `/workspace/terra/phase-ui-2/assets/src/geo_meta.json`

Generated under `sandbox/assets/`:

| File | Format | Contents |
|---|---|---|
| `geo_pack.png` | RGBA8 2048×1024 | R=`country_id` (0–176 exact), G=`continent_id` (0–6), B=`border`×255, A=`cont_border`×255 |
| `country_id.png` | L8 | country_id 0–176 |
| `continent_id.png` | L8 | continent_id 0–6 |
| `border.png` | L8 | soft border field |
| `earth_topo.jpg` / `.webp` | RGB 2048×1024 | equirect topo (LANCZOS from source) |
| `land_coast.png` | RGBA8 | R=land mask, G=coast edge (UI-2 heuristic) |
| `mock_s3_height_glow.png` | RGBA8 | R=height×255, G=glowType (0=none,1=A,2=B), B=country_id |
| `geo_meta.json` | copy | ids 1–176 |
| `example-mock-data.json` | copy | S3 MVP MOCK |

Shader sampling: nearest for country_id / glow type; linear for border, land, topo.
Country IDs remain Natural Earth 110m 1–176. Russia tagged Europe per NE — accepted mock.
