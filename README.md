# explain-ladder

A Claude skill that explains anything in the format you pick. It is based on [Andrej Karpathy's idea](https://x.com/karpathy) of an "output ladder": stop reading walls of text from AI, and ask for a better format instead.

| Level | Format | What you get |
|---|---|---|
| 1 | **Clear writing** | Text in [ASD-STE100](https://www.asd-ste100.org/) style. This is the strict, simple English written for airplane repair manuals: short sentences, one idea in each. The default is "80% of the way", so it stays readable. |
| 2 | **Diagram** | Boxes and arrows that show how the parts connect (Mermaid, SVG or HTML). |
| 3 | **Web page** | One HTML file you can click through, with a small interactive element for each idea. |
| 4 | **Explainer video** | An MP4 with animation, captions, a natural-sounding voice and a music bed. It all runs locally and is free. |

The skill always **asks first**:
- which level you want (it suggests one based on the topic);
- who the explanation is for (beginner, basics, or expert).

## Install

```bash
git clone https://github.com/duolahypercho/explain-ladder
cp -R explain-ladder/explain-ladder ~/.claude/skills/
```

The command above makes the skill available in every project. To use it in one project only, copy the folder into that project's `.claude/skills/` folder.

Then ask Claude something like:

> explain how DNS works
>
> break down this paper for me: ./paper.pdf
>
> make an explainer video about how vaccines train the immune system

## Level 4 (video) requirements

Levels 1 to 3 need nothing extra. Level 4 uses:

- **[Kokoro](https://github.com/thewh1teagle/kokoro-onnx)**: an open-source, local text-to-speech model. The model files are about 340 MB.
- **espeak-ng**: pronunciation (`brew install espeak-ng`, or `apt install espeak-ng`).
- **ffmpeg**, **Node.js**, **uv**, and **playwright-core** with Chromium. Chromium renders the canvas animation frame by frame.

The skill runs `scripts/check_deps.sh` and **asks before it downloads anything**. To install everything up front:

```bash
bash ~/.claude/skills/explain-ladder/scripts/check_deps.sh
bash ~/.claude/skills/explain-ladder/scripts/setup.sh   # installs into ~/.cache/explain-ladder
```

`setup.sh` installs packages with Homebrew, so it is written for macOS. On Linux, install `ffmpeg`, `espeak-ng`, `uv` and Node with your package manager first. `setup.sh` then handles the rest.

A ~2 minute video takes about 5 to 6 minutes to render at 1080p / 30 fps. The script also makes a 720p copy of about 25 MB that fits social and chat upload limits.

### How the video pipeline works

```
script.json ──tts.py──▶ narration + timeline.js ──▶ explainer.html (scenes sync to the spoken words)
                                  │                          │
                               mix.py                  render.js (headless Chromium)
                                  ▼                          ▼
                             audio.wav ─────────────▶ explainer.mp4 + explainer_720p.mp4
```

The animation does not guess its timing. It reads the real start of each narration segment and estimates when each phrase is spoken. This lets a visual appear on the exact word that names it (`cue('step1', 'ASD-STE100')`). The full guide is in [`explain-ladder/references/video.md`](explain-ladder/references/video.md).

### Known macOS issue (already handled)

The `espeak` loader bundled with `kokoro-onnx` crashes with this error:

```
Error processing file '/Users/runner/work/espeakng-loader/.../phontab': No such file or directory.
```

`setup.sh` installs Homebrew `espeak-ng` and `phonemizer-fork` instead. `tts.py` then points Kokoro at the system library.

## Layout

```
explain-ladder/
├── SKILL.md                 # the instructions Claude follows
├── references/
│   ├── ste100.md            # working summary of the ASD-STE100 rules + "80%" mode
│   └── video.md             # level 4 step by step
├── scripts/
│   ├── check_deps.sh        # reports what's missing, installs nothing
│   ├── setup.sh             # installs level 4 deps into ~/.cache/explain-ladder
│   ├── tts.py               # Kokoro narration → vo/*.wav + timeline.js
│   ├── mix.py               # voice + ducked music bed + transition sounds → audio.wav
│   └── render.js            # stills contact sheet, or full MP4 render
└── assets/
    └── template.html        # canvas animation engine: cues, captions, transitions, helpers
```

## Credits

- The output ladder idea comes from Andrej Karpathy.
- The voice is [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M), run through [kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx).
- ASD-STE100 is a specification of ASD (the AeroSpace, Security and Defence Industries Association of Europe). `references/ste100.md` is only a short working summary, not the specification.

## License

MIT
