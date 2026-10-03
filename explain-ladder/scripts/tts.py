"""Narrate script.json with Kokoro and write the timeline the animation syncs to.

Run with the skill's venv:
  ~/.cache/explain-ladder/venv/bin/python tts.py WORKDIR [--voice af_heart] [--speed 1.0]

WORKDIR/script.json = [{"id": "intro", "text": "What is shown and spoken.", "say": "optional spoken override"}, ...]
  text  - the caption text, also used for cue() timing.
  say   - optional; what the voice reads if it must differ (acronyms: "A S D, S T E one hundred").
Writes WORKDIR/vo/<id>.wav (48 kHz mono), timeline.json and timeline.js (window.TL).
Voices: af_heart (default, warm female), af_bella, am_michael, am_fenrir, bm_george (British male), bf_emma.
"""
import argparse, json, os, shutil, subprocess, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro, EspeakConfig

C = os.environ.get("EXPLAIN_LADDER_HOME", os.path.expanduser("~/.cache/explain-ladder"))
ap = argparse.ArgumentParser()
ap.add_argument("workdir")
ap.add_argument("--voice", default="af_heart")
ap.add_argument("--speed", type=float, default=1.0)
ap.add_argument("--lead", type=float, default=1.2, help="silence before the first line (s)")
ap.add_argument("--gap", type=float, default=0.9, help="pause between segments (s)")
ap.add_argument("--tail", type=float, default=2.2, help="time after the last line for the end card (s)")
a = ap.parse_args()


def espeak():
    # kokoro-onnx's bundled espeak library is broken on macOS, so point it at a system espeak-ng.
    pre = ""
    if shutil.which("brew"):
        pre = subprocess.run(["brew", "--prefix", "espeak-ng"], capture_output=True, text=True).stdout.strip()
    for base in [pre, "/opt/homebrew", "/usr/local", "/usr"]:
        if not base:
            continue
        for lib in ["lib/libespeak-ng.dylib", "lib/libespeak-ng.so.1", "lib/x86_64-linux-gnu/libespeak-ng.so.1", "lib/aarch64-linux-gnu/libespeak-ng.so.1"]:
            p = os.path.join(base, lib)
            if not os.path.exists(p):
                continue
            for data in [os.path.join(base, "share/espeak-ng-data"), "/usr/lib/x86_64-linux-gnu/espeak-ng-data", "/usr/lib/aarch64-linux-gnu/espeak-ng-data"]:
                if os.path.isdir(data):
                    return EspeakConfig(lib_path=p, data_path=data)
    sys.exit("espeak-ng not found: brew install espeak-ng (or apt install espeak-ng)")


k = Kokoro(os.path.join(C, "kokoro-v1.0.onnx"), os.path.join(C, "voices-v1.0.bin"), espeak_config=espeak())
W = a.workdir
os.makedirs(os.path.join(W, "vo"), exist_ok=True)
segs = json.load(open(os.path.join(W, "script.json")))
t = a.lead
for s in segs:
    say = s.get("say") or s["text"].replace("A.I.", "AI")
    audio, sr = k.create(say, voice=a.voice, speed=a.speed, lang="en-us")
    audio = np.asarray(audio, dtype=np.float32)
    nz = np.where(np.abs(audio) > 0.01)[0]
    audio = audio[max(0, nz[0] - int(.03 * sr)): nz[-1] + int(.12 * sr)]
    raw = os.path.join(W, "vo", s["id"] + "_raw.wav")
    out = os.path.join(W, "vo", s["id"] + ".wav")
    sf.write(raw, audio, sr)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-ar", "48000", "-ac", "1", "-sample_fmt", "s16", out], check=True)
    os.remove(raw)
    s["start"] = round(t, 3)
    s["dur"] = round(len(audio) / sr, 3)
    t += s["dur"] + a.gap
    print(f'{s["id"]:<14} start {s["start"]:>7.2f}s  dur {s["dur"]:>6.2f}s')
segs[-1]["end"] = round(t - a.gap + a.tail, 3)
json.dump(segs, open(os.path.join(W, "timeline.json"), "w"), indent=1)
keep = ("id", "text", "label", "start", "dur", "end")
open(os.path.join(W, "timeline.js"), "w").write("window.TL=" + json.dumps([{x: s[x] for x in keep if x in s} for s in segs]) + ";")
print(f"total {segs[-1]['end']:.1f}s  voice {a.voice}")
