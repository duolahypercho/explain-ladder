# Level 4: narrated explainer video, step by step

This pipeline made a 1:44 explainer of Karpathy's output-ladder post. Everything runs locally and is free.

```
script.json ──tts.py──▶ vo/*.wav + timeline.js ──▶ explainer.html (scenes sync to cue())
                                    │                         │
                                 mix.py                 render.js (headless Chromium, frame by frame)
                                    ▼                         ▼
                               audio.wav ───────────▶ explainer.mp4 + explainer_720p.mp4
```

Paths below: `S` = this skill's folder, `C` = `~/.cache/explain-ladder`, `WD` = a new working folder (use the scratchpad when there is one).

## 0. Dependencies (ask first)

```bash
bash "$S/scripts/check_deps.sh"
```

If anything is missing, tell the user what will be downloaded and how big it is (the script prints both), and wait for a yes. Then run:

```bash
bash "$S/scripts/setup.sh"
```

Known trap: the `espeak` library that ships with `kokoro-onnx` crashes on macOS with `Error processing file '/Users/runner/work/espeakng-loader/...phontab'`. `setup.sh` installs Homebrew `espeak-ng` and `phonemizer-fork`, and `tts.py` points Kokoro at them. Do not try to fix the bundled loader.

## 1. Script (`WD/script.json`)

```json
[
 {"id":"intro", "text":"Karpathy shared a simple idea. AI can do a lot of work for us now. So our new job is to understand what it gives back."},
 {"id":"problem", "label":"THE PROBLEM", "text":"Most of the time, AI gives us a wall of text. Long, dense, and hard to read."},
 {"id":"step1", "label":"STEP 01", "text":"Step one. Better writing. Ask it to explain in ASD-STE100.", "say":"Step one. Better writing. Ask it to explain in A S D, S T E one hundred."}
]
```

- One segment = one scene. Use 6 to 10 segments. Each segment has 1 to 3 short spoken sentences.
- `text` is the caption, and it is the text that `cue()` searches. Write it the way it should appear on screen.
- `say` (optional) is what the voice reads instead. Use it for acronyms, numbers, and names the voice gets wrong.
- `label` (optional) is the big word shown in the transition into this scene.
- Write for the ear. Use short sentences, and say the main point first. Do not use parentheses, because a listener cannot hear them.
- Aim for 90-140 seconds. About 150 spoken words is roughly 1 minute.

## 2. Voice

```bash
"$C/venv/bin/python" "$S/scripts/tts.py" "$WD" --voice af_heart
```

This prints the real start time and length of each segment, and writes `timeline.js`. Voices:
- `af_heart` (default, warm female)
- `af_bella`
- `am_michael`
- `am_fenrir`
- `bm_george` (British male)
- `bf_emma`

To change the speed, use `--speed 0.95`. Do not use the macOS `say` voices. They sound robotic next to Kokoro.

Check the hard words before you build visuals. Play `vo/<id>.wav` with `afplay`, or ask the user to listen to one segment.

## 3. Animation (`WD/explainer.html`)

```bash
cp "$S/assets/template.html" "$WD/explainer.html"
```

Edit `CFG` (`topic`, `endTitle`, `credit`). Then write one function in `SCENES` for each script id.

Rules that kept the first video clean:
- **Sync visuals to words**, not to the scene start. Use `const T = cue('step1', 'ASD-STE100');`, then `stamp(c, W/2, 500, -.08, 'ASD-STE100', T, t)`. The visual lands as the word is said.
- **One visual idea for each sentence.** Think of it as a picture of the words: a wall of text, stamped LONG / DENSE; a slider that goes to 100% and then back to 80%; a paragraph that turns into boxes and arrows.
- Inside a scene, change to a new view on a cue: fade the old group out with `eIX(P(t, X-.2, X+.2))`, and bring the new group in with `fadeIn(t, X)`.
- The content zone is y 140-880. Captions use y 900-1020. Keep the caption zone clear.
- The helpers are: `slam` (letters drop in), `stamp`, `box` (spring node), `flowArrow(bez(...))`, `bullets`, `counter`, `person`, `stepTitle`. For anything more, draw it with canvas 2D.
- Every frame is a pure function of `t`. Do not use `Math.random()` (use `hsh(n)` or `rng(seed)`), and do not keep state between frames.

## 4. Check before the full render

```bash
NODE_PATH="$C/node_modules" node "$S/scripts/render.js" "$WD" stills
```

Open `WD/sheet.jpg` and look at it. Fix:
- text that overlaps other text or the captions;
- a scene that is empty while the voice talks;
- a visual that appears after its word.

Re-render the stills only at the times you changed (`... stills 12.5,30`).

## 5. Final render

```bash
"$C/venv/bin/python" "$S/scripts/mix.py" "$WD"            # --music 0.6 for quieter music, --no-beat for pads only
NODE_PATH="$C/node_modules" node "$S/scripts/render.js" "$WD" video
```

At 30 fps, a ~2 min video takes about 5-6 minutes. Run it in the background. The output is:
- `explainer.mp4`: 1080p, about 110 MB;
- `explainer_720p.mp4`: about 25 MB, for X, chat and phone uploads.

Copy both to wherever the user keeps deliverables. Give them the path and the length.
