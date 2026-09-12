import { useEffect, useState } from 'react';
import { ActivityIndicator, Platform, SafeAreaView, StatusBar, StyleSheet, Text, View } from 'react-native';
import { WebView } from 'react-native-webview';
import * as FileSystem from 'expo-file-system';
import { Asset } from 'expo-asset';
import { unzipSync } from 'fflate';

/**
 * TERRA UI-2.5 — thin Expo WebView over WebGL2 sandbox (C3 Soft Hollow).
 * Unzips assets/www.zip into cache; file:// load. Dev prefers :8765.
 * Android APK via EAS preview profile. iOS-ready ids; no iOS binary this phase.
 */
export default function App() {
  const [uri, setUri] = useState(null);
  const [err, setErr] = useState(null);
  const platform = Platform.OS === 'ios' ? 'ios' : 'android';

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const metro = Platform.OS === 'android' ? 'http://10.0.2.2:8765' : 'http://127.0.0.1:8765';
        try {
          const ctrl = new AbortController();
          const t = setTimeout(() => ctrl.abort(), 500);
          const r = await fetch(metro + '/', { signal: ctrl.signal });
          clearTimeout(t);
          if (r.ok) {
            if (alive) setUri(`${metro}/?platform=${platform}&mode=S1`);
            return;
          }
        } catch (_) {}

        const root = FileSystem.cacheDirectory + 'terra-ui25-www/';
        const marker = root + '.ready-v1';
        const info = await FileSystem.getInfoAsync(marker);
        if (!info.exists) {
          await FileSystem.deleteAsync(root, { idempotent: true });
          await FileSystem.makeDirectoryAsync(root, { intermediates: true });
          const asset = Asset.fromModule(require('./assets/www.zip'));
          await asset.downloadAsync();
          const b64 = await FileSystem.readAsStringAsync(asset.localUri, {
            encoding: FileSystem.EncodingType.Base64,
          });
          const binary = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
          const files = unzipSync(binary);
          for (const [name, data] of Object.entries(files)) {
            if (name.endsWith('/')) continue;
            const target = root + name;
            const dir = target.slice(0, target.lastIndexOf('/'));
            await FileSystem.makeDirectoryAsync(dir, { intermediates: true });
            // write as base64
            let s = '';
            const chunk = 0x8000;
            for (let i = 0; i < data.length; i += chunk) {
              s += String.fromCharCode.apply(null, data.subarray(i, i + chunk));
            }
            await FileSystem.writeAsStringAsync(target, btoa(s), {
              encoding: FileSystem.EncodingType.Base64,
            });
          }
          await FileSystem.writeAsStringAsync(marker, '1');
        }
        if (alive) setUri(`${root}index.html?platform=${platform}&mode=S1`);
      } catch (e) {
        if (alive) setErr(String(e && e.message ? e.message : e));
      }
    })();
    return () => { alive = false; };
  }, [platform]);

  if (err) {
    return (
      <View style={styles.center}>
        <Text style={styles.err}>Shell error: {err}</Text>
        <Text style={styles.hint}>Dev: `python3 -m http.server 8765` in sandbox/, then reload.</Text>
      </View>
    );
  }
  if (!uri) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color="#333" />
        <Text style={styles.hint}>TERRA · C3 Soft Hollow</Text>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.root}>
      <StatusBar barStyle="dark-content" backgroundColor="#f5f2ed" />
      <WebView
        source={{ uri }}
        style={styles.web}
        originWhitelist={['*']}
        allowFileAccess
        allowFileAccessFromFileURLs
        allowUniversalAccessFromFileURLs
        mixedContentMode="always"
        javaScriptEnabled
        domStorageEnabled
        androidLayerType="hardware"
        setSupportMultipleWindows={false}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#f5f2ed' },
  web: { flex: 1, backgroundColor: '#f5f2ed' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: '#f5f2ed', padding: 24 },
  err: { color: '#8a2b0a', textAlign: 'center' },
  hint: { color: '#667', marginTop: 12, textAlign: 'center', fontSize: 13 },
});
