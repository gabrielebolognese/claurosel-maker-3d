---
name: carousel-maker
description: Design and render a step-by-step Instagram, LinkedIn or X carousel in a clean 2.5D isometric look (white canvas, black type, 3D blocks, floating cards, round 3D logo coins), as 1080x1440 PNG slides plus a sheet with every slide. Use when the user says "make a carousel", "carousel about", "slides for Instagram", "swipe post", "turn this into a carousel", "explain this process in slides", or wants a workflow, a tool stack, a guide or a list shown as a carousel with call-to-action slides.
---

# carousel-maker

Turns a topic into a finished carousel: a cover, one slide per step, and call-to-action ("ad") slides, all in one consistent 2.5D style.
You write the content as JSON; the script draws and renders every slide. Never draw slides by hand.

## Setup (once)

The scripts are in the `scripts/` folder next to this file; the fonts are bundled in `fonts/`.

1. Python 3.10 or newer (`python --version`).
2. Playwright and its Chromium: `python -m pip install playwright` then `python -m playwright install chromium`.

Run `python scripts/make_carousel.py --check examples/instagram-automation.json` (paths relative to this skill's folder) to confirm it works.

## Workflow

1. **Understand the carousel.** Ask only what you cannot infer: the topic and the audience, the steps (or the material to take them from),
   the platform, the call to action (comment a keyword, DM a keyword, join a community, save the post), the brand colour and logos.
   Default to 14 steps and 3 ad slides (18 slides) for a full process; a short list can be 6 to 10 slides.
2. **Write the steps.** One idea per slide. A `label` of one or two words, a `title` of about 20 characters, a `line` of one or two plain
   sentences (under about 140 characters) with a concrete number or detail. No hype words, no em dashes.
3. **Pick a scene per step** from [references/scenes.md](references/scenes.md), matching what the step does (queues: `stack`, sources: `float`,
   filters: `gate`, scores: `bars` or `gauge`, rules: `doc`, comparisons: `versus`, schedules: `clock`, logs: `terminal`...). Vary them:
   no scene twice in a row, few scenes more than twice.
4. **Write the ad slides.** Each one different: a different kind (`comment`, `dm`, `discord`, `save`), a different keyword and a different
   reason to act. Typical positions: 5, 15 and `last`.
5. **Write the JSON** (format in references/scenes.md; examples/instagram-automation.json is a complete example) into the user's folder,
   then run `python <skill>/scripts/make_carousel.py --check content.json` and fix every error it prints.
6. **Render:** `python <skill>/scripts/make_carousel.py content.json <out-folder>`. It writes `slides/slide-01.png` and onward, `sheet.png`
   and `carousel.html`.
7. **Look at sheet.png** (open the image) before showing it. Check every slide for: text cut at the left or right edge, a tag covering
   another label, a card running into the footer line or the progress bar, a title that wrapped badly. Fix by shortening text, moving
   a long item, or swapping the scene, then render again. Look at single slides at full size when in doubt.
8. **Deliver:** the folder path, the sheet, and one line per ad slide saying what it asks for.

## Style rules (do not break them)

- White canvas, black text; colour comes only from logos, the step colours and coloured lines.
- One highlighted phrase per title at most (`[[...]]`), usually the payoff word.
- Big and filling: if a slide looks empty, choose a richer scene or add items; if it looks crowded, cut words, not the scene.
- Logos are always round coins. Use the built-in ones or define the user's own in `logos` (a letter coin is fine).
- Slides are 1080x1440 (3:4), which Instagram, LinkedIn and X all accept.

## Example

User: "make a carousel about my content workflow, 6 steps, ask people to comment GUIDE"

You write `workflow.json` with a 3-line title, 6 steps (stack, float, doc, versus, gauge, dash), ads `{"4": {"kind": "comment", "word": "GUIDE", ...},
"last": {"kind": "save", ...}}`, run `--check`, render to `workflow-carousel/`, open `workflow-carousel/sheet.png`, fix one long title,
render again, and answer with the folder and the two asks.
