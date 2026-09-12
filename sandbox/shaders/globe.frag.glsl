#version 300 es
precision highp float;
precision highp sampler2D;

in vec2 v_uv;
out vec4 fragColor;

uniform sampler2D u_earth;
uniform sampler2D u_landCoast;   // R=land G=coast
uniform sampler2D u_geoPack;     // R=cid/255 G=cont B=border A=cont_border (NEAREST for ids)
uniform sampler2D u_mockS3;      // R=height G=glowType(0/1/2/3) NEAREST

uniform vec2 u_res;
uniform float u_yaw;             // radians
uniform float u_pitch;           // radians
uniform float u_zoom;            // 1 = default frame
uniform int u_mode;              // 0=S0 1=S1 3=S3 5=S5
uniform float u_extrudeScale;    // 0.085
uniform float u_maxHeight;       // 0.80 for S3
uniform vec3 u_stage;            // 0.96,0.95,0.93
uniform vec2 u_globeCenter;      // UV-space center (0.5, ~0.518)
uniform float u_globeRadiusPx;   // in CSS px relative to min(res)

// C3 Soft Hollow locks
const float glass_thick = 0.62;
const float ocean_body_a = 0.20;
const float ocean_tint_a = 0.10;
const float rim_gain = 0.92;
const float shell_rim_boost = 1.35;
const float far_land_gain = 0.15;
const float far_coast_gain = 0.22;
const float far_path_atten = 0.65;
const float far_limb_suppress = 0.45;
const float ior_bend = 0.16;
const float fresnel_pow = 2.15;
const float spec_gain = 0.24;
const float near_land_a = 0.30;
const float near_coast_boost = 0.40;
const float land_fill = 0.06;
const float through_land = 0.12;
const float tunnel_clarity = 1.15;
const float coast_etch = 0.42;
const float far_blur_px = 3.0;

const vec3 land_rgb = vec3(0.70, 0.76, 0.82);
const vec3 far_land_rgb = vec3(0.58, 0.66, 0.76);
const vec3 ocean_rgb = vec3(0.54, 0.72, 0.86);
const vec3 GLOW_A = vec3(0.25, 0.85, 0.95);
const vec3 GLOW_B = vec3(1.00, 0.55, 0.28);
const vec3 GLOW_C = vec3(0.72, 0.42, 1.00);
const vec3 Ldir = normalize(vec3(0.35, -0.42, 0.84));

vec3 rotate_ypr(vec3 p, float yaw, float pitch) {
  // Match Python rotate_points: pitch about X, then yaw about Y
  float cp = cos(pitch), sp = sin(pitch);
  float cy = cos(yaw), sy = sin(yaw);
  float y1 = p.y * cp - p.z * sp;
  float z1 = p.y * sp + p.z * cp;
  float x2 = p.x * cy + z1 * sy;
  float y2 = y1;
  float z2 = -p.x * sy + z1 * cy;
  return vec3(x2, y2, z2);
}

vec2 xyz_to_uv(vec3 p) {
  float lat = asin(clamp(p.y, -1.0, 1.0));
  float lon = atan(p.x, p.z);
  float u = lon / (2.0 * 3.14159265) + 0.5;
  float v = 0.5 - (lat / 3.14159265);
  return vec2(fract(u), clamp(v, 0.0, 1.0));
}

vec2 xyz_to_lonlat(vec3 p) {
  float lat = asin(clamp(p.y, -1.0, 1.0));
  float lon = atan(p.x, p.z);
  return vec2(lon, lat);
}

vec2 lonlat_to_uv(vec2 lonlat) {
  float u = lonlat.x / (2.0 * 3.14159265) + 0.5;
  float v = 0.5 - (lonlat.y / 3.14159265);
  return vec2(fract(u), clamp(v, 0.0, 1.0));
}

vec4 sampleEarth(vec2 uv) { return texture(u_earth, uv); }
vec2 sampleLandCoast(vec2 uv) {
  vec4 t = texture(u_landCoast, uv);
  return vec2(t.r, t.g);
}
float sampleBorder(vec2 uv) {
  // geo_pack B channel — use dedicated linear-friendly sample from geoPack
  return texture(u_geoPack, uv).b;
}
float sampleCid(vec2 uv) {
  // nearest-ish: texels are exact ids/255
  return texture(u_geoPack, uv).r * 255.0;
}
vec2 sampleMock(vec2 uv) {
  vec4 t = texture(u_mockS3, uv);
  return vec2(t.r, t.g * 255.0); // height, glowType (0 none, 1 A, 2 B)
}

void main() {
  vec2 frag = v_uv * u_res;
  float minSide = min(u_res.x, u_res.y);
  float Rpx = u_globeRadiusPx * u_zoom;
  vec2 center = u_globeCenter * u_res;
  // Screen → orthographic nx,ny in [-1,1] over globe disk
  vec2 d = (frag - center) / Rpx;
  float nx = d.x;
  float ny = -d.y; // flip Y to match Python (+up)
  float r2 = nx * nx + ny * ny;
  float radial = sqrt(r2);

  bool elevMode = (u_mode == 3 || u_mode == 5);
  float R_ext = elevMode ? (1.0 + u_maxHeight * u_extrudeScale) : 1.0;
  float maskUnit = step(r2, 1.0);
  float maskExt = step(r2, R_ext * R_ext);

  // Outside extended disk → stage with soft floor reflection cue only
  if (maskExt < 0.5 && radial > R_ext + 0.12) {
    // subtle ground shadow / reflection region below globe
    float below = smoothstep(0.0, 1.2, (frag.y - center.y) / Rpx);
    float shadow = exp(-pow((nx) / 0.85, 2.0)) * exp(-pow((ny + 1.15) / 0.35, 2.0)) * 0.12;
    vec3 col = u_stage - vec3(0.04, 0.035, 0.03) * shadow;
    fragColor = vec4(col, 1.0);
    return;
  }

  float nz_abs = (maskUnit > 0.5) ? sqrt(max(1.0 - r2, 0.0)) : 0.0;

  vec3 pn = rotate_ypr(vec3(nx, ny, nz_abs), u_yaw, u_pitch);
  vec3 pf = rotate_ypr(vec3(nx, ny, -nz_abs), u_yaw, u_pitch);

  vec2 lonlat_n = xyz_to_lonlat(pn);
  vec2 lonlat_f = xyz_to_lonlat(pf);

  // Limb lon/lat for extrusion ring
  float invR = 1.0 / max(radial, 1e-6);
  vec3 plimb = rotate_ypr(vec3(nx * invR, ny * invR, 0.0), u_yaw, u_pitch);
  vec2 lonlat_limb = xyz_to_lonlat(plimb);

  float path_len = 2.0 * nz_abs * maskUnit;
  float bend = ior_bend * pow(clamp(radial, 0.0, 1.0), 1.4) * (0.4 + 0.6 * glass_thick);
  float ang = atan(ny, nx);
  vec2 lonlat_fb = lonlat_f;
  lonlat_fb.x += bend * cos(ang) * 0.55;
  lonlat_fb.y = clamp(lonlat_fb.y + bend * sin(ang) * 0.35, -1.5707 + 1e-3, 1.5707 - 1e-3);

  // Far sample with multi-tap blur (far_blur_px=3 → 6 offsets)
  vec2 offs[8];
  offs[0] = vec2(0.012, 0.0); offs[1] = vec2(-0.012, 0.0);
  offs[2] = vec2(0.0, 0.01); offs[3] = vec2(0.0, -0.01);
  offs[4] = vec2(0.018, 0.012); offs[5] = vec2(-0.018, -0.012);
  offs[6] = vec2(0.014, -0.014); offs[7] = vec2(-0.014, 0.014);
  int n_off = 6;
  float scale = 1.0 + bend + 0.35 * (far_blur_px / 4.0);

  vec3 tex_f = sampleEarth(lonlat_to_uv(lonlat_fb)).rgb;
  vec2 lc_f = sampleLandCoast(lonlat_to_uv(lonlat_fb));
  float land_f = lc_f.x;
  float coast_f = lc_f.y;
  for (int i = 0; i < 6; i++) {
    vec2 ll = lonlat_fb + offs[i] * scale;
    vec2 uv = lonlat_to_uv(ll);
    tex_f += sampleEarth(uv).rgb;
    vec2 lc = sampleLandCoast(uv);
    land_f += lc.x;
    coast_f += lc.y;
  }
  float denom = 1.0 + float(n_off);
  tex_f /= denom;
  land_f = clamp(land_f / denom, 0.0, 1.0);
  coast_f = clamp(coast_f / denom, 0.0, 1.0);

  vec2 uv_n = lonlat_to_uv(lonlat_n);
  vec3 tex_n = sampleEarth(uv_n).rgb;
  vec2 lc_n = sampleLandCoast(uv_n);
  float land_n = lc_n.x * maskUnit;
  float coast_n = lc_n.y * maskUnit;
  land_f *= maskUnit;
  coast_f *= maskUnit;
  float ocean_n = (1.0 - land_n) * maskUnit;

  vec3 N = vec3(nx, ny, nz_abs);
  float ndotl = clamp(dot(N, Ldir), 0.0, 1.0);
  float fresnel = pow(1.0 - clamp(nz_abs, 0.0, 1.0), fresnel_pow) * maskUnit;
  float limb = pow(1.0 - clamp(nz_abs, 0.0, 1.0), 1.35) * maskUnit;
  float thickness_cue = limb * glass_thick;

  vec3 Rvec = 2.0 * ndotl * N - Ldir;
  float spec = pow(clamp(Rvec.z, 0.0, 1.0), 48.0 + 20.0 * glass_thick) * maskUnit;

  float rim_ring = exp(-pow(clamp(radial, 0.0, 1.0) - (0.92 + 0.04 * glass_thick), 2.0)
                       / (0.0018 + 0.001 * glass_thick));
  rim_ring *= maskUnit * shell_rim_boost;

  vec3 base = u_stage;

  float transmit = (0.55 + 0.45 * ocean_n * tunnel_clarity)
                 * (1.0 - near_land_a * land_n * (1.0 - through_land));
  transmit *= (1.0 - far_limb_suppress * clamp(radial, 0.0, 1.0));
  transmit = clamp(transmit, 0.0, 1.0);

  float far_w = land_f * far_land_gain * transmit * far_path_atten;
  float far_coast_w = coast_f * far_coast_gain * transmit * far_path_atten * (0.85 + 0.15 * ocean_n);
  vec3 far_col = far_land_rgb * (0.85 + 0.15 * (1.0 - ndotl));
  float far_lum = (tex_f.r + tex_f.g + tex_f.b) / 3.0;
  far_col *= (0.90 + 0.12 * (1.0 - far_lum));
  base = mix(base, far_col, far_w);
  vec3 coast_dark = vec3(0.32, 0.38, 0.48);
  base = mix(base, coast_dark, far_coast_w * coast_etch);

  float ocean_a = (ocean_tint_a + ocean_body_a * (0.35 + 0.65 * path_len / 2.0) + 0.12 * fresnel) * ocean_n;
  vec3 ocean_col = ocean_rgb * (0.88 + 0.12 * ndotl);
  float caust = abs(sin(nx * 9.0 + ny * 6.0 + nz_abs * 4.0))
              * abs(cos(nx * 5.0 - ny * 8.0))
              * ocean_n * (0.3 + 0.7 * ndotl) * (0.04 + 0.06 * glass_thick);
  ocean_col += caust * vec3(0.70, 0.88, 1.0);
  base = mix(base, ocean_col, ocean_a);

  float near_a = (near_land_a + land_fill * land_n + near_coast_boost * coast_n + 0.08 * thickness_cue) * land_n;
  near_a = clamp(near_a, 0.0, 0.85);
  vec3 near_col = land_rgb * (0.92 + 0.08 * ndotl);
  float near_lum = (tex_n.r + tex_n.g + tex_n.b) / 3.0;
  near_col -= coast_n * 0.22 * vec3(0.30, 0.26, 0.20);
  near_col *= (0.94 + 0.08 * (1.0 - near_lum));
  near_col += (land_fill * 0.12 * land_n) * vec3(0.90, 0.94, 0.98);
  base = mix(base, near_col, near_a);

  float f_ocean = fresnel * ocean_n;
  float f_land = fresnel * land_n * 0.65;
  base += f_ocean * 0.55 * vec3(0.45, 0.68, 0.88);
  base += f_land * 0.35 * vec3(0.75, 0.82, 0.92);
  float chroma = fresnel * 0.06 * glass_thick;
  base.r += chroma * 0.08;
  base.b += chroma * 0.16;

  base += spec_gain * spec;
  base += rim_ring * rim_gain * 0.35 * vec3(0.95, 0.98, 1.0);
  float glass_edge = exp(-pow(clamp(radial, 0.0, 1.0) - 0.985, 2.0) / 0.00035) * maskUnit;
  base = base * (1.0 - glass_edge * 0.15 * glass_thick)
       + (glass_edge * 0.20 * glass_thick) * vec3(0.88, 0.93, 1.0);

  // --- Geo overlays ---
  float border_n = sampleBorder(uv_n) * maskUnit;

  // S1 / S3 / S5 borders
  if (u_mode == 1 || u_mode == 3 || u_mode == 5) {
    vec3 line_col = vec3(0.42, 0.50, 0.60);
    float line_mul = (u_mode == 1) ? 0.22 : 0.14;
    float line_a = border_n * land_n * line_mul;
    base = mix(base, line_col, line_a);
  }

  vec3 bloomAcc = vec3(0.0);
  float alpha_boost = 0.0;
  float elev = 0.0;

  if (elevMode) {
    vec2 mock_n = sampleMock(uv_n);
    elev = mock_n.x * maskUnit;
    float gt = mock_n.y; // 0 none, 1 A, 2 B

    vec2 mock_limb = sampleMock(lonlat_to_uv(lonlat_limb));
    float elev_limb = mock_limb.x;
    float gt_limb = mock_limb.y;

    float island = step(0.05, elev) * step(0.25, land_n) * maskUnit;
    float thick = elev * island;

    // Crystal body
    float crystal_lift = thick * 0.55;
    vec3 crystal_col = vec3(0.88, 0.94, 1.0);
    base += crystal_lift * 0.35 * crystal_col * island;
    float fill_a = thick * 0.28;
    base = mix(base, crystal_col * (0.75 + 0.25 * ndotl), fill_a);

    float wall = border_n * thick * (0.55 + 0.45 * fresnel);
    vec3 wall_col = vec3(0.70, 0.82, 0.95);
    base = mix(base, wall_col, wall * 0.65);
    base += wall * 0.45 * vec3(0.85, 0.95, 1.0);

    // Internal glow emission
    for (int gi = 1; gi <= 2; gi++) {
      float gm = island * (abs(gt - float(gi)) < 0.5 ? 1.0 : 0.0);
      if (gm < 0.01) continue;
      vec3 gcol = (gi == 1) ? GLOW_A : GLOW_B;
      float core = thick * (1.0 - border_n * 0.7) * (0.55 + 0.45 * nz_abs);
      float emit = core * gm;
      float bleed = emit * (0.35 + 0.90 * fresnel) * (0.7 + 0.3 * thick);
      base += emit * 0.55 * gcol;
      base += bleed * 0.70 * gcol;
      bloomAcc += emit * gcol * 0.85;
      alpha_boost += emit * 0.35;
    }

    // Radial extrusion beyond unit disk
    float ring = step(1.0, radial) * step(radial, R_ext) * step(0.05, elev_limb);
    if (ring > 0.5) {
      float local_R = 1.0 + elev_limb * u_extrudeScale;
      float on_cap = ring * step(radial, local_R);
      float wall_ring = on_cap * step(local_R - 0.012 - elev_limb * 0.02, radial);
      float nz_e = (on_cap > 0.5) ? sqrt(max(local_R * local_R - r2, 0.0)) : 0.0;
      vec3 Nn = normalize(vec3(nx, ny, nz_e) + 1e-6);
      float nd = clamp(dot(Nn, Ldir), 0.0, 1.0);
      float fr = pow(1.0 - clamp(nz_e / (local_R + 1e-6), 0.0, 1.0), 1.6);

      vec3 roof_col = vec3(0.82, 0.90, 0.98);
      vec3 side_col = vec3(0.65, 0.78, 0.92);
      float roof_a = on_cap * (0.55 + 0.25 * elev_limb);
      base = mix(base, roof_col * (0.75 + 0.25 * nd), roof_a);

      for (int gi = 1; gi <= 2; gi++) {
        float gm = on_cap * (abs(gt_limb - float(gi)) < 0.5 ? 1.0 : 0.0);
        vec3 gcol = (gi == 1) ? GLOW_A : GLOW_B;
        float eg = elev_limb * gm;
        base += eg * 0.50 * (0.4 + 0.6 * fr) * gcol;
        bloomAcc += eg * gcol * 0.9;
        alpha_boost += eg * 0.5;
      }

      float side_a = wall_ring * (0.75 + 0.25 * elev_limb);
      base = mix(base, side_col, side_a);
      base += side_a * 0.35 * vec3(0.9, 0.97, 1.0);
      alpha_boost = max(alpha_boost, on_cap * 0.75);
      maskUnit = max(maskUnit, on_cap);
    }

    // In-shader multi-tap bloom (approx Gaussian 14 then 28, limb-masked)
    // Screen-space offset in globe radii; scaled for ~14/28 px at R≈470
    float pxToR = 1.0 / max(Rpx, 1.0);
    vec3 bloomTap = vec3(0.0);
    // Use accumulated bloomAcc as center; sample neighbors by re-using a cheap glow probe
    // Approximate: blur the current bloomAcc contribution with ring samples of mock glow
    vec2 dirs[8];
    dirs[0]=vec2(1,0); dirs[1]=vec2(-1,0); dirs[2]=vec2(0,1); dirs[3]=vec2(0,-1);
    dirs[4]=vec2(0.707,0.707); dirs[5]=vec2(-0.707,0.707);
    dirs[6]=vec2(0.707,-0.707); dirs[7]=vec2(-0.707,-0.707);
    float r14 = 14.0 * pxToR;
    float r28 = 28.0 * pxToR;
    vec3 tight = bloomAcc;
    vec3 soft = bloomAcc;
    for (int i = 0; i < 8; i++) {
      // probe nearby screen points for island glow (unit disk only)
      for (int k = 0; k < 2; k++) {
        float rad = (k == 0) ? r14 : r28;
        vec2 off = dirs[i] * rad;
        float nx2 = nx + off.x;
        float ny2 = ny + off.y;
        float r22 = nx2*nx2 + ny2*ny2;
        if (r22 > 1.0) continue;
        float nz2 = sqrt(max(1.0 - r22, 0.0));
        vec3 p2 = rotate_ypr(vec3(nx2, ny2, nz2), u_yaw, u_pitch);
        vec2 uv2 = lonlat_to_uv(xyz_to_lonlat(p2));
        vec2 m2 = sampleMock(uv2);
        vec2 lc2 = sampleLandCoast(uv2);
        float isl2 = step(0.05, m2.x) * step(0.25, lc2.x);
        if (isl2 < 0.5) continue;
        float thick2 = m2.x * isl2;
        float core2 = thick2 * (0.55 + 0.45 * nz2);
        vec3 gcol2 = (m2.y > 1.5) ? GLOW_B : GLOW_A;
        if (m2.y < 0.5) continue;
        vec3 em2 = core2 * gcol2 * 0.85;
        if (k == 0) tight += em2 * 0.12;
        else soft += em2 * 0.10;
      }
    }
    float disk = step(radial, R_ext + 0.04);
    disk *= clamp(1.0 - max(radial - R_ext, 0.0) / 0.08, 0.0, 1.0);
    vec3 addBloom = (tight * 0.55 + soft * 0.85) * disk * 0.85;
    base += addBloom;
    alpha_boost += (addBloom.r + addBloom.g + addBloom.b) / 3.0 * 0.25;
  }

  // Alpha / AA
  float dist = 1.0 - sqrt(clamp(r2, 0.0, 2.0));
  float edge_aa = clamp(dist * (Rpx / 2.8), 0.0, 1.0);
  if (R_ext > 1.0) {
    float dist_e = R_ext - radial;
    edge_aa = max(edge_aa, clamp(dist_e * (Rpx / 2.8), 0.0, 1.0) * step(0.95, radial));
  }

  float alpha_mat =
      ocean_n * (0.28 + 0.22 * glass_thick + 0.20 * fresnel + 0.15 * path_len / 2.0)
    + land_n * (0.40 + 0.35 * near_a + 0.15 * fresnel)
    + rim_ring * 0.45
    + glass_edge * 0.55
    + alpha_boost;
  alpha_mat += land_f * ocean_n * (0.04 + 0.08 * far_land_gain);
  float alpha = clamp(alpha_mat * clamp(edge_aa, 0.0, 1.0), 0.0, 1.0);
  alpha = clamp(alpha + alpha_boost * 0.4, 0.0, 1.0);

  // Soft shadow under globe (outside disk)
  if (maskExt < 0.5) {
    float shadow = exp(-pow(nx / 0.9, 2.0)) * exp(-pow((ny + 1.05) / 0.28, 2.0)) * 0.14;
    // faint reflection strip
    float reflY = -ny;
    float reflBand = smoothstep(1.0, 1.02, radial) * exp(-pow((radial - 1.08) / 0.35, 2.0));
    vec3 col = u_stage - vec3(0.05, 0.04, 0.035) * shadow;
    fragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
    return;
  }

  // Composite over stage with alpha (Python returns RGBA globe composited later)
  vec3 outc = mix(u_stage, clamp(base, 0.0, 1.0), clamp(alpha, 0.0, 1.0));
  // Extra: when fully inside, still keep some stage peek via alpha
  // Soft floor reflection of globe (cheap vertical stretch cue)
  if (ny < -0.15 && maskUnit > 0.5) {
    // no-op inside
  }

  // Outside unit but inside R_ext already handled in elev; fill stage elsewhere
  if (maskUnit < 0.5 && !(elevMode && radial <= R_ext)) {
    float shadow = exp(-pow(nx / 0.9, 2.0)) * exp(-pow((ny + 1.05) / 0.28, 2.0)) * 0.14;
    outc = u_stage - vec3(0.05, 0.04, 0.035) * shadow;
  }

  fragColor = vec4(clamp(outc, 0.0, 1.0), 1.0);
}
