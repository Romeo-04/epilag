#!/bin/sh
cd "$(dirname "$0")"
C="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
"$C" --headless=new --disable-gpu --hide-scrollbars --allow-file-access-from-files --virtual-time-budget=8000 \
  --force-device-scale-factor=1.6 --window-size=1900,2688 --screenshot="$PWD/poster_pixel.png" "file://$PWD/poster_pixel.html" 2>/dev/null
"$C" --headless=new --disable-gpu --allow-file-access-from-files --virtual-time-budget=8000 --no-pdf-header-footer \
  --print-to-pdf="$PWD/poster_pixel.pdf" "file://$PWD/poster_pixel.html" 2>/dev/null
