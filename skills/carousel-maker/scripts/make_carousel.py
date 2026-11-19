"""Build a 2.5D carousel from a JSON content file.

    python make_carousel.py content.json OUT_DIR
    python make_carousel.py --check content.json      (validate only, no render)

Writes OUT_DIR/slides/slide-01.png ... (1080x1440), OUT_DIR/sheet.png (every slide in rows) and OUT_DIR/carousel.html.
The content format and every scene are described in ../references/scenes.md.
"""
import argparse, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import carousel_lib as L  # noqa: E402

PALETTE = ["#FF3B30", "#FF9500", "#E6B800", "#34C759", "#00B8A9", "#32ADE6", "#007AFF", "#5856D6", "#AF52DE", "#FF2D55", "#8E6E4E", "#1FA2B8", "#FF6B00", "#0A0A0A"]

REQUIRED = {
    "stack": ["rows", "tag"], "float": ["cards", "block", "block_sub"], "gate": ["tag", "fail"], "bars": ["bars"], "doc": ["file", "checks"],
    "versus": ["left", "right", "left_label", "right_label", "tag"], "wave": ["words", "tag"], "browser": ["url", "cells", "tag"],
    "phone": ["mode", "head"], "layers": ["layers", "tag"], "qa": ["scores", "tag"], "sound": ["cues", "tag"], "thread": ["posts", "tag"],
    "gauge": ["value", "formula", "drop", "keep"], "monitor": ["tag"], "sheet": ["file", "count", "rows", "tag"],
    "network": ["nodes", "edges", "tag"], "dash": ["file", "cards", "tag"], "clock": ["hours", "chips"], "terminal": ["log", "tag"],
}
LIMITS = {"stack": ("rows", 5), "float": ("cards", 4), "bars": ("bars", 8), "doc": ("checks", 4), "wave": ("words", 4), "browser": ("cells", 3),
          "layers": ("layers", 5), "qa": ("scores", 5), "sound": ("cues", 5), "thread": ("posts", 5), "sheet": ("rows", 4), "dash": ("cards", 6),
          "clock": ("chips", 4), "terminal": ("log", 7)}
AD_REQUIRED = {"comment": ["word", "title", "line", "tag"], "discord": ["title", "line"], "dm": ["word", "you", "title", "line"], "save": ["file", "items", "title", "line", "tag"]}
DARK_ADS = {"discord"}


def fail(msg):
    raise SystemExit("content error: " + msg)


def marks(text, dark=False, tag="span"):
    """Escape text, turn [[words]] into the highlight block and a line break into <br>."""
    out = L.E(text)
    if tag == "span":
        out = re.sub(r"\[\[(.+?)\]\]", lambda m: f'<span class="inv{" w" if dark else ""}">{m.group(1)}</span>', out)
    else:
        out = re.sub(r"\[\[(.+?)\]\]", r"<b>\1</b>", out)
    return out.replace("\n", "<br>")


def validate(c):
    for k in ("title", "label", "steps", "ads"):
        if k not in c:
            fail(f'missing top-level key "{k}"')
    if not c["steps"]:
        fail("steps is empty")
    for i, s in enumerate(c["steps"], 1):
        where = f'step {i} ("{s.get("title", "?")}")'
        for k in ("label", "title", "line", "scene", "data"):
            if k not in s:
                fail(f'{where} has no "{k}"')
        if s["scene"] not in REQUIRED:
            fail(f'{where}: unknown scene "{s["scene"]}"; scenes: {", ".join(REQUIRED)}')
        for k in REQUIRED[s["scene"]]:
            if k not in s["data"]:
                fail(f'{where}: scene "{s["scene"]}" needs data.{k}')
        if s["scene"] == "phone":
            need = "cells" if s["data"]["mode"] == "grid" else "lines"
            if need not in s["data"]:
                fail(f'{where}: a phone in mode "{s["data"]["mode"]}" needs data.{need}')
        if s["scene"] in LIMITS:
            k, n = LIMITS[s["scene"]]
            if len(s["data"][k]) > n:
                fail(f'{where}: data.{k} has {len(s["data"][k])} items, the scene holds {n}')
        if s["scene"] == "float" and len(s["data"]["cards"]) != 4:
            fail(f"{where}: a float scene takes exactly 4 cards")
        if len(s["title"]) > 22:
            print(f'warning: {where}: titles over about 20 characters wrap to two lines (the scene then shrinks to fit)', file=sys.stderr)
        if len(s["line"]) > 170:
            print(f"warning: {where}: the line is long ({len(s['line'])} characters); keep it under about 140", file=sys.stderr)
    total = 1 + len(c["steps"]) + len(c["ads"])
    seen = set()
    for key, a in c["ads"].items():
        n = total if key == "last" else int(key)
        if not 2 <= n <= total or n in seen:
            fail(f'ad slide "{key}" is outside 2..{total} or used twice (the carousel has {total} slides: cover + steps + ads)')
        seen.add(n)
        if a.get("kind") not in AD_REQUIRED:
            fail(f'ad "{key}": kind must be one of {", ".join(AD_REQUIRED)}')
        for k in AD_REQUIRED[a["kind"]]:
            if k not in a:
                fail(f'ad "{key}" ({a["kind"]}) needs "{k}"')
    return total


def cover(c):
    """The default cover: the title on top, the main logo coin, and a board of every step around a hub."""
    W = H = 1000
    steps = c["steps"]
    labels = [s["label"] for s in steps][:12]
    P_ALL = [(60, 70), (290, 70), (520, 70), (750, 70), (830, 290), (830, 470), (830, 650), (750, 870), (520, 870), (290, 870), (60, 870), (-20, 650)]
    n = len(labels)
    P = [P_ALL[round(i * 12 / n) % 12] for i in range(n)] if n < 12 else P_ALL
    ph0, ph1 = (360, 230), (640, 770)
    traces, dots, items = [], [], []
    for k, (x, y) in enumerate(P):
        col = steps[k]["color"]
        cw = max(196, 54 + len(labels[k]) * 15)
        cx, cy = x + cw / 2, y + 42
        outside = cy < ph0[1] or cy > ph1[1]
        tx, ty = min(max(cx, ph0[0] + 20), ph1[0] - 20), min(max(cy, ph0[1] + 20), ph1[1] - 20)
        d = f"M{cx} {cy} L{cx} {ty} L{tx} {ty}" if outside else f"M{cx} {cy} L{tx} {cy}"
        traces.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>')
        dx, dy = (cx, (cy + ty) / 2) if outside else ((cx + tx) / 2, cy)
        dots.append(f'<circle cx="{dx}" cy="{dy}" r="13" fill="{col}"/><circle cx="{dx}" cy="{dy}" r="5" fill="#fff"/>')
    items.append(L.svg("".join(traces) + "".join(dots), W, H))
    cols = ["#0a0a0a", "#ededeb"] + [s["color"] for s in steps[:10]]
    grid = "".join(f'<div class="rg" style="background:{cols[(i * 5) % len(cols)]}"></div>' for i in range(12))
    screen = f'<div class="phs"><div class="phh mono">{L.E(c.get("hub_text", c["label"]))}</div><div class="rgrid">{grid}</div></div>'
    items.append(L.shadow(ph0[0], ph0[1], ph1[0] - ph0[0], ph1[1] - ph0[1], 0.16))
    items.append(L.box(ph0[0], ph0[1], ph1[0] - ph0[0], ph1[1] - ph0[1], 34, top="#0a0a0a", front="#1c1c1c", side="#2a2a2a", inner=screen, border=False))
    for k, (x, y) in enumerate(P):
        cw = max(196, 54 + len(labels[k]) * 15)
        items.append(L.box(x, y, cw, 84, 24, top="#ffffff", inner=f'<div class="nlab"><i style="background:{steps[k]["color"]}"></i>{L.E(labels[k])}</div>'))
    if c.get("hub_logo"):
        items.append(L.coin(140, 560, 40, 170, c["hub_logo"], 16))
    board = L.plane("".join(items), W, H, 555, 905, scale=0.84)
    title = f'<h1 class="cover-t">{marks(c["title"])}</h1>'
    sub = f'<div class="cover-s mono">{L.E(c.get("subtitle", ""))}</div>' if c.get("subtitle") else ""
    logo = L.flatcoin(c["logo"], 230) if c.get("logo") else ""
    return board + title + sub + logo


def main():
    ap = argparse.ArgumentParser(description="Build a 2.5D carousel (1080x1440 PNG slides and a sheet) from a JSON content file.")
    ap.add_argument("content", help="the content JSON (see references/scenes.md)")
    ap.add_argument("out", nargs="?", help="the output folder")
    ap.add_argument("--check", action="store_true", help="validate the JSON only")
    a = ap.parse_args()
    sys.stdout.reconfigure(newline="\n")
    c = json.loads(Path(a.content).read_text(encoding="utf-8"))
    for name, lg in c.get("logos", {}).items():
        L.register_logo(name, lg.get("bg", "#0A0A0A"), svg=lg.get("svg"), text=lg.get("text"), fg=lg.get("fg", "#ffffff"))
    for i, s in enumerate(c.get("steps", [])):
        s.setdefault("color", PALETTE[i % len(PALETTE)])
        s.setdefault("tools", "")
    total = validate(c)
    print(f"content ok: {total} slides ({len(c['steps'])} steps, {len(c['ads'])} ad slides, 1 cover)")
    if a.check:
        return
    if not a.out:
        raise SystemExit("give an output folder, or --check")
    ads = {}
    for key, ad in c["ads"].items():
        n = total if key == "last" else int(key)
        ad = dict(ad)
        dark = ad["kind"] in DARK_ADS
        ad["title"] = marks(ad["title"], dark=dark)
        if "you" in ad:
            ad["you"] = marks(ad["you"], tag="b")
        if "logo" in ad:
            ad["coin"] = ad.pop("logo")
        ads[n] = ad
    content = dict(steps=c["steps"], ads=ads, label=c["label"], accent=c.get("accent", "#0A0A0A"),
                   platform=c.get("platform", c.get("logo", "instagram")), cover=lambda: cover(c))
    L.build(content, str(Path(a.out)))


if __name__ == "__main__":
    main()
