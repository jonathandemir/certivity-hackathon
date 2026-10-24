#!/usr/bin/env bash
# Rendert eine Folie (HTML, 1920x1080) als PNG in 3840x2160 wie die übrigen Folien: docs/pitch/render-slide.sh <folie.html>
set -eu
html=$(cd "$(dirname "$1")" && pwd)/$(basename "$1"); png="${html%.html}.png"
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --hide-scrollbars \
  --window-size=1920,1080 --force-device-scale-factor=2 --virtual-time-budget=4000 \
  --screenshot="$png" "file://$html" >/dev/null 2>&1
echo "$png"
