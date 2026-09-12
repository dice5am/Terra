# TERRA UI-2.5 sandbox — C3 Soft Hollow WebGL2

Disposable high-fi interactive globe. Ports locked Python `render_globe` (Pale IOR Veil + C3 Soft Hollow). **MOCK only.**

## Run (globe)

```bash
cd /workspace/terra/phase-ui-2-tech/sandbox
python3 -m http.server 8765 --bind 0.0.0.0
```

- http://127.0.0.1:8765/?platform=ios&mode=S1   ← default launch = **S1**
- `?platform=android&mode=S3` etc.
- Modes: **S0 → S1 → S3 → S5** (tiny switcher)

### Gestures
- One-finger drag = orbit (pitch clamp ±35°)
- Light inertia (settles; no endless spin)
- Pinch / wheel zoom (globe stays readable)
- Double-tap eases to home **100° / −16°**
- S5 eases to **210° / −12°** (home + 110°)

## Assets
See `assets/CONVERSION.md`. Country ids **1–176** from locked `geo_rasters.npz`.

## Proof PNGs
`proof/s{0,1,3,5}-{ios,android}.png` + `proof/s5-closeup.png`  
Regenerate: `node scripts/capture_cdp.mjs` (server must be on :8765).

## Expo / Android APK
`expo-app/` — thin React Native WebView shell (not Compose/Kotlin-only). iOS bundle id set; **no iOS binary this phase**.

```bash
cd expo-app && npm install
npx eas build --platform android --profile preview   # produces APK via EAS
# or with local Android SDK: npx expo prebuild && npx expo run:android --variant release
```

**Blocker on this box:** no Android SDK / JAVA_HOME — local APK build not possible here. EAS cloud build is the path.

## CoS locks used
`extrude_scale=0.085` · S3 max India 0.80 → +6.8% · S5 yaw 210 / pitch −12 · home 100 / −16 · C3 dials verbatim · Glow A/B · MOCK fence.
