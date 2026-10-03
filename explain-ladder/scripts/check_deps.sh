#!/usr/bin/env bash
# Reports what level 4 (video) needs and what is missing. Installs nothing.
C="${EXPLAIN_LADDER_HOME:-$HOME/.cache/explain-ladder}"
ok(){ printf "  ok       %s\n" "$1"; }; miss(){ printf "  MISSING  %s  (%s)\n" "$1" "$2"; MISSING=1; }
echo "explain-ladder level 4 dependencies (cache: $C)"
command -v ffmpeg >/dev/null && ok ffmpeg || miss ffmpeg "brew install ffmpeg, ~50 MB"
command -v node >/dev/null && ok node || miss node "https://nodejs.org or brew install node"
command -v uv >/dev/null && ok uv || miss uv "brew install uv, ~30 MB"
ESPEAK_LIB=$( { brew --prefix espeak-ng 2>/dev/null || echo /usr; } )/lib
ls "$ESPEAK_LIB"/libespeak-ng.* >/dev/null 2>&1 && ok espeak-ng || miss espeak-ng "brew install espeak-ng (or apt install espeak-ng), ~26 MB"
[ -x "$C/venv/bin/python" ] && "$C/venv/bin/python" -c "import kokoro_onnx" 2>/dev/null && ok "kokoro-onnx venv" || miss "kokoro-onnx venv" "uv venv + pip kokoro-onnx soundfile phonemizer-fork, ~150 MB"
[ -f "$C/kokoro-v1.0.onnx" ] && [ -f "$C/voices-v1.0.bin" ] && ok "Kokoro model files" || miss "Kokoro model files" "github.com/thewh1teagle/kokoro-onnx releases, ~340 MB"
[ -d "$C/node_modules/playwright-core" ] && ok playwright-core || miss playwright-core "npm package, ~10 MB"
B=$(ls -d "$HOME"/Library/Caches/ms-playwright/chromium-* "$HOME"/.cache/ms-playwright/chromium-* 2>/dev/null | head -1)
[ -n "$B" ] || [ -d "/Applications/Google Chrome.app" ] && ok "Chromium/Chrome" || miss "Chromium" "npx playwright install chromium, ~150 MB"
[ -z "$MISSING" ] && echo "All set." || { echo; echo "Ask the user before running scripts/setup.sh."; exit 1; }
