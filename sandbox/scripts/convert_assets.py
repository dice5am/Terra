#!/usr/bin/env python3
"""Convert locked geo_rasters.npz + earth_topo.jpg → GPU-ready textures under sandbox/assets/.

Preserves country_id 1–176. Does NOT regenerate Natural Earth ids.
"""
from __future__ import annotations
import json
import shutil
from pathlib import Path
import numpy as np
from PIL import Image

SRC = Path("/workspace/terra/phase-ui-2/assets/src")
OUT = Path("/workspace/terra/phase-ui-2-tech/sandbox/assets")
OUT.mkdir(parents=True, exist_ok=True)

z = np.load(SRC / "geo_rasters.npz")
country = z["country_id"]  # int16 1024x2048, 0-176
continent = z["continent_id"]  # uint8
border = z["border"].astype(np.float32)
cont_border = z["cont_border"].astype(np.float32)

assert country.shape == (1024, 2048)
assert int(country.max()) == 176

# Pack: R=country_id/255, G=continent_id/255, B=border, A=cont_border
# country_id is 0-176 so fits in 8-bit with exact integer values when *255/255
pack = np.zeros((1024, 2048, 4), dtype=np.uint8)
pack[..., 0] = np.clip(country, 0, 255).astype(np.uint8)  # exact id 0-176
pack[..., 1] = continent.astype(np.uint8)
pack[..., 2] = np.clip(border * 255.0, 0, 255).astype(np.uint8)
pack[..., 3] = np.clip(cont_border * 255.0, 0, 255).astype(np.uint8)
Image.fromarray(pack, "RGBA").save(OUT / "geo_pack.png", optimize=True)

# Also save raw float border as greyscale for higher fidelity sampling (optional)
border_u16 = np.clip(border * 65535.0, 0, 65535).astype(np.uint16)
# PNG doesn't do grey16 easily via PIL without mode I; keep 8-bit primary + note
Image.fromarray(pack[..., 2], "L").save(OUT / "border.png", optimize=True)
Image.fromarray(pack[..., 0], "L").save(OUT / "country_id.png", optimize=True)
Image.fromarray(pack[..., 1], "L").save(OUT / "continent_id.png", optimize=True)

# Earth topo — resize to 2048x1024 to match geo equirect
earth = Image.open(SRC / "earth_topo.jpg").convert("RGB")
earth_r = earth.resize((2048, 1024), Image.Resampling.LANCZOS)
earth_r.save(OUT / "earth_topo.jpg", quality=92)
# Also keep a webp for smaller loads
earth_r.save(OUT / "earth_topo.webp", quality=90)

# Precompute land mask (same heuristic as render_terra_ui2.py)
arr = np.asarray(earth_r).astype(np.float32) / 255.0
r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
land = ((r + g) > (b * 1.35)) & ((r + g + b) > 0.18)
ice = (r > 0.55) & (g > 0.55) & (b > 0.55)
land = land | ice
land_f = land.astype(np.float32)

# Coast edge from land mask (same as land_edge_from_mask)
lm = land_f
dx = np.abs(np.roll(lm, 1, axis=1) - np.roll(lm, -1, axis=1))
dy = np.abs(np.roll(lm, 1, axis=0) - np.roll(lm, -1, axis=0))
edge = np.clip(dx + dy, 0, 1)
for _ in range(2):
    edge = (edge + np.roll(edge, 1, 0) + np.roll(edge, -1, 0) + np.roll(edge, 1, 1) + np.roll(edge, -1, 1)) / 5.0
edge = np.clip(edge * 2.5, 0, 1).astype(np.float32)

# Land+coast pack: R=land, G=coast, B=0, A=1
lc = np.zeros((1024, 2048, 4), dtype=np.uint8)
lc[..., 0] = np.clip(land_f * 255, 0, 255).astype(np.uint8)
lc[..., 1] = np.clip(edge * 255, 0, 255).astype(np.uint8)
lc[..., 2] = 0
lc[..., 3] = 255
Image.fromarray(lc, "RGBA").save(OUT / "land_coast.png", optimize=True)

# Height + glow maps from S3 mock (for GPU LUT sampling)
meta = json.loads((SRC / "geo_meta.json").read_text())
mock_path = Path("/workspace/terra/phase-ui-2-tech/example-mock-data.json")
mock = json.loads(mock_path.read_text())
glow_map = {"A": 0, "B": 1, "C": 2}
hmap = np.zeros(country.shape, dtype=np.float32)
gmap = np.full(country.shape, 0, dtype=np.uint8)  # 0=none; store glow+1 so 0 means none
for item in mock["sets"]["S3"]["items"]:
    cid = item["country_id"]
    m = country == cid
    hmap[m] = float(item["height"])
    gmap[m] = glow_map[item["glow"]] + 1  # 1=A, 2=B, 3=C

hg = np.zeros((1024, 2048, 4), dtype=np.uint8)
hg[..., 0] = np.clip(hmap * 255, 0, 255).astype(np.uint8)
hg[..., 1] = gmap  # 0 none, 1 A, 2 B
hg[..., 2] = pack[..., 0]  # country id echo
hg[..., 3] = 255
Image.fromarray(hg, "RGBA").save(OUT / "mock_s3_height_glow.png", optimize=True)

# Copy meta + mock json into assets
shutil.copy2(SRC / "geo_meta.json", OUT / "geo_meta.json")
shutil.copy2(mock_path, OUT / "example-mock-data.json")

# Conversion doc
doc = """# Asset conversion notes

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
"""
(OUT / "CONVERSION.md").write_text(doc)
print("Wrote assets to", OUT)
for p in sorted(OUT.iterdir()):
    print(f"  {p.name:40s} {p.stat().st_size:10d}")
