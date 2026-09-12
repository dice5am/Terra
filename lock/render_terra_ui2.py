#!/usr/bin/env python3
"""TERRA Phase UI-2 — Demographic-style data ON the globe (design mock ONLY).

Locked base: UI-1e C3 Soft Hollow (Pale IOR Veil).
States S0–S5: globe → country lines → continents → elevated glow → dense → orbit.
ALWAYS np.clip before uint8. lime-wrap = 0.
All magnitudes are EXAMPLE / MOCK — never real demographics.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont, ImageChops

ROOT = Path("/workspace/terra/phase-ui-2")
SRC = ROOT / "assets" / "src"
EARTH_SRC = SRC / "earth_topo.jpg"
GEO_NPZ = SRC / "geo_rasters.npz"
GEO_META = SRC / "geo_meta.json"
PLATES = ROOT / "assets" / "plates"
BOARDS = ROOT / "boards"
CLOSEUPS = ROOT / "closeups"
DOCS = ROOT / "docs"
PREVIEW = ROOT / "assets" / "preview"

for d in (PLATES, BOARDS, CLOSEUPS, DOCS, PREVIEW):
    d.mkdir(parents=True, exist_ok=True)

W, H = 1170, 2080
GLOBE_R = 470
CX, CY = W // 2, H // 2 + 36

# C3 Soft Hollow params (locked from UI-1e)
C3 = dict(
    far_land_gain=0.15,
    far_coast_gain=0.22,
    near_land_a=0.30,
    near_coast_boost=0.40,
    ocean_tint_a=0.10,
    ocean_body_a=0.20,
    ior_bend=0.16,
    far_blur_px=3,
    glass_thick=0.62,
    land_rgb=np.array([0.70, 0.76, 0.82], dtype=np.float32),
    far_land_rgb=np.array([0.58, 0.66, 0.76], dtype=np.float32),
    ocean_rgb=np.array([0.54, 0.72, 0.86], dtype=np.float32),
    fresnel_pow=2.15,
    spec_gain=0.24,
    rim_gain=0.92,
    through_land=0.12,
    land_fill=0.06,
    far_path_atten=0.65,
    far_limb_suppress=0.45,
    tunnel_clarity=1.15,
    shell_rim_boost=1.35,
    coast_etch=0.42,
)

# Continent soft tints (Pale IOR family — not political map)
CONT_TINT = {
    1: np.array([0.78, 0.68, 0.52], dtype=np.float32),  # Africa warm sand
    2: np.array([0.55, 0.72, 0.64], dtype=np.float32),  # Americas sage
    3: np.array([0.62, 0.68, 0.82], dtype=np.float32),  # Europe lavender-blue
    4: np.array([0.78, 0.62, 0.68], dtype=np.float32),  # Asia rose
    5: np.array([0.52, 0.74, 0.76], dtype=np.float32),  # Oceania aqua
    6: np.array([0.82, 0.86, 0.92], dtype=np.float32),  # Antarctica cool
}

# Glow hues for EXAMPLE mock data types (sci-fi glass emission)
GLOW_A = np.array([0.25, 0.85, 0.95], dtype=np.float32)  # cyan — Activity Index
GLOW_B = np.array([1.00, 0.55, 0.28], dtype=np.float32)  # amber — Flow Volume
GLOW_C = np.array([0.72, 0.42, 1.00], dtype=np.float32)  # violet — Density Signal

# Mock elevation / glow assignments (country_id → height 0..1, glow type 0/1/2)
# Heights are FAKE EXAMPLE magnitudes for craft review only.
MOCK_S3 = {
    # id: (height, glow_type)
    5: (0.72, 0),    # USA — Activity
    29: (0.58, 1),   # Brazil — Flow
    121: (0.48, 0),  # Germany — Activity
    98: (0.80, 1),   # India — Flow
    155: (0.55, 0),  # Japan — Activity
    25: (0.42, 1),   # South Africa — Flow
    137: (0.50, 0),  # Australia — Activity
}

MOCK_S4 = {
    **MOCK_S3,
    139: (0.88, 2),  # China — Density
    56: (0.62, 1),   # Nigeria — Flow
    27: (0.45, 0),   # Mexico — Activity
    43: (0.40, 0),   # France — Activity
    143: (0.38, 0),  # UK — Activity
    9: (0.70, 2),    # Indonesia — Density
    163: (0.35, 1),  # Egypt — Flow
    10: (0.44, 1),   # Argentina — Flow
    4: (0.36, 0),    # Canada — Activity
    158: (0.52, 2),  # Saudi Arabia — Density
    14: (0.33, 1),   # Kenya — Flow
    132: (0.34, 0),  # Spain — Activity
    141: (0.37, 0),  # Italy — Activity
    19: (0.60, 2),   # Russia — Density
    124: (0.41, 1),  # Turkey — Flow
    32: (0.39, 1),   # Colombia — Flow
}


def load_earth(max_w=2700):
    im = Image.open(EARTH_SRC).convert("RGB")
    if im.width > max_w:
        h = int(im.height * max_w / im.width)
        im = im.resize((max_w, h), Image.Resampling.LANCZOS)
    arr = np.asarray(im).astype(np.float32) / 255.0
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    land = ((r + g) > (b * 1.35)) & ((r + g + b) > 0.18)
    ice = (r > 0.55) & (g > 0.55) & (b > 0.55)
    land = land | ice
    return arr, land.astype(np.float32)


def land_edge_from_mask(land_f):
    lm = land_f
    dx = np.abs(np.roll(lm, 1, axis=1) - np.roll(lm, -1, axis=1))
    dy = np.abs(np.roll(lm, 1, axis=0) - np.roll(lm, -1, axis=0))
    edge = np.clip(dx + dy, 0, 1)
    for _ in range(2):
        edge = (
            edge
            + np.roll(edge, 1, 0)
            + np.roll(edge, -1, 0)
            + np.roll(edge, 1, 1)
            + np.roll(edge, -1, 1)
        ) / 5.0
    return np.clip(edge * 2.5, 0, 1).astype(np.float32)


def load_geo():
    z = np.load(GEO_NPZ)
    meta = json.loads(GEO_META.read_text())
    return {
        "country_id": z["country_id"],
        "continent_id": z["continent_id"],
        "border": z["border"].astype(np.float32),
        "cont_border": z["cont_border"].astype(np.float32),
        "meta": meta,
    }


def sample_equirect(arr, land, edge, lon, lat):
    h, w = arr.shape[:2]
    u = (lon / (2 * math.pi) + 0.5) % 1.0
    v = 0.5 - (lat / math.pi)
    x = u * (w - 1)
    y = np.clip(v * (h - 1), 0, h - 1)
    xi = np.clip(x.astype(np.int32), 0, w - 1)
    yi = np.clip(y.astype(np.int32), 0, h - 1)
    x1 = np.clip(xi + 1, 0, w - 1)
    y1 = np.clip(yi + 1, 0, h - 1)
    fx = (x - xi).astype(np.float32)[..., None] if arr.ndim == 3 else (x - xi).astype(np.float32)
    fy = (y - yi).astype(np.float32)[..., None] if arr.ndim == 3 else (y - yi).astype(np.float32)
    c00 = arr[yi, xi]
    c10 = arr[yi, x1]
    c01 = arr[y1, xi]
    c11 = arr[y1, x1]
    if arr.ndim == 3:
        tex = c00 * (1 - fx) * (1 - fy) + c10 * fx * (1 - fy) + c01 * (1 - fx) * fy + c11 * fx * fy
    else:
        tex = c00 * (1 - (x - xi)) * (1 - (y - yi)) + c10 * (x - xi) * (1 - (y - yi))
        tex = tex + c01 * (1 - (x - xi)) * (y - yi) + c11 * (x - xi) * (y - yi)
    lf = land[yi, xi] * (1 - (x - xi)) * (1 - (y - yi)) + land[yi, x1] * (x - xi) * (1 - (y - yi))
    lf = lf + land[y1, xi] * (1 - (x - xi)) * (y - yi) + land[y1, x1] * (x - xi) * (y - yi)
    ef = edge[yi, xi]
    return tex.astype(np.float32), np.clip(lf, 0, 1).astype(np.float32), ef.astype(np.float32)


def sample_scalar(field, lon, lat):
    """Nearest + bilinear for 2D scalar/int field."""
    h, w = field.shape[:2]
    u = (lon / (2 * math.pi) + 0.5) % 1.0
    v = 0.5 - (lat / math.pi)
    x = u * (w - 1)
    y = np.clip(v * (h - 1), 0, h - 1)
    xi = np.clip(x.astype(np.int32), 0, w - 1)
    yi = np.clip(y.astype(np.int32), 0, h - 1)
    x1 = np.clip(xi + 1, 0, w - 1)
    y1 = np.clip(yi + 1, 0, h - 1)
    fx = (x - xi).astype(np.float32)
    fy = (y - yi).astype(np.float32)
    if field.dtype in (np.int16, np.int32, np.uint8, np.int64):
        # nearest for IDs
        return field[yi, xi]
    c00 = field[yi, xi]
    c10 = field[yi, x1]
    c01 = field[y1, xi]
    c11 = field[y1, x1]
    return (c00 * (1 - fx) * (1 - fy) + c10 * fx * (1 - fy) + c01 * (1 - fx) * fy + c11 * fx * fy).astype(
        np.float32
    )


def rotate_points(x, y, z, yaw_rad, pitch_rad):
    cp, sp = math.cos(pitch_rad), math.sin(pitch_rad)
    cy, sy = math.cos(yaw_rad), math.sin(yaw_rad)
    y1 = y * cp - z * sp
    z1 = y * sp + z * cp
    x1 = x
    x2 = x1 * cy + z1 * sy
    y2 = y1
    z2 = -x1 * sy + z1 * cy
    return x2, y2, z2


def xyz_to_lonlat(x, y, z):
    lat = np.arcsin(np.clip(y, -1, 1))
    lon = np.arctan2(x, z)
    return lon, lat


def build_mock_maps(geo, mock_dict):
    """Per-pixel equirect height + glow_type from country mock table."""
    cid = geo["country_id"]
    hmap = np.zeros(cid.shape, dtype=np.float32)
    gmap = np.full(cid.shape, -1, dtype=np.int8)
    for c_id, (ht, gt) in mock_dict.items():
        m = cid == c_id
        hmap[m] = ht
        gmap[m] = gt
    return hmap, gmap


def render_globe(
    earth,
    land_m,
    edge_m,
    geo,
    *,
    yaw_deg=100.0,
    pitch_deg=-16.0,
    size=1100,
    mode="S0",
    mock_dict=None,
    stage_rgb=(0.96, 0.95, 0.93),
    extrude_scale=0.085,
):
    """Render C3 Soft Hollow + optional overlays. mode in S0..S5."""
    yaw = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)
    p = C3
    n = size
    yy, xx = np.mgrid[0:n, 0:n]
    nx = (xx + 0.5) / n * 2 - 1
    ny = -((yy + 0.5) / n * 2 - 1)
    r2 = nx * nx + ny * ny
    radial = np.sqrt(np.clip(r2, 0, 4))

    # Max extrusion for this mode
    if mock_dict:
        max_h = max(v[0] for v in mock_dict.values()) if mock_dict else 0.0
    else:
        max_h = 0.0
    R_ext = 1.0 + max_h * extrude_scale if mode in ("S3", "S4", "S5") else 1.0

    # Base unit sphere mask + extended disk for crystal islands
    mask_unit = r2 <= 1.0
    mask_ext = r2 <= (R_ext * R_ext)
    nz_abs = np.zeros_like(nx)
    nz_abs[mask_unit] = np.sqrt(np.clip(1.0 - r2[mask_unit], 0, 1))

    # For extended ring: project direction to unit limb / elevated shell
    # Cap points: on sphere of radius R_local, orthographic → r_screen = sqrt(x^2+y^2)
    # For ring pixels, nz on elevated sphere of radius R: nz = sqrt(R^2 - r^2)

    x_n, y_n, z_n = nx.copy(), ny.copy(), nz_abs.copy()
    x_f, y_f, z_f = nx.copy(), ny.copy(), -nz_abs.copy()

    xn, yn, zn = rotate_points(x_n, y_n, z_n, yaw, pitch)
    xf, yf, zf = rotate_points(x_f, y_f, z_f, yaw, pitch)

    lon_n, lat_n = xyz_to_lonlat(xn, yn, zn)
    lon_f, lat_f = xyz_to_lonlat(xf, yf, zf)

    # Limb lon/lat for extrusion ring (z≈0 on unit sphere direction)
    ux = np.where(radial > 1e-6, nx / np.maximum(radial, 1e-6), 0)
    uy = np.where(radial > 1e-6, ny / np.maximum(radial, 1e-6), 0)
    xl, yl, zl = rotate_points(ux, uy, np.zeros_like(ux), yaw, pitch)
    lon_limb, lat_limb = xyz_to_lonlat(xl, yl, zl)

    far_land_gain = p["far_land_gain"]
    far_coast_gain = p["far_coast_gain"]
    near_land_a = p["near_land_a"]
    near_coast_boost = p["near_coast_boost"]
    ocean_tint_a = p["ocean_tint_a"]
    ocean_body_a = p["ocean_body_a"]
    ior_bend = p["ior_bend"]
    far_blur_px = p["far_blur_px"]
    glass_thick = p["glass_thick"]
    land_rgb = p["land_rgb"]
    far_land_rgb = p["far_land_rgb"]
    ocean_rgb = p["ocean_rgb"]
    fresnel_pow = p["fresnel_pow"]
    spec_gain = p["spec_gain"]
    rim_gain = p["rim_gain"]
    through_land = p["through_land"]
    land_fill = p["land_fill"]
    far_path_atten = p["far_path_atten"]
    far_limb_suppress = p["far_limb_suppress"]
    tunnel_clarity = p["tunnel_clarity"]
    shell_rim_boost = p["shell_rim_boost"]
    coast_etch = p["coast_etch"]

    path_len = (2.0 * nz_abs) * mask_unit
    bend = ior_bend * (np.clip(radial, 0, 1) ** 1.4) * (0.4 + 0.6 * glass_thick)
    ang = np.arctan2(ny, nx)
    lon_f_b = lon_f + bend * np.cos(ang) * 0.55
    lat_f_b = np.clip(lat_f + bend * np.sin(ang) * 0.35, -math.pi / 2 + 1e-3, math.pi / 2 - 1e-3)

    if far_blur_px > 0:
        offsets = [
            (0.012, 0.0), (-0.012, 0.0), (0.0, 0.01), (0.0, -0.01),
            (0.018, 0.012), (-0.018, -0.012), (0.014, -0.014), (-0.014, 0.014),
        ]
        n_off = min(far_blur_px * 2, len(offsets))
        tex_f, land_f, coast_f = sample_equirect(earth, land_m, edge_m, lon_f_b, lat_f_b)
        for dlo, dla in offsets[:n_off]:
            scale = 1.0 + bend + 0.35 * (far_blur_px / 4.0)
            t2, l2, c2 = sample_equirect(
                earth, land_m, edge_m, lon_f_b + dlo * scale, lat_f_b + dla * scale
            )
            tex_f = tex_f + t2
            land_f = land_f + l2
            coast_f = coast_f + c2
        denom = 1.0 + n_off
        tex_f = tex_f / denom
        land_f = np.clip(land_f / denom, 0, 1)
        coast_f = np.clip(coast_f / denom, 0, 1)
    else:
        tex_f, land_f, coast_f = sample_equirect(earth, land_m, edge_m, lon_f_b, lat_f_b)

    tex_n, land_n, coast_n = sample_equirect(earth, land_m, edge_m, lon_n, lat_n)

    land_n = land_n * mask_unit
    land_f = land_f * mask_unit
    coast_n = coast_n * mask_unit
    coast_f = coast_f * mask_unit
    ocean_n = (1.0 - land_n) * mask_unit

    L = np.array([0.35, -0.42, 0.84], dtype=np.float32)
    L = L / np.linalg.norm(L)
    N = np.stack([nx, ny, nz_abs], axis=-1)
    ndotl = np.clip((N * L).sum(axis=-1), 0, 1)
    fresnel = np.power(1.0 - np.clip(nz_abs, 0, 1), fresnel_pow) * mask_unit
    limb = np.power(1.0 - np.clip(nz_abs, 0, 1), 1.35) * mask_unit
    thickness_cue = limb * glass_thick

    Rvec = 2 * ndotl[..., None] * N - L
    spec = np.power(np.clip(Rvec[..., 2], 0, 1), 48 + 20 * glass_thick) * mask_unit

    rim_ring = np.exp(
        -((np.clip(radial, 0, 1) - (0.92 + 0.04 * glass_thick)) ** 2) / (0.0018 + 0.001 * glass_thick)
    )
    rim_ring = rim_ring * mask_unit * shell_rim_boost

    stage = np.array(stage_rgb, dtype=np.float32)
    base = np.zeros((n, n, 3), dtype=np.float32)
    base[..., 0] = stage[0]
    base[..., 1] = stage[1]
    base[..., 2] = stage[2]

    transmit = (0.55 + 0.45 * ocean_n * tunnel_clarity) * (
        1.0 - near_land_a * land_n * (1.0 - through_land)
    )
    transmit = transmit * (1.0 - far_limb_suppress * np.clip(radial, 0, 1))
    transmit = np.clip(transmit, 0, 1)

    far_w = land_f * far_land_gain * transmit * far_path_atten
    far_coast_w = coast_f * far_coast_gain * transmit * far_path_atten * (0.85 + 0.15 * ocean_n)

    far_col = far_land_rgb * (0.85 + 0.15 * (1.0 - ndotl)[..., None])
    far_lum = tex_f.mean(axis=-1)
    far_col = far_col * (0.90 + 0.12 * (1.0 - far_lum)[..., None])
    base = base * (1.0 - far_w)[..., None] + far_col * far_w[..., None]
    coast_dark = np.array([0.32, 0.38, 0.48], dtype=np.float32)
    base = base * (1.0 - far_coast_w * coast_etch)[..., None] + coast_dark * (
        far_coast_w * coast_etch
    )[..., None]

    ocean_a = (
        ocean_tint_a + ocean_body_a * (0.35 + 0.65 * path_len / 2.0) + 0.12 * fresnel
    ) * ocean_n
    ocean_col = ocean_rgb * (0.88 + 0.12 * ndotl[..., None])
    caust = (
        np.abs(np.sin(nx * 9 + ny * 6 + nz_abs * 4))
        * np.abs(np.cos(nx * 5 - ny * 8))
        * ocean_n
        * (0.3 + 0.7 * ndotl)
        * (0.04 + 0.06 * glass_thick)
    )
    ocean_col = ocean_col + caust[..., None] * np.array([0.70, 0.88, 1.0], dtype=np.float32)
    base = base * (1.0 - ocean_a)[..., None] + ocean_col * ocean_a[..., None]

    near_a = (
        near_land_a + land_fill * land_n + near_coast_boost * coast_n + 0.08 * thickness_cue
    ) * land_n
    near_a = np.clip(near_a, 0, 0.85)
    near_col = land_rgb * (0.92 + 0.08 * ndotl[..., None])
    near_lum = tex_n.mean(axis=-1)
    near_col = near_col - (coast_n * 0.22)[..., None] * np.array([0.30, 0.26, 0.20])
    near_col = near_col * (0.94 + 0.08 * (1.0 - near_lum)[..., None])
    if land_fill > 0:
        near_col = near_col + (land_fill * 0.12 * land_n)[..., None] * np.array(
            [0.90, 0.94, 0.98]
        )
    base = base * (1.0 - near_a)[..., None] + near_col * near_a[..., None]

    f_ocean = fresnel * ocean_n
    f_land = fresnel * land_n * 0.65
    base = base + (f_ocean * 0.55)[..., None] * np.array([0.45, 0.68, 0.88])
    base = base + (f_land * 0.35)[..., None] * np.array([0.75, 0.82, 0.92])
    chroma = fresnel * 0.06 * glass_thick
    base[..., 0] = base[..., 0] + chroma * 0.08
    base[..., 2] = base[..., 2] + chroma * 0.16

    base = base + (spec_gain * spec)[..., None]
    base = base + (rim_ring * rim_gain * 0.35)[..., None] * np.array([0.95, 0.98, 1.0])
    glass_edge = np.exp(-((np.clip(radial, 0, 1) - 0.985) ** 2) / 0.00035) * mask_unit
    base = base * (1.0 - glass_edge * 0.15 * glass_thick)[..., None]
    base = base + (glass_edge * 0.20 * glass_thick)[..., None] * np.array([0.88, 0.93, 1.0])

    # --- Geo overlays ---
    border_n = sample_scalar(geo["border"], lon_n, lat_n) * mask_unit
    cont_n = sample_scalar(geo["continent_id"], lon_n, lat_n)
    cont_border_n = sample_scalar(geo["cont_border"], lon_n, lat_n) * mask_unit
    cid_n = sample_scalar(geo["country_id"], lon_n, lat_n)

    # S1 / default faint country lines
    if mode in ("S1", "S2", "S3", "S4", "S5"):
        # Whisper thin theme-matched borders (never harsh black)
        line_col = np.array([0.42, 0.50, 0.60], dtype=np.float32)
        line_a = border_n * land_n * (0.22 if mode == "S1" else 0.14)
        if mode == "S2":
            line_a = border_n * land_n * 0.10  # quieter under continent fill
        base = base * (1.0 - line_a)[..., None] + line_col * line_a[..., None]

    # S2 continent grouping soft fill + stronger continent seams
    if mode == "S2":
        tint_a = land_n * 0.34
        tint_col = np.zeros((n, n, 3), dtype=np.float32)
        for cid, col in CONT_TINT.items():
            m = (cont_n == cid) & (land_n > 0.3)
            tint_col[m] = col
        has = (cont_n > 0) & (land_n > 0.3)
        base = np.where(
            has[..., None],
            base * (1.0 - tint_a)[..., None] + tint_col * tint_a[..., None],
            base,
        )
        # continent seams slightly clearer than country lines
        seam_col = np.array([0.34, 0.44, 0.58], dtype=np.float32)
        seam_a = cont_border_n * land_n * 0.48
        base = base * (1.0 - seam_a)[..., None] + seam_col * seam_a[..., None]

    # S3/S4/S5 elevated glowing glass
    elev = np.zeros((n, n), dtype=np.float32)
    glow_t = np.full((n, n), -1, dtype=np.int8)
    bloom = np.zeros((n, n, 3), dtype=np.float32)
    alpha_boost = np.zeros((n, n), dtype=np.float32)

    if mode in ("S3", "S4", "S5") and mock_dict:
        hmap, gmap = build_mock_maps(geo, mock_dict)
        elev_n = sample_scalar(hmap, lon_n, lat_n) * mask_unit
        gt_n = sample_scalar(gmap, lon_n, lat_n)
        # also sample at limb for ring
        elev_limb = sample_scalar(hmap, lon_limb, lat_limb)
        gt_limb = sample_scalar(gmap, lon_limb, lat_limb)

        elev = elev_n
        glow_t = gt_n

        # Crystal island body on near land: thicker glass fill + soft side walls at borders
        island = (elev > 0.05) & (land_n > 0.25) & mask_unit
        thick = elev * island.astype(np.float32)

        # Internal crystal body — pale glass lift
        crystal_lift = thick * 0.55
        crystal_col = np.array([0.88, 0.94, 1.0], dtype=np.float32)
        base = base + (crystal_lift * 0.35)[..., None] * crystal_col * island[..., None]
        # denser fill
        fill_a = thick * 0.28
        base = base * (1.0 - fill_a)[..., None] + (
            crystal_col * (0.75 + 0.25 * ndotl)[..., None]
        ) * fill_a[..., None]

        # Soft side walls via country border * elevation (fresnel-ish)
        wall = border_n * thick * (0.55 + 0.45 * fresnel)
        wall_col = np.array([0.70, 0.82, 0.95], dtype=np.float32)
        base = base * (1.0 - wall * 0.65)[..., None] + wall_col * (wall * 0.65)[..., None]
        # side spill highlight
        base = base + (wall * 0.45)[..., None] * np.array([0.85, 0.95, 1.0])

        # Internal glow emission (inside volume) + fresnel bleed
        glow_colors = [GLOW_A, GLOW_B, GLOW_C]
        for gi, gcol in enumerate(glow_colors):
            gm = island & (glow_t == gi)
            if not gm.any():
                continue
            # core emission stronger toward center of island (away from border) + mid-volume
            core = thick * (1.0 - border_n * 0.7) * (0.55 + 0.45 * nz_abs)
            emit = core * gm.astype(np.float32)
            # fresnel bleed at limb of island / sphere
            bleed = emit * (0.35 + 0.90 * fresnel) * (0.7 + 0.3 * thick)
            base = base + (emit * 0.55)[..., None] * gcol
            base = base + (bleed * 0.70)[..., None] * gcol
            bloom[..., 0] += emit * gcol[0] * 0.85
            bloom[..., 1] += emit * gcol[1] * 0.85
            bloom[..., 2] += emit * gcol[2] * 0.85
            alpha_boost += emit * 0.35

        # Radial extrusion beyond unit disk — sleek crystal island silhouette
        ring = (radial > 1.0) & (radial <= R_ext) & (elev_limb > 0.05)
        if ring.any():
            # local height allowed
            local_R = 1.0 + elev_limb * extrude_scale
            on_cap = ring & (radial <= local_R)
            # side wall of extrusion: near outer edge of local_R
            wall_ring = on_cap & (radial > (local_R - 0.012 - elev_limb * 0.02))
            # roof/cap of elevated shell
            # reconstruct nz on elevated sphere
            nz_e = np.zeros_like(nx)
            nz_e[on_cap] = np.sqrt(np.clip(local_R[on_cap] ** 2 - r2[on_cap], 0, None))
            # glass side + roof
            roof_col = np.array([0.82, 0.90, 0.98], dtype=np.float32)
            side_col = np.array([0.65, 0.78, 0.92], dtype=np.float32)
            # shade by local normal approx
            Nn = np.stack([nx, ny, nz_e], axis=-1)
            nn = np.linalg.norm(Nn, axis=-1, keepdims=True) + 1e-6
            Nn = Nn / nn
            nd = np.clip((Nn * L).sum(axis=-1), 0, 1)
            fr = np.power(1.0 - np.clip(nz_e / (local_R + 1e-6), 0, 1), 1.6)

            roof_a = on_cap.astype(np.float32) * (0.55 + 0.25 * elev_limb)
            base = np.where(
                on_cap[..., None],
                base * (1.0 - roof_a)[..., None]
                + (roof_col * (0.75 + 0.25 * nd)[..., None]) * roof_a[..., None],
                base,
            )
            # glow into extruded volume
            for gi, gcol in enumerate(glow_colors):
                gm = on_cap & (gt_limb == gi)
                if not gm.any():
                    continue
                eg = elev_limb * gm.astype(np.float32)
                base = base + (eg * 0.50 * (0.4 + 0.6 * fr))[..., None] * gcol
                bloom[..., 0] += eg * gcol[0] * 0.9
                bloom[..., 1] += eg * gcol[1] * 0.9
                bloom[..., 2] += eg * gcol[2] * 0.9
                alpha_boost += eg * 0.5

            # crisp soft side rim of crystal island
            side_a = wall_ring.astype(np.float32) * (0.75 + 0.25 * elev_limb)
            base = base * (1.0 - side_a)[..., None] + side_col * side_a[..., None]
            base = base + (side_a * 0.35)[..., None] * np.array([0.9, 0.97, 1.0])
            alpha_boost = np.maximum(alpha_boost, on_cap.astype(np.float32) * 0.75)

            # extend mask for alpha
            mask_unit = mask_unit | on_cap

        # Soft outer bloom (Gaussian via box approx later on PIL) — pre-accumulate
        # also faint far-side elevated? keep far ghost only — no loud far glow
        # (elevation is near-side craft read)

    # Optional S6-lite: no chrome-heavy; skip for main board set

    dist = 1.0 - np.sqrt(np.clip(r2, 0, 2))
    edge_aa = np.clip(dist * (n / 2.8), 0, 1)
    # For extrusion, softer AA at R_ext
    if R_ext > 1.0:
        dist_e = R_ext - radial
        edge_aa = np.maximum(edge_aa, np.clip(dist_e * (n / 2.8), 0, 1) * (radial > 0.95))

    alpha_mat = (
        ocean_n * (0.28 + 0.22 * glass_thick + 0.20 * fresnel + 0.15 * path_len / 2)
        + land_n * (0.40 + 0.35 * near_a + 0.15 * fresnel)
        + rim_ring * 0.45
        + glass_edge * 0.55
        + alpha_boost
    )
    alpha_mat = alpha_mat + land_f * ocean_n * (0.04 + 0.08 * far_land_gain)
    alpha = np.clip(alpha_mat * np.clip(edge_aa, 0, 1), 0, 1)
    # ensure extruded pixels visible
    alpha = np.clip(alpha + alpha_boost * 0.4, 0, 1)

    out = np.zeros((n, n, 4), dtype=np.float32)
    out[..., :3] = np.clip(base, 0, 1)
    out[..., 3] = np.clip(alpha, 0, 1)

    globe = Image.fromarray((np.clip(out, 0, 1) * 255.0).astype(np.uint8), "RGBA")

    # Bloom pass — soft glow respecting sphere (multiply by soft disk)
    if bloom.max() > 0.01:
        bloom_img = Image.fromarray(
            (np.clip(bloom, 0, 1.5) / 1.5 * 255.0).astype(np.uint8), "RGB"
        )
        bloom_img = bloom_img.filter(ImageFilter.GaussianBlur(radius=14))
        bloom_soft = bloom_img.filter(ImageFilter.GaussianBlur(radius=28))
        ba = np.asarray(bloom_img).astype(np.float32) / 255.0
        bb = np.asarray(bloom_soft).astype(np.float32) / 255.0
        # limb-respecting: fade bloom outside mask_ext
        disk = (radial <= (R_ext + 0.04)).astype(np.float32)
        disk = disk * np.clip(1.0 - np.maximum(radial - R_ext, 0) / 0.08, 0, 1)
        garr = np.asarray(globe).astype(np.float32) / 255.0
        add = (ba * 0.55 + bb * 0.85) * disk[..., None]
        garr[..., :3] = np.clip(garr[..., :3] + add * 0.85, 0, 1)
        # slight alpha lift where bloom
        garr[..., 3] = np.clip(garr[..., 3] + add.mean(axis=-1) * 0.25, 0, 1)
        globe = Image.fromarray((np.clip(garr, 0, 1) * 255.0).astype(np.uint8), "RGBA")

    proof = {
        "mode": mode,
        "yaw_deg": yaw_deg,
        "pitch_deg": pitch_deg,
        "elev_px": int((elev > 0.05).sum()) if mode in ("S3", "S4", "S5") else 0,
        "border_mean": float(border_n[mask_unit].mean()) if mask_unit.any() else 0,
        "R_ext": R_ext,
    }
    return globe, proof


def gradient_bg(w, h, kind="cool_glass"):
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    xx = np.linspace(0, 1, w, dtype=np.float32)[None, :]
    hx = np.abs(xx - 0.5) * 2.0
    t = yy
    if kind == "cool_glass":
        r = 248 - t * 8 + (1 - np.abs(t - 0.45)) * 8 - hx * 1
        g = 246 - t * 4 + 6 + hx * 0
        b = 240 + t * 10 + hx * 6
    else:
        r = 254 - t * 10 + (1 - np.abs(t - 0.45)) * 14 - hx * 1
        g = 246 - t * 8 + 8
        b = 230 + t * 12 + hx * 5
    arr = np.stack(
        [np.clip(r, 0, 255), np.clip(g, 0, 255), np.clip(b, 0, 255)], axis=-1
    ).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


def radial_studio(bg, cx, cy, strength=18, radius=900, warm=False):
    w, h = bg.size
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / radius
    v = np.clip(strength * np.clip(1 - d, 0, 1) ** 2, 0, 255)
    if warm:
        overlay = np.stack([v * 1.1, v * 1.0, v * 0.85], axis=-1)
    else:
        overlay = np.stack([v * 0.92, v * 1.0, v * 1.1], axis=-1)
    base = np.asarray(bg).astype(np.float32) + overlay
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB")


def draw_ios_statusbar(draw, w, y0=14):
    fill = (28, 32, 38, 230)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    except Exception:
        font = ImageFont.load_default()
    draw.text((52, y0 + 8), "9:41", fill=fill, font=font)
    island_w, island_h = 126, 36
    ix = (w - island_w) // 2
    iy = y0 + 6
    draw.rounded_rectangle([ix, iy, ix + island_w, iy + island_h], radius=18, fill=(0, 0, 0, 255))
    rx = w - 52
    draw.rounded_rectangle([rx - 44, y0 + 14, rx - 8, y0 + 32], radius=4, outline=fill, width=2)
    draw.rectangle([rx - 8, y0 + 19, rx - 4, y0 + 27], fill=fill)
    draw.rounded_rectangle([rx - 40, y0 + 18, rx - 14, y0 + 28], radius=2, fill=fill)
    draw.ellipse([rx - 72, y0 + 12, rx - 52, y0 + 32], outline=fill, width=2)
    draw.ellipse([rx - 66, y0 + 18, rx - 58, y0 + 26], fill=fill)


def draw_android_statusbar(draw, w, y0=10):
    fill = (28, 32, 38, 230)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)
    except Exception:
        font = ImageFont.load_default()
    draw.text((36, y0 + 10), "9:41", fill=fill, font=font)
    rx = w - 36
    draw.rounded_rectangle([rx - 40, y0 + 14, rx - 6, y0 + 32], radius=3, outline=fill, width=2)
    draw.rectangle([rx - 6, y0 + 18, rx - 2, y0 + 28], fill=fill)
    draw.rounded_rectangle([rx - 36, y0 + 18, rx - 12, y0 + 28], radius=1, fill=fill)
    draw.polygon([(rx - 70, y0 + 28), (rx - 58, y0 + 14), (rx - 46, y0 + 28)], outline=fill)
    for i, hgt in enumerate([10, 14, 18, 22]):
        x0 = rx - 100 + i * 8
        draw.rectangle([x0, y0 + 32 - hgt, x0 + 5, y0 + 32], fill=fill)


def phone_chrome(content: Image.Image, platform: str, caption: str) -> Image.Image:
    pad = 48
    top_cap = 88
    bot = 56
    out_w = content.width + pad * 2
    out_h = content.height + pad * 2 + top_cap + bot
    canvas = Image.new("RGB", (out_w, out_h), (236, 238, 242))
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        font_b = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        font_mock = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    except Exception:
        font = ImageFont.load_default()
        font_b = font
        font_mock = font
    draw.text((pad, 22), "TERRA  ·  Phase UI-2  ·  C3 Soft Hollow + data-on-globe", fill=(120, 128, 140), font=font)
    draw.text((pad, 48), caption, fill=(32, 36, 44), font=font_b)
    # EXAMPLE / MOCK badge
    badge = "EXAMPLE / MOCK DATA — not real demographics"
    bw = draw.textlength(badge, font=font_mock) if hasattr(draw, "textlength") else 320
    bx0, by0 = pad, 72
    draw.rounded_rectangle([bx0 - 4, by0 - 2, bx0 + bw + 10, by0 + 18], radius=4, fill=(255, 236, 200))
    draw.text((bx0 + 4, by0), badge, fill=(140, 80, 20), font=font_mock)

    dx0, dy0 = pad - 8, top_cap + pad - 8
    dx1, dy1 = pad + content.width + 8, top_cap + pad + content.height + 8
    draw.rounded_rectangle([dx0, dy0, dx1, dy1], radius=56, fill=(48, 50, 56))
    sx0, sy0 = pad, top_cap + pad
    canvas.paste(content, (sx0, sy0))
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle(
        [sx0 - 2, sy0 - 2, sx0 + content.width + 2, sy0 + content.height + 2],
        radius=48,
        outline=(180, 184, 192, 200),
        width=3,
    )
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    d2 = ImageDraw.Draw(canvas)
    hx = out_w // 2
    if platform == "ios":
        hy = sy0 + content.height - 18
        d2.rounded_rectangle([hx - 70, hy, hx + 70, hy + 6], radius=3, fill=(40, 44, 52, 90))
    else:
        hy = sy0 + content.height - 16
        d2.rounded_rectangle([hx - 60, hy, hx + 60, hy + 5], radius=2, fill=(40, 44, 52, 70))
    d2.text((pad, out_h - 40), platform.upper(), fill=(110, 118, 130), font=font)
    return canvas


def compose_board(globe, platform, caption, *, globe_r=None, cy_off=0):
    gr = globe_r if globe_r is not None else GLOBE_R
    # slightly larger globe when extrusion present
    cx, cy = CX, CY + cy_off
    bg = gradient_bg(W, H, "cool_glass")
    bg = radial_studio(bg, cx, cy, strength=18, radius=900, warm=False)
    base = bg.convert("RGBA")

    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse(
        [cx - gr * 0.72, cy + gr * 0.78, cx + gr * 0.72, cy + gr * 1.02],
        fill=(40, 50, 70, 50),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(34))
    base = Image.alpha_composite(base, shadow)

    g = globe.resize((gr * 2, gr * 2), Image.Resampling.LANCZOS)
    refl = g.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    refl = ImageEnhance.Brightness(refl).enhance(0.32)
    ra = refl.split()[-1]
    ra = ImageEnhance.Brightness(ra).enhance(0.16)
    fade = Image.new("L", refl.size, 0)
    fd = ImageDraw.Draw(fade)
    for i in range(refl.height):
        a = int(max(0, 85 * (1 - i / (refl.height * 0.5))))
        fd.line([(0, i), (refl.width, i)], fill=a)
    r, gch, b, a = refl.split()
    refl = Image.merge("RGBA", (r, gch, b, ImageChops.multiply(ra, fade)))
    base.paste(refl, (cx - gr, cy + gr - 40), refl)
    base.paste(g, (cx - gr, cy - gr), g)

    ui = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ud = ImageDraw.Draw(ui)
    if platform == "ios":
        draw_ios_statusbar(ud, W)
    else:
        draw_android_statusbar(ud, W)
    base = Image.alpha_composite(base, ui)
    return phone_chrome(base.convert("RGB"), platform, caption)


def closeup_detail(globe, title, crop_frac=(0.35, 0.25, 0.95, 0.75)):
    """Crop elevated/glow limb region from globe plate."""
    size = 1024
    canvas = gradient_bg(size, size, "cool_glass")
    canvas = radial_studio(canvas, size // 2, size // 2, strength=22, radius=560).convert("RGBA")
    g = globe.resize((2200, 2200), Image.Resampling.LANCZOS)
    # offset to show limb + islands
    canvas.paste(g, (size // 2 - 700, size // 2 - 1200), g)
    out = canvas.convert("RGB")
    draw = ImageDraw.Draw(out)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
        font_m = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    except Exception:
        font = ImageFont.load_default()
        font_m = font
    draw.text((28, size - 56), title, fill=(40, 48, 58), font=font)
    draw.rounded_rectangle([28, size - 88, 420, size - 64], radius=4, fill=(255, 236, 200))
    draw.text((36, size - 84), "EXAMPLE / MOCK — craft only", fill=(140, 80, 20), font=font_m)
    return out


STATES = [
    dict(
        key="S0",
        file="S0-globe-only",
        name="S0 Globe only",
        mode="S0",
        mock=None,
        yaw=100.0,
        pitch=-16.0,
        orbit=False,
        label="C3 Soft Hollow control · no borders",
    ),
    dict(
        key="S1",
        file="S1-country-lines",
        name="S1 Country lines",
        mode="S1",
        mock=None,
        yaw=100.0,
        pitch=-16.0,
        orbit=False,
        label="faint theme-matched borders · default",
    ),
    dict(
        key="S2",
        file="S2-continent-grouping",
        name="S2 Continent grouping",
        mode="S2",
        mock=None,
        yaw=100.0,
        pitch=-16.0,
        orbit=False,
        label="Africa · Americas · Europe · Asia · Oceania · Antarctica",
    ),
    dict(
        key="S3",
        file="S3-elevated-glow",
        name="S3 Elevated glow",
        mode="S3",
        mock=MOCK_S3,
        yaw=100.0,
        pitch=-16.0,
        orbit=False,
        label="crystal islands · 2 glow hues · EXAMPLE magnitudes",
    ),
    dict(
        key="S4",
        file="S4-dense-data",
        name="S4 Dense data",
        mode="S4",
        mock=MOCK_S4,
        yaw=100.0,
        pitch=-16.0,
        orbit=False,
        label="more islands · 3 glow hues · EXAMPLE magnitudes",
    ),
    dict(
        key="S5",
        file="S5-orbit-glow",
        name="S5 Orbit glow",
        mode="S5",
        mock=MOCK_S4,  # denser glow for volume proof
        yaw=100.0 + 110.0,  # ~110° orbit of glowing state
        pitch=-12.0,
        orbit=True,
        label="orbit ~110° of S4 · glow-in-volume spill proof",
    ),
]


def main():
    print("Loading Earth…")
    earth, land = load_earth(2700)
    edge = land_edge_from_mask(land)
    print("Loading geo rasters…")
    geo = load_geo()
    print(f"  countries in meta: {len(geo['meta']['countries'])}")

    lime_wrap = 0
    proofs = {}

    for st in STATES:
        print(f"\n=== {st['name']} ===")
        # slightly larger canvas for extrusion modes so islands aren't clipped
        size = 1200 if st["mode"] in ("S3", "S4", "S5") else 1100
        globe, proof = render_globe(
            earth, land, edge, geo,
            yaw_deg=st["yaw"],
            pitch_deg=st["pitch"],
            size=size,
            mode=st["mode"],
            mock_dict=st["mock"],
        )
        proofs[st["key"]] = proof
        plate = PLATES / f"{st['file']}-globe.png"
        globe.save(plate)
        print("  plate", plate.name, "elev_px", proof.get("elev_px"), "R_ext", proof.get("R_ext"))

        gr = 490 if st["mode"] in ("S3", "S4", "S5") else GLOBE_R
        for platform in ("ios", "android"):
            angle = "ORBIT ~110°" if st["orbit"] else "FRONT"
            cap = f"{st['name']}  ·  {angle}  ·  {st['label']}  ·  {platform.upper()}"
            board = compose_board(globe, platform, cap, globe_r=gr)
            out = BOARDS / f"{st['file']}-{platform}.png"
            board.save(out)
            print("  wrote", out.name)

        globe.convert("RGB").resize((512, 512), Image.Resampling.LANCZOS).save(
            PREVIEW / f"{st['file']}.jpg", quality=88
        )

    # Closeups — extrusion + glow limb / elevated island
    print("\nCloseups…")
    # Re-render S3 and S4 at higher res for detail
    for key, fname, title in [
        ("S3", "S3-elevated-island", "S3 — elevated crystal island · internal glow · EXAMPLE"),
        ("S4", "S4-dense-glow-limb", "S4 — dense glow limb · fresnel bleed · EXAMPLE"),
        ("S5", "S5-orbit-volume-spill", "S5 — orbit volume spill / through-glass · EXAMPLE"),
    ]:
        st = next(s for s in STATES if s["key"] == key)
        globe, _ = render_globe(
            earth, land, edge, geo,
            yaw_deg=st["yaw"], pitch_deg=st["pitch"],
            size=1400, mode=st["mode"], mock_dict=st["mock"],
            extrude_scale=0.095,
        )
        cu = closeup_detail(globe, title)
        cu.save(CLOSEUPS / f"{fname}.png")
        print("  closeup", fname)

    (ROOT / "assets" / "proof_meta.json").write_text(
        json.dumps({"proofs": proofs, "lime_wrap": lime_wrap, "base": "C3 Soft Hollow UI-1e"}, indent=2),
        encoding="utf-8",
    )
    print("\nDONE render. lime-wrap=", lime_wrap)
    return proofs


if __name__ == "__main__":
    main()
