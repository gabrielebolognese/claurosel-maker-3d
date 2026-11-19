"""carousel-maker: 2.5D isometric carousel slides on a white canvas with a fine floor grid, solid 3D blocks, billboard labels that face the
camera, floating cards with floor shadows, big round 3D logo coins, a tight text block on top and a scene that fills the rest.
1080x1440 slides (3:4), PNGs plus a sheet.png. build(content, out_dir) renders a content dict; make_carousel.py builds one from JSON."""
import html, os, time
from pathlib import Path

FONTS = (Path(__file__).resolve().parent.parent / "fonts").as_uri() + "/"
E = html.escape
RX, RZ = 58, 40


def shade(hexc, k):
    if not hexc.startswith("#"):
        return "#7a1c3e"
    h = hexc.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % (int(r * k), int(g * k), int(b * k))


# ---------------------------------------------------------------- 3D primitives (positions in plane pixels)
def plane(inner, w, h, cx, cy, scale=1.0, grid=True, persp=2200):
    g = " grid" if grid else ""
    return (f'<div class="stage" style="perspective:{persp}px;perspective-origin:{cx}px {cy - 300}px">'
            f'<div class="plane{g}" style="width:{w}px;height:{h}px;left:{cx - w / 2}px;top:{cy - h / 2}px;transform:rotateX({RX}deg) rotateZ({RZ}deg) scale({scale})">{inner}</div></div>')


def box(x, y, w, d, h, top="#ffffff", front=None, side=None, z=0, inner="", border=True, extra=""):
    front = front or (shade(top, 0.82) if top.startswith("#") else "#d4d4d2")
    side = side or (shade(top, 0.66) if top.startswith("#") else "#b8b8b6")
    b = "outline:2px solid #0a0a0a;outline-offset:-1px;" if border else ""
    return (f'<div class="b3" style="left:{x}px;top:{y}px;width:{w}px;height:{d}px;transform:translateZ({z}px);{extra}">'
            f'<div class="f" style="width:{w}px;height:{h}px;left:0;top:{d}px;background:{front};transform-origin:0 0;transform:rotateX(90deg);{b}"></div>'
            f'<div class="f" style="width:{h}px;height:{d}px;left:{w}px;top:0;background:{side};transform-origin:0 0;transform:rotateY(-90deg);{b}"></div>'
            f'<div class="f top" style="width:{w}px;height:{d}px;left:0;top:0;background:{top};transform:translateZ({h}px);{b}">{inner}</div></div>')


def bb(x, y, z, inner):
    return f'<div class="bb" style="left:{x}px;top:{y}px;transform:translateZ({z}px) rotateZ({-RZ}deg) rotateX({-RX}deg) translate(-50%,-100%)">{inner}</div>'


def shadow(x, y, w, d, op=0.12):
    return f'<div class="sh" style="left:{x + 14}px;top:{y + 14}px;width:{w}px;height:{d}px;background:rgba(10,10,10,{op})"></div>'


def card(x, y, w, d, z, inner, bg="#ffffff", thick=10):
    return (shadow(x, y, w, d) if z > 0 else "") + box(x, y, w, d, thick, top=bg, z=z, inner=inner)


def svg(paths, w=860, h=860):
    return f'<svg class="psvg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{paths}</svg>'


GLYPH = {
    "claude": ("#D97757", '<g fill="#fff">' + "".join(f'<rect x="11" y="2.5" width="2" height="19" rx="1" transform="rotate({a} 12 12)"/>' for a in (0, 30, 60, 90, 120, 150)) + "</g>"),
    "youtube": ("#FF0000", '<path d="M9.2 7.6v8.8l7.6-4.4z" fill="#fff"/>'),
    "x": ("#0A0A0A", '<path fill="#fff" d="M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932ZM17.61 20.644h2.039L6.486 3.24H4.298Z"/>'),
    "instagram": ("linear-gradient(45deg,#f9ce34,#ee2a7b 55%,#6228d7)", '<rect x="2.5" y="2.5" width="19" height="19" rx="5.5" fill="none" stroke="#fff" stroke-width="2.1"/><circle cx="12" cy="12" r="4.4" fill="none" stroke="#fff" stroke-width="2.1"/><circle cx="17.6" cy="6.4" r="1.3" fill="#fff"/>'),
    "discord": ("#5865F2", '<path fill="#fff" d="M20.317 4.37a19.79 19.79 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.74 19.74 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.1 13.1 0 0 1-1.872-.892.077.077 0 0 1-.008-.128c.126-.094.252-.192.372-.291a.074.074 0 0 1 .078-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.009c.12.1.246.198.373.292a.077.077 0 0 1-.006.127 12.3 12.3 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.84 19.84 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.331c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/>'),
    "github": ("#0A0A0A", '<path fill="#fff" d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>'),
    "reddit": ("#FF4500", '<ellipse cx="12" cy="14" rx="7.5" ry="5" fill="#fff"/><circle cx="9.2" cy="13.6" r="1.2" fill="#FF4500"/><circle cx="14.8" cy="13.6" r="1.2" fill="#FF4500"/><path d="M9.3 16.4c1.6 1 3.8 1 5.4 0" stroke="#FF4500" stroke-width="1" fill="none" stroke-linecap="round"/><circle cx="17.5" cy="5.6" r="1.5" fill="#fff"/><path d="M12 9V5.3l5.2 .5" stroke="#fff" stroke-width="1.2" fill="none"/>'),
    "hn": ("#FF6600", '<path d="M7 5.5h2.4l2.6 5 2.6-5H17l-3.9 7.1V18.5h-2.2v-5.9z" fill="#fff"/>'),
    "hf": ("#FFD21E", '<circle cx="12" cy="12" r="8.5" fill="#FFD21E"/><circle cx="9" cy="10.4" r="1.3" fill="#3a2d0a"/><circle cx="15" cy="10.4" r="1.3" fill="#3a2d0a"/><path d="M8.2 13.6c2 2.6 5.6 2.6 7.6 0" stroke="#3a2d0a" stroke-width="1.6" fill="none" stroke-linecap="round"/>'),
    "chrome": ("#ffffff", '<circle cx="12" cy="12" r="9.5" fill="#DB4437"/><path d="M12 12L3.8 16.8A9.5 9.5 0 0 1 4.6 6Z" fill="#0F9D58"/><path d="M12 12h9.5a9.5 9.5 0 0 1-12.8 8.9Z" fill="#F4B400"/><circle cx="12" cy="12" r="4.2" fill="#fff"/><circle cx="12" cy="12" r="3.2" fill="#4285F4"/>'),
    "capcut": ("#0A0A0A", '<path d="M5 8.5l7-3.5 7 3.5-7 3.5z M5 15.5l7-3.5 7 3.5-7 3.5z" fill="none" stroke="#fff" stroke-width="1.8" stroke-linejoin="round"/>'),
}


def register_logo(name, bg, svg=None, text=None, fg="#ffffff"):
    """Add a logo: an SVG drawn in a 24x24 box (white shapes read best), or up to 3 letters."""
    if svg:
        GLYPH[name] = (bg, svg)
    else:
        t = (text or name[:2]).upper()[:3]
        size = {1: 14, 2: 11, 3: 8.5}[len(t)]
        GLYPH[name] = (bg, f'<text x="12" y="{12 + size * 0.36:.1f}" text-anchor="middle" font-family="Inter" font-weight="850" font-size="{size}" fill="{fg}">{E(t)}</text>')


FALLBACK = ["#0A0A0A", "#FF3B30", "#007AFF", "#34C759", "#AF52DE", "#FF9500"]


def glyph(brand):
    if brand not in GLYPH:
        register_logo(brand, FALLBACK[sum(map(ord, brand)) % len(FALLBACK)], text=brand[:2])
    return GLYPH[brand]


def coin(x, y, z, d, brand, thick=16):
    """A round 3D coin standing up and facing the camera (a big, round logo) with its shadow on the floor."""
    bg, g = glyph(brand)
    edge = shade(bg, 0.62) if bg.startswith("#") else "#8d1f52"
    if bg == "#0A0A0A":
        edge = "#2c2c2c"
    layers = ",".join(f"0 {k}px 0 {edge}" for k in range(1, thick + 1)) + f",0 {thick + 2}px 0 rgba(10,10,10,.25)"
    sh = f'<div class="csh" style="left:{x - d * 0.42}px;top:{y - d * 0.28}px;width:{d * 0.84}px;height:{d * 0.56}px"></div>'
    face = (f'<div class="coin" style="width:{d}px;height:{d}px;background:{bg};box-shadow:{layers},inset 0 -{d // 14}px 0 rgba(0,0,0,.14),inset 0 {d // 22}px 0 rgba(255,255,255,.18)">'
            f'<svg viewBox="0 0 24 24" style="width:{int(d * 0.58)}px;height:{int(d * 0.58)}px">{g}</svg></div>')
    return sh + bb(x, y, z, face)


def flatcoin(brand, d, cls=""):
    """The same coin as a plain element on the slide (next to a title)."""
    bg, g = glyph(brand)
    edge = shade(bg, 0.62) if bg.startswith("#") else "#8d1f52"
    if bg == "#0A0A0A":
        edge = "#333333"
    layers = ",".join(f"0 {k}px 0 {edge}" for k in range(1, 19)) + ",0 20px 0 rgba(10,10,10,.22)"
    return (f'<div class="fcoin {cls}"><div class="csh2"></div><div class="coin" style="width:{d}px;height:{d}px;background:{bg};box-shadow:{layers},inset 0 -16px 0 rgba(0,0,0,.14),inset 0 10px 0 rgba(255,255,255,.18)">'
            f'<svg viewBox="0 0 24 24" style="width:{int(d * 0.56)}px;height:{int(d * 0.56)}px">{g}</svg></div></div>')


def tag(text, kind="dark", color=None):
    st = f' style="background:{color};color:#fff;border-color:{color}"' if color else ""
    return f'<div class="tag {kind}"{st}>{E(text)}</div>'


# ---------------------------------------------------------------- scene templates: each returns plane items; data is a dict
def s_stack(c, d):
    it = []
    rows = d["rows"]
    for i, r in enumerate(rows):
        top = "#0a0a0a" if i == 0 else "#ffffff"
        lab = d.get("first_label", "NEXT") if i == 0 else f"{i + 1:02d}"
        txt = f'<div class="qrow{" inv2" if i == 0 else ""}"><span class="mono">{E(lab)}</span>{E(r)}</div>'
        it.append(card(80 + i * 26, 120 + i * 130, 640, 110, 160 - i * 34, txt, bg=top, thick=16))
    it.append(bb(600, 40, 230, tag(d["tag"], color=c)))
    return it


def s_float(c, d):
    it, lines = [], []
    pos = [(40, 40, 230), (500, 20, 300), (20, 520, 170), (590, 620, 170)]
    for (fid, u, t), (x, y, z) in zip(d["cards"], pos):
        head = f'<b style="background:{c}">{E(fid)}</b>' if not fid.startswith("@") else f'<span class="cmini">{coin_inline(fid[1:])}</span>'
        it.append(card(x, y, 300, 190, z, f'<div class="srcc">{head}<div class="mono u">{E(u)}</div><div class="t">{E(t)}</div></div>'))
        lines.append(f'<path d="M{x + 150} {y + 95} L430 430" stroke="{c}" stroke-width="4" stroke-dasharray="3 12"/>')
    it.insert(0, svg("".join(lines)))
    it.append(box(300, 320, 260, 220, 70, top="#0a0a0a", front="#1c1c1c", side="#2b2b2b", inner=f'<div class="fold">{E(d["block"])}<br><small>{E(d["block_sub"])}</small></div>', border=False))
    return it


def coin_inline(brand):
    bg, g = glyph(brand)
    return f'<span class="ci" style="background:{bg}"><svg viewBox="0 0 24 24">{g}</svg></span>'


def s_gate(c, d):
    it = [svg('<rect x="60" y="380" width="760" height="120" fill="#f1f1ef" stroke="#0a0a0a" stroke-width="2"/>' + "".join(f'<path d="M{x} 380 L{x} 500" stroke="rgba(10,10,10,.15)" stroke-width="2"/>' for x in range(100, 820, 60)))]
    it += [box(400, 330, 40, 40, 300, top="#0a0a0a", border=False), box(400, 520, 40, 40, 300, top="#0a0a0a", border=False), box(400, 330, 40, 230, 40, top=c, z=300, border=False),
           card(150, 395, 170, 90, 30, '<div class="gc ok">✓</div>', thick=12), card(560, 395, 170, 90, 30, '<div class="gc ok">✓</div>', thick=12),
           box(640, 600, 170, 90, 12, top="#ffffff", inner='<div class="gc no">✕</div>', extra="transform:translateZ(0) rotateZ(28deg)"),
           bb(420, 440, 380, tag(d["tag"], color=c)), bb(720, 660, 60, tag(d["fail"], "red"))]
    return it


def s_bars(c, d):
    it = []
    n = len(d["bars"])
    step = 700 / n
    for i, (lab, sc) in enumerate(d["bars"]):
        x = 90 + i * step
        wv = max(40, step - 40)
        win = i == d.get("win", 0)
        col = c if win else ("#0a0a0a" if i % 2 else "#ffffff")
        it.append(box(x, 520, wv, wv, sc * d.get("k", 4.4), top=col, border=(col == "#ffffff")))
        it.append(bb(x + wv / 2, 520 + wv / 2, sc * d.get("k", 4.4) + 26, f'<div class="score{" win" if win else ""}{" sm" if n > 5 else ""}" style="{"background:" + c + ";border-color:" + c if win else ""}">{sc}</div>'))
        it.append(bb(x + wv + 10, 520 + wv + 60, 4, f'<div class="hlb{" w" if win else ""}{" sm" if n > 5 else ""}" style="{"background:" + c + ";border-color:" + c if win else ""}">{E(lab)}</div>'))
    return it


def s_doc(c, d):
    lines = "".join(f'<div class="dl" style="width:{w}%"></div>' for w in (92, 70, 86, 60, 95, 78, 66, 90, 74, 82))
    it = [box(140, 120, 520, 640, 26, top="#ffffff", inner=f'<div class="docp"><div class="mono dh">{E(d["file"])}</div>{lines}</div>')]
    for k, t in enumerate(d["checks"]):
        it.append(bb(520, 320, 390 - k * 85, f'<div class="chip"><span style="background:{c}">✓</span>{E(t)}</div>'))
    return it


def s_versus(c, d):
    it = [box(110, 300, 240, 240, 60, top="#ffffff"), box(510, 300, 240, 240, 60, top="#0a0a0a", front="#1c1c1c", side="#2a2a2a", border=False)]
    it.append(coin(230, 420, 70, 180, d["left"], 16))
    it.append(coin(630, 420, 70, 180, d["right"], 16))
    it.append(bb(230, 660, 10, tag(d["left_label"], "light")))
    it.append(bb(630, 660, 10, tag(d["right_label"], color=c)))
    it.append(bb(430, 420, 260, f'<div class="vsw">{tag(d["tag"])}<div class="vs">VS</div></div>'))
    return it


def s_wave(c, d):
    hs = [30, 70, 120, 60, 160, 210, 110, 70, 180, 250, 150, 90, 60, 130, 200, 170, 80, 40, 110, 230, 270, 190, 130, 220, 170, 100, 150, 200, 110, 60]
    it = []
    for i, h_ in enumerate(hs):
        colr = c if 12 <= i <= 20 else "#0a0a0a"
        it.append(box(70 + i * 25, 420, 16, 60, h_, top=colr, front=shade(colr, .78), side=shade(colr, .6), border=False))
    for (w, t), x in zip(d["words"], (120, 290, 450, 640)):
        it.append(bb(x, 640, 40, f'<div class="wt">{E(w)}<small class="mono">{E(t)}</small></div>'))
    it.append(bb(420, 420, 330, tag(d["tag"], color=c)))
    return it


def s_browser(c, d):
    cells = "".join(f'<div class="pc{" hl" if i == d.get("hl", 2) else ""}" style="{"border-color:" + c if i == d.get("hl", 2) else ""}"><b>{E(a)}</b><span>{E(b)}</span></div>' for i, (a, b) in enumerate(d["cells"]))
    ui = f'<div class="bw"><div class="bwb"><i></i><i></i><i></i><span class="mono">{E(d["url"])}</span></div><div class="bwc">{cells}</div></div>'
    it = [box(80, 160, 720, 520, 30, top="#ffffff", inner=ui),
          svg(f'<circle cx="640" cy="470" r="70" fill="none" stroke="{c}" stroke-width="7"/><circle cx="640" cy="470" r="38" fill="none" stroke="{c}" stroke-width="4" opacity=".6"/>'),
          bb(650, 480, 150, '<svg class="cursor" viewBox="0 0 24 24"><path d="M4 2l14 9.5-6.2 1.2 3.6 7.1-2.6 1.3-3.6-7.2L4 18z" fill="#0a0a0a" stroke="#fff" stroke-width="1.4" stroke-linejoin="round"/></svg>'),
          coin(620, 40, 90, 140, d.get("coin", "chrome"), 12), bb(560, 640, 40, tag(d["tag"]))]
    return it


def s_phone(c, d):
    if d.get("mode") == "grid":
        cells = "".join(f'<div class="rg" style="background:{["#0a0a0a", "#ededeb", c, "#ededeb", "#0a0a0a", "#ededeb", "#ededeb", c, "#0a0a0a"][i]}"><span class="mono">{E(t)}</span></div>' for i, t in enumerate(d["cells"]))
        screen = f'<div class="phs"><div class="phh mono">{E(d["head"])}</div><div class="rgrid">{cells}</div></div>'
    else:
        lines = "".join(f'<div class="cap{" b" if i == 0 else ""}">{E(t)}</div>' for i, t in enumerate(d["lines"]))
        screen = f'<div class="phs"><div class="phh mono">{E(d["head"])}</div><div class="pv" style="background:{c}"></div>{lines}</div>'
    it = [card(250, 70, 380, 720, 90, screen, bg="#0a0a0a", thick=24)]
    for k, t in enumerate(d.get("chips", [])):
        it.append(bb(650, 320 + k * 120, 200 - k * 30, f'<div class="chip"><span style="background:{c}">✓</span>{E(t)}</div>'))
    if d.get("coin"):
        it.append(coin(150, 720, 50, 160, d["coin"], 14))
    return it


def s_layers(c, d):
    it = []
    for k, (name, kind) in enumerate(d["layers"]):
        z = 30 + k * 95
        inner = {"paper": '<div class="lay paper"></div>', "cards": f'<div class="lay"><div class="lc" style="left:40px;top:60px"></div><div class="lc" style="left:300px;top:200px;background:{c}"></div></div>',
                 "text": f'<div class="lay"><div class="lt2">{E(d.get("text", "YOUR HEADLINE"))}</div></div>', "caption": f'<div class="lay"><div class="lcap"><span>{E(d.get("caption", ["your", "caption"])[0])}</span> <b style="background:{c}">{E(d.get("caption", ["your", "caption"])[1])}</b></div></div>',
                 "mascot": f'<div class="lay"><div class="masc" style="background:{c}"></div></div>'}[kind]
        it.append(shadow(160, 160, 540, 540, 0.05))
        it.append(box(160, 160, 540, 540, 4, top=("#ffffff" if kind != "paper" else "#f4f4f2"), z=z, inner=inner))
        it.append(bb(700, 700, z + 10, tag(f"{k + 1}  {name}", "light")))
    it.append(bb(560, 860, 0, tag(d["tag"], color=c)))
    return it


def s_qa(c, d):
    it = []
    for k in range(6):
        dark = k % 3 == 1
        it.append(box(60 + k * 130, 220, 110, 160, 14, top=("#0a0a0a" if dark else "#ffffff"), z=k * 12, inner='<div class="perf"></div>'))
    rows = "".join(f'<div class="qr"><span class="mono">{E(n_)}</span>' + "".join(f'<i style="background:{(c if v >= 4 else "#E8322B") if j < v else "#ececea"}"></i>' for j in range(5)) + "</div>" for n_, v in d["scores"])
    it.append(bb(560, 650, 0, f'<div class="qcard up">{rows}</div>'))
    it.append(svg('<path d="M680 700 Q840 600 700 300" fill="none" stroke="#E8322B" stroke-width="6" stroke-dasharray="3 14"/>'))
    it.append(bb(380, 130, 300, tag(d["tag"], "red")))
    return it


def s_sound(c, d):
    hs = [40, 90, 140, 70, 110, 170, 120, 60, 90, 150, 200, 140, 80, 50, 110, 140, 90, 60, 120, 170, 110, 80, 50, 90, 140, 110, 60, 40]
    it = [box(70 + i * 27, 450, 18, 60, h_, top="#0a0a0a", front="#222", side="#333", border=False) for i, h_ in enumerate(hs)]
    for x, t in zip((110, 300, 470, 630, 790), d["cues"]):
        it.append(box(x, 330, 6, 6, 240, top=c, border=False))
        it.append(bb(x, 330, 250, f'<div class="flag" style="background:{c}">{E(t)}</div>'))
    it.append(bb(540, 620, 30, tag(d["tag"])))
    return it


def s_thread(c, d):
    it = [svg(f'<path d="M180 130 L180 760" stroke="{c}" stroke-width="8" stroke-linecap="round"/>')]
    for k, t in enumerate(d["posts"]):
        y = 90 + k * 140
        main = k == 0
        it.append(card(130, y, 560, 112, 170 - k * 28, f'<div class="tw{" m" if main else ""}"><span class="tav"></span><div><div class="mono s1">{"MAIN POST" if main else f"{k}."}</div><div class="s2">{E(t)}</div></div></div>', bg=("#0a0a0a" if main else "#ffffff"), thick=14))
    it.append(bb(420, 20, 330, tag(d["tag"], color=c)))
    return it


def s_gauge(c, d):
    val = d["value"]
    ang = -120 + 240 * val / 100
    ticks = "".join(f'<rect x="248" y="40" width="4" height="26" fill="{("#E8322B" if v < 70 else c) if v <= val else "#d9d9d7"}" transform="rotate({-120 + 240 * v / 100} 250 250)"/>' for v in range(0, 101, 5))
    dial = (f'<svg viewBox="0 0 500 500" class="gauge"><circle cx="250" cy="250" r="230" fill="#fff" stroke="#0a0a0a" stroke-width="5"/>{ticks}'
            f'<rect x="246" y="80" width="8" height="175" rx="4" fill="#0a0a0a" transform="rotate({ang} 250 250)"/><circle cx="250" cy="250" r="22" fill="#0a0a0a"/>'
            f'<text x="250" y="380" text-anchor="middle" font-family="Inter" font-weight="850" font-size="96" fill="#0a0a0a">{val}</text></svg>')
    row = f'<div class="grow">{tag(d["drop"], "red")}{tag(d["keep"], color="#34C759")}</div>'
    it = [svg('<ellipse cx="470" cy="600" rx="230" ry="120" fill="rgba(10,10,10,.10)"/>'), bb(470, 620, 0, f'<div class="gwrap">{dial}{tag(d["formula"])}{row}</div>')]
    return it


def s_monitor(c, d):
    cells = "".join(f'<i style="background:{c if (k * 7) % 11 == 0 else ("#ffffff" if (k * 3) % 5 == 0 else "#2a2a2a")};opacity:{0.35 + ((k * 13) % 7) / 10}"></i>' for k in range(16 * 9))
    screen = f'<div class="mon"><div class="mgrid">{cells}</div><div class="rec mono"><b></b>REC</div><div class="mono stat">{E(d.get("stat", "LIVE · 60 FPS"))}</div></div>'
    it = [box(300, 420, 260, 160, 24, top="#cfcfcd", border=False), box(410, 470, 40, 40, 150, top="#9a9a98", border=False),
          bb(450, 560, 90, f'<div class="monup">{screen}</div>'), bb(560, 700, 0, tag(d["tag"], color=c))] + ([coin(760, 370, 40, 140, d["coin"], 12)] if d.get("coin") else [])
    return it


def s_sheet(c, d):
    rows = "".join(f'<div class="sr"><span class="tav"></span><div class="st2"><div class="mono s1">@{E(h)}</div><div class="s3">{E(t)}</div></div><span class="ob mono" style="background:{c}">{E(d.get("button", "OPEN"))}</span></div>' for h, t in d["rows"])
    it = [box(100, 120, 660, 640, 24, top="#ffffff", inner=f'<div class="sheet"><div class="mono dh">{E(d["file"])}</div>{rows}</div>'),
          bb(600, 110, 300, f'<div class="bignum" style="background:{c}">{E(d["count"])}</div>'), bb(480, 790, 30, tag(d["tag"]))]
    return it


def s_network(c, d):
    it, lines = [], []
    nodes = d["nodes"]   # (x, y, label, kind)
    for a, b in d["edges"]:
        (x1, y1), (x2, y2) = nodes[a][:2], nodes[b][:2]
        lines.append(f'<path d="M{x1} {y1} L{x2} {y2}" stroke="{c}" stroke-width="5" stroke-dasharray="{("2 12" if d.get("dashed") else "0")}"/>')
    it.append(svg("".join(lines)))
    for x, y, lab, kind in nodes:
        if kind == "hub":
            it.append(box(x - 80, y - 80, 160, 160, 80, top="#0a0a0a", front="#1c1c1c", side="#2a2a2a", border=False, inner=f'<div class="hubt" style="font-size:24px">{E(lab)}</div>'))
        else:
            hot = kind == "hot"
            it.append(box(x - 42, y - 42, 84, 84, 26, top=(c if hot else "#ffffff"), border=not hot))
            it.append(bb(x, y, 60, f'<div class="score{" win" if hot else ""}" style="font-size:24px;{"background:" + c + ";border-color:" + c if hot else ""}">{E(lab)}</div>'))
    it.append(bb(540, 720, 20, tag(d["tag"])))
    return it


def s_dash(c, d):
    cards = "".join(f'<div class="dc"><div class="dth" style="background:{["#0a0a0a", c, "#ededeb"][i % 3]}"></div><div class="mono s1">{E(t)}</div><b class="mono" style="color:{c if s == d.get("ready", "READY") else "#0a0a0a"}">{E(s)}</b></div>' for i, (t, s) in enumerate(d["cards"]))
    it = [box(80, 140, 720, 560, 26, top="#ffffff", inner=f'<div class="dash"><div class="mono dh">{E(d["file"])}</div><div class="dgrid">{cards}</div></div>'), bb(520, 100, 270, tag(d["tag"], color=c))]
    if d.get("coin"):
        it.append(coin(780, 680, 60, 150, d["coin"], 14))
    return it


def s_clock(c, d):
    marks = "".join(f'<rect x="248" y="34" width="4" height="22" fill="#0a0a0a" transform="rotate({k * 30} 250 250)"/>' for k in range(12))
    slots = "".join(f'<circle cx="{250 + 190 * __import__("math").sin(__import__("math").radians(h * 30))}" cy="{250 - 190 * __import__("math").cos(__import__("math").radians(h * 30))}" r="22" fill="{c}"/>' for h in d["hours"])
    dial = f'<svg viewBox="0 0 500 500" class="gauge"><circle cx="250" cy="250" r="232" fill="#fff" stroke="#0a0a0a" stroke-width="5"/>{marks}{slots}<rect x="246" y="110" width="8" height="145" rx="4" fill="#0a0a0a" transform="rotate(210 250 250)"/><rect x="246" y="70" width="5" height="185" rx="3" fill="#E8322B" transform="rotate(20 250 250)"/><circle cx="250" cy="250" r="16" fill="#0a0a0a"/></svg>'
    it = [box(250, 520, 360, 140, 60, top="#0a0a0a", front="#1c1c1c", side="#2a2a2a", border=False), bb(430, 590, 60, dial)]
    for k, t in enumerate(d["chips"]):
        it.append(bb(780, 330 + k * 120, 120, f'<div class="chip"><span style="background:{c}">✓</span>{E(t)}</div>'))
    return it


def s_terminal(c, d):
    cols = {"RETRY": "#E6B800", "ERROR": "#FF3B30", "FIXED": "#34C759", "DONE": "#ffffff", "POSTED": "#ffffff", "QUEUED": "#32ADE6"}
    rows = "".join(f'<div class="lg"><span class="lt">{t}</span><span style="color:{cols.get(k, "#fff")}">{k}</span>{E(m)}</div>' for t, k, m in d["log"])
    it = [box(100, 160, 660, 400, 40, top="#0a0a0a", front="#1c1c1c", side="#2a2a2a", inner=f'<div class="term mono">{rows}</div>', border=False),
          svg('<circle cx="430" cy="700" r="130" fill="none" stroke="#34C759" stroke-width="10" stroke-dasharray="40 18"/><path d="M552 650 l18 52 l-52 -10" fill="none" stroke="#34C759" stroke-width="10" stroke-linejoin="round"/>'),
          bb(430, 700, 60, tag(d["tag"]))]
    return it


SCENES = {"stack": s_stack, "float": s_float, "gate": s_gate, "bars": s_bars, "doc": s_doc, "versus": s_versus, "wave": s_wave, "browser": s_browser, "phone": s_phone,
          "layers": s_layers, "qa": s_qa, "sound": s_sound, "thread": s_thread, "gauge": s_gauge, "monitor": s_monitor, "sheet": s_sheet, "network": s_network, "dash": s_dash,
          "clock": s_clock, "terminal": s_terminal}
PLACE = {"bars": (965, 1.0), "wave": (935, 1.06), "sound": (935, 1.06), "gate": (930, 1.04), "stack": (930, 1.04), "float": (920, 1.08), "layers": (900, 0.98), "thread": (900, 1.02),
         "gauge": (960, 0.95), "versus": (930, 1.05), "network": (905, 1.05), "clock": (920, 1.02)}


# ---------------------------------------------------------------- ads
def ad_comment(c, a, platform):
    box_ui = (f'<div class="cbox"><span class="cav"></span><span class="ctx">{E(a["word"])}</span><span class="ccur"></span><span class="mono csend">{"REPLY" if platform == "x" else "POST"}</span></div>')
    it = [card(90, 330, 680, 170, 120, box_ui, thick=22), coin(690, 160, 80, 200, a.get("coin", platform), 16),
          bb(250, 330, 200, '<div class="heart">♥</div>'), bb(560, 380, 230, '<div class="heart s">♥</div>'), bb(430, 640, 40, tag(a["tag"]))]
    return plane("".join(it), 860, 860, 540, 1010, scale=1.1), False


def ad_discord(c, a, platform):
    it = [box(330, 520, 200, 200, 40, top="#2b2b2b", front="#1e1e1e", side="#161616", border=False), coin(430, 620, 50, 360, a.get("coin", "discord"), 22),
          bb(660, 480, 300, f'<div class="sticker">{E(a.get("sticker", "FREE"))}</div>'), bb(430, 840, 10, f'<div class="tag white">{E(a.get("badge", "LINK IN BIO"))}</div>')]
    return plane("".join(it), 860, 860, 540, 1075, scale=1.08, grid=False), True


def ad_dm(c, a, platform):
    me_bg = {"instagram": "#E1306C", "x": "#1D9BF0", "tiktok": "#FE2C55", "linkedin": "#0A66C2", "youtube": "#FF0000"}.get(platform, c)
    phone = (f'<div class="ph"><div class="phb mono">{"DIRECT" if platform == "instagram" else "MESSAGES"}</div><div class="bub you">{a["you"]}</div><div class="bub me" style="background:{me_bg}">{E(a["word"])}</div>'
             f'<div class="bub you sm">{E(a.get("reply", "sending it now"))}</div></div>')
    it = [card(220, 90, 420, 700, 90, phone, bg="#0a0a0a", thick=24), coin(140, 720, 50, 170, platform, 16), bb(690, 520, 200, f'<div class="fbtn mono">{E(a.get("button", "FOLLOW FIRST"))}</div>')]
    return plane("".join(it), 860, 860, 540, 1010, scale=1.02), False


def ad_save(c, a, platform):
    it = [card(170, 140, 520, 560, 60, f'<div class="savec"><div class="mono s1">{E(a["file"])}</div>' + "".join(f'<div class="ckl"><span style="background:{c}">✓</span>{E(t)}</div>' for t in a["items"]) + "</div>", thick=18),
          bb(690, 200, 300, '<svg class="bmk" viewBox="0 0 24 24"><path d="M6 3h12v18l-6-4.5L6 21z" fill="#0a0a0a"/></svg>'), coin(160, 690, 60, 170, platform, 16), bb(560, 800, 20, tag(a["tag"]))]
    return plane("".join(it), 860, 860, 540, 1000, scale=1.04), False


ADS = {"comment": ad_comment, "discord": ad_discord, "dm": ad_dm, "save": ad_save}


# ---------------------------------------------------------------- slides
def frame(n, total, label, inner, dark=False):
    prog = n / total * 100
    return f'''<section class="slide{' dark' if dark else ''}" id="s{n}">{inner}
  <div class="top"><span class="mono">{n:02d} / {total}</span><span class="mono">{E(label)}</span></div>
  <div class="foot"><div class="bar"><div class="fill" style="width:{prog:.1f}%"></div></div><span class="mono">{'SAVE THIS' if n == total else 'SWIPE'}</span><svg class="arr" viewBox="0 0 24 24"><path d="M4 12h15M13 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></div>
</section>'''


def build(content, out):
    os.makedirs(out + "/slides", exist_ok=True)
    steps, ads, label = content["steps"], content["ads"], content["label"]
    order, si = [], 0
    total = len(steps) + len(ads) + 1
    for n in range(1, total + 1):
        if n == 1:
            order.append(("cover", None))
        elif n in ads:
            order.append(("ad", ads[n]))
        else:
            order.append(("step", si)); si += 1
    assert si == len(steps), (si, len(steps))
    slides = []
    for n, (kind, p) in enumerate(order, 1):
        if kind == "cover":
            slides.append(frame(n, total, label, content["cover"]()))
        elif kind == "ad":
            sc, dark = ADS[p["kind"]](content["accent"], p, content["platform"])
            klass = "adt" if dark else "adt b"
            slides.append(frame(n, total, label, sc + f'<h2 class="{klass}">{p["title"]}</h2><p class="{klass.replace("adt", "adp")}">{E(p["line"])}</p>', dark=dark))
        else:
            s = steps[p]
            items = SCENES[s["scene"]](s["color"], s["data"])
            cy, scl = PLACE.get(s["scene"], (890, 1.1))
            sc = plane("".join(items), 860, 860, 540, cy, scale=scl)
            head = f'<div class="stag mono"><i style="background:{s["color"]}"></i>STEP {p + 1:02d} · {E(s["label"])}</div>'
            slides.append(frame(n, total, label, sc + f'<div class="hd">{head}<h2 class="st">{E(s["title"])}</h2><p class="sp">{E(s["line"])}</p></div><div class="tools mono">{E(s["tools"])}</div>'))
    doc = f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{''.join(slides)}</body></html>"
    if chr(0x2014) in doc:
        raise SystemExit("em dash in the slides")
    open(out + "/carousel.html", "w", encoding="utf-8", newline="\n").write(doc)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit("Playwright is missing: run  python -m pip install playwright  and then  python -m playwright install chromium")
    cols, w, h, gap = 6, 360, 480, 24
    rows = (total + cols - 1) // cols
    tiles = "".join(f'<img src="{(Path(out) / "slides" / f"slide-{n:02d}.png").resolve().as_uri()}" style="position:absolute;left:{((n - 1) % cols) * (w + gap) + gap}px;top:{((n - 1) // cols) * (h + gap) + gap}px;width:{w}px;height:{h}px">' for n in range(1, total + 1))
    Wd, Hd = cols * (w + gap) + gap, rows * (h + gap) + gap
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1440})
        pg.goto((Path(out) / "carousel.html").resolve().as_uri())
        pg.evaluate("document.fonts.ready.then(() => true)")
        time.sleep(0.8)
        pg.evaluate(FIT_JS)
        for n in range(1, total + 1):
            pg.locator(f"#s{n}").screenshot(path=f"{out}/slides/slide-{n:02d}.png")
        sheet = Path(out) / "sheet.html"
        sheet.write_text(f"<!doctype html><html><body style='margin:0;background:#E7E7E5;width:{Wd}px;height:{Hd}px;position:relative'>{tiles}</body></html>", encoding="utf-8")
        pg2 = b.new_page(viewport={"width": Wd, "height": Hd})
        pg2.goto(sheet.resolve().as_uri())
        pg2.wait_for_load_state("load")
        pg2.screenshot(path=f"{out}/sheet.png")
        b.close()
    sheet.unlink()
    print(f"{total} slides and sheet.png in {out}")


# the scene shrinks toward the bottom when the header runs longer than a one-line title and a two-line paragraph (measured, never guessed)
FIT_JS = """() => { document.querySelectorAll('section.slide').forEach(function (sec) {
  var hd = sec.querySelector('.hd'), st = sec.querySelector('.stage'); if (!hd || !st) return;
  var shift = hd.getBoundingClientRect().bottom - sec.getBoundingClientRect().top - 380;
  if (shift > 2) { st.style.transformOrigin = '540px 1280px'; st.style.transform = 'scale(' + ((880 - shift) / 880) + ')'; }
}); return true; }"""

CSS = f"""
@font-face {{ font-family: Inter; src: url("{FONTS}Inter-Variable.ttf"); font-weight: 100 900; }}
@font-face {{ font-family: Plex; src: url("{FONTS}IBMPlexMono-Medium.ttf"); font-weight: 500; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ background: #ccc; font-family: Inter, sans-serif; color: #0a0a0a; }}
.slide {{ position: relative; width: 1080px; height: 1440px; background: #fff; overflow: hidden; margin-bottom: 20px; }}
.slide.dark {{ background: #0a0a0a; color: #fff; }}
.mono {{ font-family: Plex, monospace; font-weight: 500; letter-spacing: .2em; text-transform: uppercase; }}
.top {{ position: absolute; left: 60px; right: 60px; top: 48px; display: flex; justify-content: space-between; font-size: 17px; opacity: .55; z-index: 5; }}
.foot {{ position: absolute; left: 60px; right: 60px; bottom: 44px; display: flex; align-items: center; gap: 20px; font-size: 17px; z-index: 5; }}
.bar {{ flex: 1; height: 3px; background: rgba(10,10,10,.12); border-radius: 2px; overflow: hidden; }} .dark .bar {{ background: rgba(255,255,255,.2); }}
.fill {{ height: 100%; background: currentColor; }} .arr {{ width: 28px; height: 28px; }}
.inv {{ background: #0a0a0a; color: #fff; padding: 0 .12em; border-radius: 10px; line-height: 1; box-decoration-break: clone; -webkit-box-decoration-break: clone; }}
.inv.w {{ background: #fff; color: #0a0a0a; }}
.stage {{ position: absolute; inset: 0; z-index: 1; }}
.plane {{ position: absolute; transform-style: preserve-3d; transform-origin: 50% 50%; }}
.plane.grid {{ background-image: linear-gradient(rgba(10,10,10,.07) 1.5px, transparent 1.5px), linear-gradient(90deg, rgba(10,10,10,.07) 1.5px, transparent 1.5px); background-size: 43px 43px; }}
.b3 {{ position: absolute; transform-style: preserve-3d; }}
.f {{ position: absolute; backface-visibility: visible; overflow: hidden; }}
.sh {{ position: absolute; border-radius: 4px; }}
.psvg {{ position: absolute; left: 0; top: 0; overflow: visible; }}
.bb {{ position: absolute; transform-origin: 0 0; white-space: nowrap; }}
.coin {{ border-radius: 50%; display: flex; align-items: center; justify-content: center; }}
.csh {{ position: absolute; border-radius: 50%; background: rgba(10,10,10,.13); }}
.fcoin {{ position: absolute; right: 30px; top: 96px; z-index: 4; transform: rotate(-8deg) scale(.86); transform-origin: 100% 0; }}
.csh2 {{ position: absolute; left: 30px; top: 210px; width: 190px; height: 60px; border-radius: 50%; background: rgba(10,10,10,.12); }}
.ci {{ display: inline-flex; width: 44px; height: 44px; border-radius: 50%; align-items: center; justify-content: center; }} .ci svg {{ width: 60%; height: 60%; }}
.tag {{ font-family: Plex, monospace; font-weight: 500; font-size: 22px; letter-spacing: .16em; padding: 14px 20px; border-radius: 12px; background: #fff; border: 2px solid #0a0a0a; }}
.tag.dark {{ background: #0a0a0a; color: #fff; }} .tag.red {{ background: #E8322B; color: #fff; border-color: #E8322B; }} .tag.light {{ background: #fff; color: #0a0a0a; }}
.tag.white {{ background: #fff; color: #0a0a0a; border: none; font-size: 28px; padding: 18px 30px; border-radius: 40px; }}
.cover-t {{ position: absolute; left: 60px; top: 104px; font-weight: 850; font-size: 100px; letter-spacing: -.05em; line-height: 1.1; z-index: 4; }}
.cover-s {{ position: absolute; left: 62px; top: 460px; font-size: 19px; opacity: .6; z-index: 4; }}
.nlab {{ display: flex; align-items: center; gap: 12px; height: 100%; padding-left: 18px; font-family: Plex, monospace; font-size: 21px; letter-spacing: .1em; white-space: nowrap; }}
.nlab i {{ width: 20px; height: 20px; border-radius: 50%; display: block; flex: none; }}
.hubt {{ color: #fff; font-weight: 850; font-size: 32px; letter-spacing: -.02em; display: flex; align-items: center; justify-content: center; height: 100%; text-align: center; }}
.hd {{ position: absolute; left: 60px; right: 60px; top: 128px; z-index: 5; }}
.stag {{ font-size: 21px; display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }} .stag i {{ width: 18px; height: 18px; border-radius: 50%; display: block; }}
.st {{ margin-left: -2px; font-weight: 850; font-size: 108px; letter-spacing: -.05em; line-height: .95; margin-bottom: 22px; }}
.sp {{ padding-right: 60px; font-size: 33px; font-weight: 600; line-height: 1.26; letter-spacing: -.012em; }}
.tools {{ position: absolute; left: 60px; bottom: 100px; font-size: 17px; opacity: .55; z-index: 4; }}
.qrow {{ display: flex; align-items: center; gap: 22px; height: 100%; padding: 0 26px; font-weight: 750; font-size: 30px; letter-spacing: -.015em; white-space: nowrap; }}
.qrow .mono {{ font-size: 17px; opacity: .55; min-width: 70px; }} .qrow.inv2 {{ color: #fff; }} .qrow.inv2 .mono {{ opacity: 1; }}
.srcc {{ padding: 22px; }} .srcc b {{ display: inline-block; color: #fff; font-family: Plex, monospace; font-weight: 500; font-size: 22px; padding: 8px 12px; border-radius: 9px; }}
.srcc .u {{ font-size: 15px; letter-spacing: .06em; opacity: .55; margin: 16px 0 6px; text-transform: none; }} .srcc .t {{ font-weight: 800; font-size: 34px; letter-spacing: -.02em; }}
.fold {{ color: #fff; font-weight: 850; font-size: 40px; letter-spacing: -.02em; padding: 40px 30px; line-height: 1.1; }} .fold small {{ font-family: Plex, monospace; font-weight: 500; font-size: 17px; letter-spacing: .18em; opacity: .7; }}
.gc {{ display: flex; align-items: center; justify-content: center; height: 100%; font-size: 52px; font-weight: 900; }} .gc.ok {{ color: #34C759; }} .gc.no {{ color: #E8322B; }}
.score {{ font-weight: 850; font-size: 46px; letter-spacing: -.03em; background: #fff; border: 2px solid #0a0a0a; border-radius: 14px; padding: 6px 14px; }} .score.win {{ color: #fff; }}
.hlb.sm {{ font-size: 15px; padding: 6px 9px; }} .score.sm {{ font-size: 30px; padding: 3px 9px; }}
.hlb {{ font-weight: 800; font-size: 21px; letter-spacing: -.01em; background: #fff; border: 2px solid #0a0a0a; border-radius: 12px; padding: 9px 13px; }} .hlb.w {{ color: #fff; }}
.docp {{ padding: 40px 36px; }} .dh {{ font-size: 18px; opacity: .55; margin-bottom: 30px; }} .dl {{ height: 16px; background: #e6e6e4; border-radius: 8px; margin-bottom: 30px; }}
.chip {{ display: flex; align-items: center; gap: 14px; background: #fff; border: 2px solid #0a0a0a; border-radius: 40px; padding: 12px 22px 12px 12px; font-family: Plex, monospace; font-size: 21px; letter-spacing: .1em; }}
.chip span {{ width: 40px; height: 40px; border-radius: 50%; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 22px; font-family: Inter; font-weight: 900; }}
.s1 {{ font-size: 15px; opacity: .55; margin-bottom: 4px; }} .s2 {{ font-size: 25px; font-weight: 750; letter-spacing: -.015em; white-space: normal; }} .s3 {{ font-size: 21px; font-weight: 650; }}
.wt {{ background: #fff; border: 2px solid #0a0a0a; border-radius: 14px; padding: 12px 18px; font-weight: 850; font-size: 34px; letter-spacing: -.02em; text-align: center; }} .wt small {{ display: block; font-size: 14px; letter-spacing: .1em; opacity: .55; }}
.bw {{ height: 100%; }} .bwb {{ height: 62px; background: #f1f1ef; display: flex; align-items: center; gap: 10px; padding: 0 22px; border-bottom: 2px solid rgba(10,10,10,.12); }}
.bwb i {{ width: 16px; height: 16px; border-radius: 50%; background: #cfcfcd; display: block; }} .bwb span {{ font-size: 18px; letter-spacing: .06em; margin-left: 14px; opacity: .6; text-transform: none; }}
.bwc {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 22px; padding: 36px; }}
.pc {{ height: 340px; border: 2px solid rgba(10,10,10,.15); border-radius: 18px; padding: 24px; display: flex; flex-direction: column; justify-content: space-between; }}
.pc b {{ font-family: Plex, monospace; font-weight: 500; font-size: 20px; letter-spacing: .14em; }} .pc span {{ font-weight: 850; font-size: 46px; letter-spacing: -.04em; white-space: normal; line-height: 1; }} .pc.hl {{ border-width: 6px; }}
.cursor {{ width: 110px; height: 110px; }}
.vsw {{ display: flex; flex-direction: column; align-items: center; gap: 16px; }}
.vs {{ font-weight: 900; font-size: 110px; letter-spacing: -.05em; background: #fff; border: 3px solid #0a0a0a; border-radius: 22px; padding: 0 26px; }}
.phs {{ height: 100%; padding: 26px 22px; color: #fff; }} .phh {{ font-size: 18px; opacity: .6; margin-bottom: 18px; }}
.rgrid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }} .rg {{ aspect-ratio: 9/16; border-radius: 6px; position: relative; }} .rg span {{ position: absolute; left: 6px; bottom: 6px; font-size: 11px; color: #fff; mix-blend-mode: difference; }}
.pv {{ height: 300px; border-radius: 14px; margin-bottom: 18px; }} .cap {{ font-size: 20px; font-weight: 600; opacity: .8; margin-bottom: 10px; white-space: normal; }} .cap.b {{ font-weight: 850; font-size: 26px; opacity: 1; }}
.lay {{ position: relative; height: 100%; }} .lay.paper {{ background-image: radial-gradient(rgba(10,10,10,.18) 2px, transparent 2px); background-size: 36px 36px; }}
.lc {{ position: absolute; width: 200px; height: 140px; border: 2px solid #0a0a0a; border-radius: 16px; background: #fff; }}
.lt2 {{ position: absolute; left: 40px; top: 210px; font-weight: 850; font-size: 60px; letter-spacing: -.04em; }}
.lcap {{ position: absolute; left: 40px; bottom: 60px; font-weight: 850; font-size: 50px; letter-spacing: -.03em; }} .lcap b {{ color: #fff; padding: 0 10px; border-radius: 8px; }}
.masc {{ position: absolute; right: 60px; top: 60px; width: 110px; height: 110px; border-radius: 22px; }}
.perf {{ height: 100%; border-left: 8px dotted rgba(127,127,127,.5); border-right: 8px dotted rgba(127,127,127,.5); }}
.qcard {{ padding: 36px 34px; }} .qcard.up {{ background: #fff; border: 2px solid #0a0a0a; border-radius: 22px; width: 520px; box-shadow: 14px 14px 0 rgba(10,10,10,.12); }}
.qr {{ display: grid; grid-template-columns: 120px repeat(5, 1fr); gap: 12px; align-items: center; margin-bottom: 22px; }} .qr .mono {{ font-size: 18px; }} .qr i {{ height: 30px; border-radius: 8px; display: block; }}
.flag {{ color: #fff; font-family: Plex, monospace; font-size: 20px; letter-spacing: .14em; padding: 10px 14px; border-radius: 10px; }}
.tw {{ display: flex; gap: 18px; align-items: center; height: 100%; padding: 0 22px; }} .tw.m {{ color: #fff; }} .tav {{ width: 54px; height: 54px; border-radius: 50%; background: #d9d9d7; flex: none; }} .tw.m .tav {{ background: #fff; }}
.gwrap {{ display: flex; flex-direction: column; align-items: center; gap: 18px; }} .grow {{ display: flex; gap: 14px; }}
.gauge {{ width: 420px; height: 420px; display: block; filter: drop-shadow(14px 14px 0 rgba(10,10,10,.12)); }}
.mon {{ position: relative; height: 100%; overflow: hidden; background: #0a0a0a; }} .mgrid {{ position: absolute; left: 30px; right: 30px; top: 70px; bottom: 60px; display: grid; grid-template-columns: repeat(16, 1fr); gap: 6px; }} .mgrid i {{ display: block; border-radius: 4px; }} .monup {{ width: 600px; height: 370px; border: 18px solid #1a1a1a; border-radius: 26px; background: #0a0a0a; box-shadow: 0 16px 0 #2a2a2a, 18px 26px 0 rgba(10,10,10,.14); overflow: hidden; }}
.rec {{ position: absolute; left: 24px; top: 20px; color: #fff; font-size: 18px; display: flex; gap: 10px; align-items: center; }} .rec b {{ width: 14px; height: 14px; border-radius: 50%; background: #E8322B; display: block; }}
.stat {{ position: absolute; left: 24px; bottom: 20px; color: #fff; font-size: 16px; opacity: .8; }}
.sheet {{ padding: 30px 30px; }} .sr {{ display: flex; align-items: center; gap: 16px; padding: 16px 0; border-bottom: 2px solid rgba(10,10,10,.08); }} .st2 {{ flex: 1; }}
.ob {{ color: #fff; font-size: 14px; letter-spacing: .1em; padding: 10px 12px; border-radius: 10px; white-space: nowrap; }}
.bignum {{ color: #fff; font-weight: 900; font-size: 96px; letter-spacing: -.05em; padding: 6px 26px; border-radius: 20px; }}
.dash {{ padding: 30px; }} .dgrid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; }} .dc {{ border: 2px solid rgba(10,10,10,.14); border-radius: 16px; padding: 14px; }}
.dth {{ height: 150px; border-radius: 10px; margin-bottom: 12px; }} .dc b {{ font-size: 16px; letter-spacing: .14em; }}
.term {{ padding: 40px; font-size: 25px; letter-spacing: .02em; text-transform: none; color: #fff; }} .lg {{ padding: 14px 0; display: flex; gap: 18px; }} .lt {{ opacity: .5; }}
.adt {{ position: absolute; left: 60px; right: 60px; top: 140px; font-weight: 850; font-size: 94px; letter-spacing: -.05em; line-height: 1.12; z-index: 4; }}
.adp {{ position: absolute; left: 62px; right: 120px; top: 560px; font-size: 34px; font-weight: 600; line-height: 1.28; opacity: .75; z-index: 4; }}
.adt.b, .adp.b {{ color: #0a0a0a; }}
.sticker {{ background: #fff; color: #0a0a0a; font-weight: 900; font-size: 64px; letter-spacing: -.03em; padding: 10px 28px; border-radius: 16px; transform: rotate(-8deg); }}
.cbox {{ display: flex; align-items: center; gap: 24px; height: 100%; padding: 0 34px; }} .cav {{ width: 80px; height: 80px; border-radius: 50%; background: #e6e6e4; flex: none; }}
.ctx {{ font-weight: 850; font-size: 56px; letter-spacing: -.02em; }} .ccur {{ width: 4px; height: 60px; background: #0a0a0a; }} .csend {{ margin-left: auto; font-size: 26px; color: #007AFF; letter-spacing: .14em; }}
.heart {{ color: #FF2D55; font-size: 90px; line-height: 1; }} .heart.s {{ font-size: 60px; }}
.ph {{ height: 100%; padding: 30px 26px; display: flex; flex-direction: column; gap: 22px; }} .phb {{ color: #fff; font-size: 20px; opacity: .6; margin-bottom: 20px; }}
.bub {{ max-width: 86%; font-size: 30px; font-weight: 700; padding: 22px 26px; border-radius: 28px; letter-spacing: -.01em; white-space: normal; }}
.bub.you {{ background: #262626; color: #fff; border-bottom-left-radius: 8px; align-self: flex-start; }} .bub.sm {{ font-size: 24px; }}
.bub.me {{ color: #fff; align-self: flex-end; border-bottom-right-radius: 8px; font-weight: 850; letter-spacing: .06em; }}
.fbtn {{ background: #0a0a0a; color: #fff; font-size: 26px; padding: 20px 40px; border-radius: 40px; letter-spacing: .26em; }}
.savec {{ padding: 40px 36px; }} .ckl {{ display: flex; align-items: center; gap: 16px; font-weight: 750; font-size: 30px; padding: 16px 0; border-bottom: 2px solid rgba(10,10,10,.08); white-space: normal; }}
.ckl span {{ width: 40px; height: 40px; border-radius: 10px; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 22px; font-weight: 900; flex: none; }}
.bmk {{ width: 150px; height: 150px; filter: drop-shadow(12px 12px 0 rgba(10,10,10,.12)); }}
"""
