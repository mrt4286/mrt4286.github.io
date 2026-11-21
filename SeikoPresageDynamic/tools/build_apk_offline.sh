#!/usr/bin/env bash
# Builds the watch face APK WITHOUT Gradle / Android Gradle Plugin.
#
# Used where dl.google.com (Android SDK + Google Maven) is unreachable. It performs the same
# steps AGP does for a resource-only app: manifest merge -> aapt2 compile/link -> zipalign -> sign.
# On a normal dev machine just run `./gradlew assembleDebug` instead.
#
# Needs: aapt2, zipalign, apksigner, keytool (JDK) and an android.jar (any API >= 23 works,
# this app only uses long-standing manifest attributes).
#   Ubuntu/Debian: sudo apt-get install aapt apksigner zipalign android-sdk-platform-23
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/build/offline"
APP_ID="com.mrt4286.seikopresage"
VERSION_CODE=1
VERSION_NAME="1.0"
ANDROID_JAR="${ANDROID_JAR:-/usr/lib/android-sdk/platforms/android-23/android.jar}"
[ -f "$ANDROID_JAR" ] || ANDROID_JAR="$(ls "$ANDROID_HOME"/platforms/android-*/android.jar 2>/dev/null | sort -V | tail -1)"
OUT_APK="$ROOT/SeikoPresageDynamic-debug.apk"

rm -rf "$BUILD" && mkdir -p "$BUILD"

echo "[1/6] regenerate assets + watchface.xml"
python3 "$ROOT/generate_assets.py" >/dev/null
python3 "$ROOT/generate_watchface_xml.py" >/dev/null
python3 "$ROOT/tools/validate_wff.py"

echo "[2/6] manifest (inject package + uses-sdk, as AGP does)"
python3 - "$ROOT/app/src/main/AndroidManifest.xml" "$BUILD/AndroidManifest.xml" "$APP_ID" <<'EOF'
import sys
src, dst, pkg = sys.argv[1:4]
s = open(src, encoding="utf-8").read()
s = s.replace("<manifest ", '<manifest package="%s" ' % pkg, 1)
s = s.replace('<uses-feature', '<uses-sdk android:minSdkVersion="34" android:targetSdkVersion="34" />\n\n    <uses-feature', 1)
open(dst, "w", encoding="utf-8").write(s)
EOF

echo "[3/6] aapt2 compile"
aapt2 compile --dir "$ROOT/app/src/main/res" -o "$BUILD/compiled.zip"

echo "[4/6] aapt2 link"
aapt2 link -o "$BUILD/unsigned.apk" -I "$ANDROID_JAR" \
  --manifest "$BUILD/AndroidManifest.xml" \
  --min-sdk-version 34 --target-sdk-version 34 \
  --version-code "$VERSION_CODE" --version-name "$VERSION_NAME" \
  -R "$BUILD/compiled.zip" --auto-add-overlay

echo "[5/6] zipalign"
zipalign -f -p 4 "$BUILD/unsigned.apk" "$BUILD/aligned.apk"

echo "[6/6] sign (debug key) + verify"
KS="$BUILD/debug.keystore"
keytool -genkeypair -keystore "$KS" -storepass android -keypass android -alias androiddebugkey \
  -keyalg RSA -keysize 2048 -validity 10000 -dname "CN=Android Debug,O=Android,C=US" 2>&1 | grep -v "^Picked\|Warning\|^$" || true
apksigner sign --ks "$KS" --ks-pass pass:android --key-pass pass:android --ks-key-alias androiddebugkey \
  --out "$OUT_APK" "$BUILD/aligned.apk" 2>&1 | grep -v "^Picked" || true
apksigner verify --verbose "$OUT_APK" 2>&1 | grep -v "^Picked" | head -6
rm -f "$OUT_APK.idsig"

echo
ls -l "$OUT_APK"
