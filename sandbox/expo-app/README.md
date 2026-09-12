# TERRA UI-2.5 — Expo WebView shell (Android APK path)

Wraps the WebGL2 sandbox in `react-native-webview`. Not Kotlin/Compose-only. iOS-ready (`ios.bundleIdentifier` set) but **this phase does not ship an iOS binary**.

## Dev (WebView → live sandbox)

```bash
# terminal A
cd /workspace/terra/phase-ui-2-tech/sandbox && python3 -m http.server 8765

# terminal B
cd expo-app && npm install && npx expo start
```

Android emulator loads `http://10.0.2.2:8765`.

## Offline APK

Bundled `assets/www.zip` is unzipped on first launch into cache, then loaded via `file://`.

```bash
npm install
npx eas build --platform android --profile preview
# or, with local Android SDK:
npx expo prebuild --platform android
npx expo run:android --variant release
```

### Blocker note
This box has **no Android SDK / no JAVA_HOME**. Local `expo run:android` cannot produce an APK here. Use EAS (`eas build`) from a machine with Expo credentials, or install Android SDK and re-run.

## MOCK
All magnitudes EXAMPLE / MOCK — not real demographics.
