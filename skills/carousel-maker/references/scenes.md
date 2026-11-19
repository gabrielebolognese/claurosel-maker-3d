# Content format and scenes

A carousel is one JSON file. `python scripts/make_carousel.py --check content.json` validates it; `python scripts/make_carousel.py content.json OUT` renders it.

## Top level

| Key | Required | What |
|---|---|---|
| `title` | yes | the cover title. `\n` breaks a line, `[[words]]` puts them in the black highlight block. Three short lines fit best (about 14 characters each); keep line 1 short, the logo coin sits to its right |
| `subtitle` | no | a small mono line under the title, uppercase reads best ("14 STEPS · ONE IDEA IN · ONE REEL OUT") |
| `label` | yes | the small top-right label on every slide ("INSTAGRAM AUTOMATION") |
| `logo` | no | the big coin on the cover, and the default coin of the ad slides: a built-in name or one from `logos` |
| `hub_logo` | no | a coin on the cover board |
| `hub_text` | no | the mono line on the cover's hub screen (defaults to `label`) |
| `accent` | no | a hex colour for the DM bubble when the platform has no colour of its own |
| `platform` | no | `instagram`, `x`, `tiktok`, `linkedin`, `youtube` or any logo name: sets the DM bubble colour, the comment button word and the ad coins |
| `logos` | no | your own logos: `{"acme": {"bg": "#123456", "text": "AC"}}` for a letter coin, or `{"acme": {"bg": "#123456", "svg": "<path d='...' fill='#fff'/>"}}` with shapes drawn in a 24x24 box |
| `steps` | yes | the content slides, in order (below) |
| `ads` | yes | the call-to-action slides by position: `{"5": {...}, "15": {...}, "last": {...}}` (can be `{}`) |

Slide count = 1 cover + steps + ads. Every ad position must be inside that count. Fifteen or more slides is a good length for a step-by-step carousel.

Built-in logos: `claude`, `youtube`, `x`, `instagram`, `discord`, `github`, `reddit`, `hn` (Hacker News), `hf` (Hugging Face), `chrome`, `capcut`.
Any other name becomes a letter coin automatically (better: define it in `logos`).

## A step

```json
{"label": "RESEARCH", "title": "Research", "line": "One or two sentences that explain the step.", "scene": "float",
 "tools": "CLAUDE CODE · PLAYWRIGHT", "color": "#E6B800", "data": {...}}
```

`label` (short, uppercase) appears as "STEP 03 · RESEARCH" and on the cover board (up to 12). `title`: about 20 characters fits one line; a longer
title wraps and the scene shrinks to make room. `line`: up to about 140 characters. `tools`: a mono footer line (optional). `color`: optional, a
palette colour is picked per step otherwise; it colours the step dot, the scene's accents and its line on the cover.

Lists of pairs or triples are JSON arrays: `["SOLVES", 9]`.

## The scenes

| Scene | Shows | `data` |
|---|---|---|
| `stack` | a queue of stacked cards, the first one black | `rows`: up to 5 strings; `tag`: a label; `first_label`: the first row's mono word (default NEXT) |
| `float` | 4 source cards floating around a black block, dashed lines to it | `cards`: exactly 4 `[head, small_line, big_line]`; a head that starts with `@` shows that logo (`"@github"`), else a coloured badge; `block`, `block_sub`: the block's text |
| `gate` | a gate over a conveyor, two cards pass, one is rejected | `tag`: the gate's label; `fail`: the rejected card's label |
| `bars` | 3D bars with scores, one highlighted | `bars`: up to 8 `[label, score]`; `win`: index of the highlighted bar (default 0); `k`: bar height per point (default 4.4; use about 42 for scores out of 10; keep the tallest bar under about 320 units of height). List the bars from tallest to shortest: a short bar's score hides behind a taller bar placed after it |
| `doc` | a document with check chips | `file`: the header; `checks`: up to 4 strings |
| `versus` | two logo coins on blocks with VS | `left`, `right`: logo names; `left_label`, `right_label`; `tag`: above the VS |
| `wave` | an audio waveform with word chips | `words`: up to 4 `[word, time]`; `tag` |
| `browser` | a browser window with 3 cells, a cursor and a ring | `url`; `cells`: 3 `[small, big]`; `hl`: highlighted cell index (default 2); `coin`: a logo (default chrome); `tag` |
| `phone` | a phone with a grid or a caption | `mode`: `grid` (with `cells`: 9 short strings) or `caption` (with `lines`: up to 4, the first bold); `head`: the screen's top line; `chips`: up to 3; `coin`: a logo |
| `layers` | stacked transparent layers | `layers`: up to 5 `[name, kind]`, kind one of paper, cards, text, caption, mascot; `text`: the text layer's words; `caption`: two words `[plain, highlighted]`; `tag` |
| `qa` | a filmstrip and a score card with a red flag | `scores`: up to 5 `[name, 0 to 5]` (under 4 shows red); `tag`: the red flag |
| `sound` | a waveform with cue flags | `cues`: up to 5 words; `tag` |
| `thread` | a thread of posts joined by a line | `posts`: up to 5 strings, the first is the main post; `tag` |
| `gauge` | a dial with a score | `value`: 0 to 100; `formula`: a label under the dial; `drop`: the red label; `keep`: the green label |
| `monitor` | an upright screen recording | `tag`; `stat`: the screen's bottom line; `coin`: a logo (optional) |
| `sheet` | a list of rows with buttons and a big number | `file`: the header; `rows`: up to 4 `[handle, text]`; `count`: the big number; `button`: the row button word (default OPEN); `tag` |
| `network` | nodes and edges around a hub | `nodes`: `[x, y, label, kind]` in a 860x860 board (x, y about 100 to 800), kind hub, node or hot; `edges`: `[from_index, to_index]`; `dashed`: true for dashed edges; `tag` |
| `dash` | a dashboard of 6 cards with statuses | `file`; `cards`: up to 6 `[name, status]`; `ready`: the status shown in colour (default READY); `coin`: a logo; `tag` |
| `clock` | a clock with coloured slots and schedule chips | `hours`: up to 4 hours (0 to 11) to mark; `chips`: up to 4 strings |
| `terminal` | a terminal log with a green loop | `log`: up to 7 `[time, KIND, message]`, KIND one of RETRY, ERROR, FIXED, DONE, POSTED, QUEUED (coloured); `tag` |

Pick a different scene for each step where you can: variety is what makes the carousel feel designed. Use `versus` when the step compares
two things, `bars` or `gauge` for scores, `stack` for queues and rankings, `float` for sources, `doc` for rules and checklists.

## Ad slides

Every ad slide has a `title` (`[[word]]` highlights) and a `line`. Make each one different: a different ask and a different reason.

| Kind | Looks like | Extra keys |
|---|---|---|
| `comment` | a comment box with the keyword, hearts, a logo coin | `word`: the keyword; `tag`; `logo` (default: the platform) |
| `discord` | a dark slide with a big community coin and a sticker | `sticker` (default FREE); `badge` (default LINK IN BIO); `logo` (default discord) |
| `dm` | a phone with a DM conversation and a follow button | `word`: the DM keyword; `you`: the first bubble (`[[word]]` is bold); `reply`: the answer bubble; `button` (default FOLLOW FIRST) |
| `save` | a checklist card with a bookmark | `file`: the card header; `items`: up to 4 strings; `tag` |

A good spread for 18 slides: an ad at 5, at 15 and the last slide, each a different kind.
