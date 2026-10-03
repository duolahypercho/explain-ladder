#!/usr/bin/env bash
# Installs level 4 dependencies into $EXPLAIN_LADDER_HOME (default ~/.cache/explain-ladder).
# Only run after the user agreed to the downloads listed by check_deps.sh.
set -e
C="${EXPLAIN_LADDER_HOME:-$HOME/.cache/explain-ladder}"; mkdir -p "$C"; cd "$C"
if command -v brew >/dev/null; then
  for p in ffmpeg uv espeak-ng; do brew list "$p" >/dev/null 2>&1 || brew install -q "$p"; done
fi
[ -x venv/bin/python ] || uv venv -q -p 3.11 venv
# kokoro-onnx's bundled espeak loader is broken on macOS; phonemizer-fork + system espeak-ng works.
uv pip install -q -p venv/bin/python kokoro-onnx soundfile numpy scipy
uv pip uninstall -q -p venv/bin/python phonemizer 2>/dev/null || true
uv pip install -q -p venv/bin/python phonemizer-fork
R=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
[ -f kokoro-v1.0.onnx ] || curl -fL -o kokoro-v1.0.onnx "$R/kokoro-v1.0.onnx"
[ -f voices-v1.0.bin ] || curl -fL -o voices-v1.0.bin "$R/voices-v1.0.bin"
[ -f package.json ] || npm init -y >/dev/null
[ -d node_modules/playwright-core ] || npm i -s playwright-core
if [ ! -d "/Applications/Google Chrome.app" ] && ! ls -d "$HOME"/Library/Caches/ms-playwright/chromium-* "$HOME"/.cache/ms-playwright/chromium-* >/dev/null 2>&1; then
  npx -y playwright install chromium
fi
echo "Setup complete: $C"
