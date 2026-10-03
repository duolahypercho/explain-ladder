---
name: explain-ladder
description: Explain any topic, document, link, or code at the level of format the user picks, following Karpathy's output ladder - (1) clean ASD-STE100 writing, (2) a diagram, (3) an interactive HTML page, (4) a narrated explainer video. Always asks which level first. Use when someone says "explain", "help me understand", "break this down", "make an explainer", "ELI5", or asks for a diagram, explainer page, or explainer video of something.
---

# Explain Ladder

Most AI answers are a wall of text. This skill turns any explanation into one of four formats. Each format is easier to take in than the one before it, but it also takes longer to make.

| Level | Format | What you get | Time to make |
|---|---|---|---|
| 1 | **Clear writing** | Text in ASD-STE100 style: short sentences, one idea in each | seconds |
| 2 | **Diagram** | Boxes and arrows that show how the parts connect | ~1 min |
| 3 | **Web page** | One HTML file you can click through, with animation | a few min |
| 4 | **Explainer video** | An MP4 with animation, captions, a human-sounding voice and music | ~15-30 min |

Idea credit: Andrej Karpathy's post on LLM output formats.

## Step 1: Ask before you explain

Never pick a level for the user. First, work out the **topic** (what they pasted, linked, or named). Then ask with the AskUserQuestion tool, in one call with two questions:

**Question 1, "Which level?"** (header `Level`). Give four options: the four levels above, each with its one-line "what you get". Recommend a level based on the topic:
- A rule, process, or definition → level 1.
- A system with parts that connect, a flow, or a cycle → level 2.
- Something with numbers, steps a person can try, or that benefits from clicking → level 3.
- Something the user wants to share or teach to other people → level 4.

**Question 2, "Who is it for?"** (header `Audience`). Options: `Total beginner (no jargon)`, `Knows the basics`, `Expert (keep the terms)`. The answer sets the vocabulary at every level. For a beginner, explain each technical word in plain words, or do not use it.

If the user already said the level or the audience ("make a video of...", "explain like I'm 5"), do not ask that question again. Ask only for what is missing.

If the topic is a link or a file, read it before you write any part of the explanation. Do not explain from the title only.

## Step 2: Write the core explanation first (all levels)

Every level starts from the same 4 to 8 **key ideas**, written in order. Write them before you choose visuals or code. A diagram, page, or video of a weak explanation is still weak.

For each key idea, write:
- the idea, as one short sentence;
- one concrete example, number, or picture that makes it real.

Do not add a key idea that does not come from the source or from facts you know are true. If you are not sure of a fact, say so in the output.

## Level 1: Clear writing (ASD-STE100)

Read `references/ste100.md` and apply the rules in it. Then give the output:

1. **One-line summary** at the top.
2. The key ideas as short paragraphs or numbered steps.
3. **Words to know**: only if the audience is a beginner and some terms remain.

Default to the "80% of the way" version: follow the rules, but keep a word or a sentence that reads more naturally when the strict rule makes the text stiff. Use full strict STE only if the user asks for it.

## Level 2: Diagram

1. Pick one diagram type that fits the shape of the ideas: **flow** (steps in order), **cycle** (it loops), **hierarchy** (parts of a whole), **comparison** (two or more side by side), or **map** (many things connected).
2. Use at most 9 boxes. If you need more, group boxes, or make two diagrams.
3. Every arrow gets a short verb label (`sends`, `turns into`, `checks`).
4. Output format:
   - In a chat that renders Mermaid → a Mermaid block.
   - In Claude Code, or when the user wants a file → a single self-contained `.svg` or `.html` file with the diagram, plus a 2-3 line caption under it.
5. Under the diagram, give a short "how to read this" (1-3 sentences): where to start and which way the arrows flow.

## Level 3: Interactive web page

Build **one self-contained HTML file**. Do not use a build step. Load libraries only from a CDN if you need them.

Structure:
1. **Hero**: the topic in one line, plus the one-line summary.
2. One **section** for each key idea. Each section has one interactive or animated element that shows the idea: a slider that changes a value, a step-through button, a hover reveal, a small chart, or an animated diagram. If an element only decorates, cut it.
3. **Recap**: the key ideas as a short list.

Rules: it must work at phone width, work in light and dark mode, and use plain words for the chosen audience. When it is done, open or publish it the way the environment allows (an Artifact, the browser pane, or `open file.html`), and give the user the path.

## Level 4: Narrated explainer video

Read `references/video.md` before you start. It contains the full pipeline that made the first video. In short:

1. **Script.** Write the narration first as `script.json`: one segment per scene, 1-3 sentences each, 90-140 seconds in total. Use simple spoken words. Put the main point in the first segment.
2. **Ask before you install.** Level 4 needs the Kokoro voice model (~340 MB), Homebrew `espeak-ng`, `playwright-core` and `ffmpeg`. Run `scripts/check_deps.sh` first. If anything is missing, tell the user the name and size of each download, and get a yes before you run `scripts/setup.sh`.
3. **Voice.** Run `scripts/tts.py`. It makes one WAV file for each segment and writes `timeline.js` with the real start time of each segment.
4. **Animation.** Copy `assets/template.html` and write one scene function per segment. Use `cue(id, "phrase")` so that each visual appears when its words are spoken.
5. **Check.** Render stills (`node scripts/render.js stills ...`), look at them as a contact sheet, and fix overlaps before the full render.
6. **Render + mix.** Run `scripts/mix.py`, then `node scripts/render.js video`. Make a second copy under 30 MB at 720p for sharing.

Give the user the MP4 path and the length. Tell them which voice you used and how to change it.

## After any level

End with one line that offers the next level up ("Want this as a diagram?"), unless they are already on level 4. Do not repeat the whole explanation in chat when the output is a file. Give the path and a short summary of what is in it.
