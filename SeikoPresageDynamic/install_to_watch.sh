#!/usr/bin/env bash
# Installs the watch face on a Galaxy Watch 7 over Wi-Fi (Wireless debugging).
#
#   ./install_to_watch.sh                      -> asks for everything
#   ./install_to_watch.sh PAIR_IP:PORT CODE CONNECT_IP:PORT
#
# On the watch: Settings > Developer options > ADB debugging ON, Wireless debugging ON,
# then "Pair new device" shows PAIR_IP:PORT + 6-digit CODE; the main Wireless debugging
# screen shows CONNECT_IP:PORT (a different port!).
set -euo pipefail
cd "$(dirname "$0")"

APK="$(ls SeikoPresageDynamic-debug.apk dist/SeikoPresageDynamic-debug.apk 2>/dev/null | head -1 || true)"
[ -n "$APK" ] || { echo "APK not found next to this script"; exit 1; }
command -v adb >/dev/null || { echo "adb not found. Install Android platform-tools: https://developer.android.com/tools/releases/platform-tools"; exit 1; }

PAIR="${1:-}"; CODE="${2:-}"; CONN="${3:-}"
if [ -z "$PAIR" ]; then
  read -rp "Pairing address shown on watch (IP:PORT, empty = already paired): " PAIR
  [ -z "$PAIR" ] || read -rp "6-digit pairing code: " CODE
fi
[ -z "$CONN" ] && read -rp "Connect address shown on watch main screen (IP:PORT): " CONN

if [ -n "$PAIR" ]; then
  echo ">> adb pair $PAIR"
  adb pair "$PAIR" "$CODE"
fi
echo ">> adb connect $CONN"
adb connect "$CONN"
echo ">> installing $APK"
adb -s "$CONN" install -r "$APK"
echo
echo "Done. On the watch: long-press the current watch face > swipe to the end > (+) Add watch face > 'Seiko Presage Dynamic'."
echo "Optional (battery): adb disconnect $CONN  and switch Wireless debugging OFF on the watch."
