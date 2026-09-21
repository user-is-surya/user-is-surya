"""All SVG art for the profile. Pure SVG + SMIL (no scripts, no external requests),
which is what GitHub allows inside <img> tags. Nothing here needs editing day to day:
change things in profile.toml instead."""
import math, random
from datetime import date
from xml.sax.saxutils import escape

FONT = "'JetBrains Mono','Fira Code','Cascadia Code','SF Mono',Menlo,Consolas,'Liberation Mono','DejaVu Sans Mono',monospace"
RED, HOT = "#E10600", "#FF2A1A"
INK, PANEL, LINE = "#0A0B0D", "#15161A", "#2A2C31"
TXT, DIM = "#E6E7EA", "#8B8F97"
GREEN, PURPLE, YEL, BLUE = "#00D26A", "#B138DD", "#FFC400", "#5B9DFF"
CW = 0.6  # monospace advance, in em
# accent -> (main, secondary, bright)
ACCENTS = {"red": (RED, PURPLE, HOT), "purple": (PURPLE, RED, "#C86BEA"), "green": (GREEN, BLUE, "#3DFF9A"),
           "blue": (BLUE, PURPLE, "#8DBBFF"), "yellow": (YEL, RED, "#FFD84D")}
HEAT = ["#17191D", "#5A0F0C", "#9B0F0A", RED, "#FF5A48"]
LANG_COLORS = [RED, PURPLE, YEL, BLUE, GREEN, "#FF8A3D", DIM]


# ---------------------------------------------------------------- helpers
def f(n):
    return ("%.2f" % n).rstrip("0").rstrip(".")


def fk(n):
    return ("%.5f" % n).rstrip("0").rstrip(".") or "0"


def clean(s):
    """Keep text on the monospace grid: drop emoji / control chars, collapse whitespace."""
    s = "".join(ch for ch in str(s) if (ch >= " " and ord(ch) < 0x2000) or ch == "\u2026")
    return " ".join(s.split())


def clip(s, n):
    s = clean(s)
    return s if len(s) <= n else s[: n - 1].rstrip() + "\u2026"


def grid_text(segments, x, y, fs, extra=""):
    """Every glyph sits on a fixed grid so the layout is identical in any monospace font."""
    cw, i, out = fs * CW, 0, []
    for s, fill in segments:
        xs, chars = [], []
        for k, ch in enumerate(s):
            if ch != " ":
                xs.append(f(x + (i + k) * cw))
                chars.append(ch)
        i += len(s)
        if chars:
            out.append(f'<text x="{" ".join(xs)}" y="{f(y)}" font-size="{fs}" fill="{fill}" {extra}>{escape("".join(chars))}</text>')
    return "\n".join(out)


def discrete(attr, pairs, T, extra=""):
    pairs = sorted(pairs, key=lambda p: p[0])
    times = [p[0] for p in pairs]
    vals = [str(p[1]) for p in pairs]
    assert times[0] == 0, pairs[:2]
    times.append(T)
    vals.append(vals[-1])
    for a, b in zip(times, times[1:]):
        assert b > a, (a, b)
    kt = ";".join(fk(t / T) if t < T else "1" for t in times)
    return (f'<animate attributeName="{attr}" calcMode="discrete" values="{";".join(vals)}" '
            f'keyTimes="{kt}" dur="{f(T)}s" repeatCount="indefinite"{extra}/>')


def svg(w, h, body, defs, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{escape(title)}" font-family="{FONT}">\n<title>{escape(title)}</title>\n'
            f'<defs>{defs}</defs>\n{body}\n</svg>\n')


def ago(iso):
    from datetime import datetime, timezone
    try:
        t = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except Exception:
        return ""
    s = max(0, (datetime.now(timezone.utc) - t).total_seconds())
    for div, unit in ((60, "s"), (60, "m"), (24, "h"), (7, "d"), (4.345, "w"), (12, "mo"), (1e9, "y")):
        if s < div:
            return "just now" if unit == "s" and s < 45 else f"{int(s)}{unit} ago"
        s /= div
    return ""


CARBON_DEFS = '''<pattern id="cf" width="8" height="8" patternUnits="userSpaceOnUse">
<rect width="8" height="8" fill="#0F1012"/><rect width="4" height="4" fill="#16181B"/><rect x="4" y="4" width="4" height="4" fill="#16181B"/>
<rect x="4" width="4" height="4" fill="#0B0C0E"/><rect y="4" width="4" height="4" fill="#0B0C0E"/></pattern>'''
SWEEP_DEF = '''<linearGradient id="sw" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".9" stop-color="#fff" stop-opacity=".95"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'''


def frame(w, h, rx=12):
    return (f'<rect width="{w}" height="{h}" rx="{rx}" fill="{INK}"/>'
            f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{rx}" fill="none" stroke="{LINE}"/>')


def prompt_segs(handle, cmd):
    return [(f"{handle}@pitwall", GREEN), (":", DIM), ("~", BLUE), ("$", DIM), (" ", DIM), (cmd, TXT)]


# ---------------------------------------------------------------- header
def header(handle, name, lines, alt):
    W, H = 1000, 320
    lines = [clip(l, 46) for l in lines if clean(l)][:5] or [name]
    T = max(12.0, 3.0 * len(lines))
    fs, dt, hold = 20, 0.045, 0.8
    cw = fs * CW
    x0, yt = 48, 252
    xp = x0 + 2 * cw
    t_out = 4.6
    light_on = [0.8 + 0.6 * i for i in range(5)]
    name_fs = 68 if len(name) <= 8 else max(30, int(68 * 8 / len(name)))

    defs = CARBON_DEFS + SWEEP_DEF + f'''
<linearGradient id="sheen" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".07"/><stop offset=".45" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff" stop-opacity=".03"/></linearGradient>
<filter id="glow" x="-150%" y="-150%" width="400%" height="400%"><feGaussianBlur stdDeviation="7"/></filter>
<clipPath id="round"><rect width="{W}" height="{H}" rx="16"/></clipPath>'''

    p = ['<g clip-path="url(#round)">',
         f'<rect width="{W}" height="{H}" fill="url(#cf)"/><rect width="{W}" height="{H}" fill="url(#sheen)"/>',
         f'<rect width="{W}" height="40" fill="{INK}" opacity=".88"/><rect y="40" width="{W}" height="1" fill="{LINE}"/>',
         f'<circle cx="28" cy="20" r="6" fill="{RED}"/><circle cx="48" cy="20" r="6" fill="{YEL}"/><circle cx="68" cy="20" r="6" fill="{GREEN}"/>',
         f'<text x="500" y="25" font-size="13" fill="{DIM}" text-anchor="middle">{escape(handle)}@pitwall: ~</text>',
         grid_text(prompt_segs(handle, "whoami"), x0, 84, 16)]
    for dx, col, dly in ((6, RED, 0), (-6, PURPLE, 0.12)):
        anim = discrete("opacity", [(0, 0), (t_out + dly, 1), (t_out + dly + .08, 0), (t_out + dly + .16, 1), (t_out + dly + .24, 0)], T)
        p.append(f'<text transform="translate({x0 + dx},158) skewX(-8)" font-size="{name_fs}" font-weight="800" fill="{col}" opacity="0">{escape(name)}{anim}</text>')
    p.append(f'<text transform="translate({x0},158) skewX(-8)" font-size="{name_fs}" font-weight="800" fill="{TXT}">{escape(name)}</text>')
    p.append(grid_text(prompt_segs(handle, "cat now.txt"), x0, 206, 16))
    p.append(grid_text([(">", HOT)], x0, yt, fs))

    events = [(0, xp)]
    for li, text in enumerate(lines):
        s = 0.3 + 3.0 * li
        n = len(text)
        e = s + n * dt + hold
        for k, ch in enumerate(text):
            if ch == " ":
                continue
            t_on = s + (k + 1) * dt
            p.append(f'<text x="{f(xp + k * cw)}" y="{yt}" font-size="{fs}" fill="{TXT}" opacity="0">{escape(ch)}'
                     f'{discrete("opacity", [(0, 0), (t_on, 1), (e, 0)], T)}</text>')
        for k in range(n + 1):
            events.append((s + k * dt if k else s, xp + k * cw))
        events.append((e, xp))
    dedup, last = [], -1
    for t, x in events:
        if t > last:
            dedup.append((t, f(x)))
            last = t
    p.append(f'<rect x="{f(xp)}" y="{yt - 17}" width="{f(cw * .6)}" height="22" fill="{HOT}">{discrete("x", dedup, T)}'
             f'<animate attributeName="opacity" calcMode="discrete" values="1;0" keyTimes="0;.5" dur="1s" repeatCount="indefinite"/></rect>')

    gx, gy, gw, gh = 712, 64, 240, 128
    p.append(f'<rect x="{gx}" y="{gy}" width="{gw}" height="{gh}" rx="12" fill="{INK}" stroke="{LINE}"/>')
    for i in range(5):
        cx = 748 + i * 46
        for cy in (104, 152):
            p.append(f'<circle cx="{cx}" cy="{cy}" r="22" fill="{HOT}" opacity="0" filter="url(#glow)">'
                     f'{discrete("opacity", [(0, 0), (light_on[i], .75), (t_out, 0)], T)}</circle>')
            p.append(f'<circle cx="{cx}" cy="{cy}" r="16" fill="#2A0E0E" stroke="#3D1515">'
                     f'{discrete("fill", [(0, "#2A0E0E"), (light_on[i], HOT), (t_out, "#2A0E0E")], T)}</circle>')
    cap_x = gx + gw / 2
    p.append(f'<text x="{f(cap_x)}" y="218" font-size="14" fill="{DIM}" text-anchor="middle">on the grid'
             f'{discrete("opacity", [(0, 1), (t_out, 0), (9.0, 1)], T)}</text>')
    p.append(f'<text x="{f(cap_x)}" y="218" font-size="14" fill="{GREEN}" text-anchor="middle" opacity="0">lights out and away we go'
             f'{discrete("opacity", [(0, 0), (t_out, 1), (9.0, 0)], T)}</text>')

    p.append(f'<rect y="288" width="{W}" height="6" fill="{RED}"/><rect y="298" width="{W}" height="2" fill="{TXT}" opacity=".8"/>')
    a, b = t_out / T, (t_out + 1.3) / T
    p.append(f'<rect x="0" y="286" width="260" height="16" fill="url(#sw)" opacity=".9">'
             f'<animateTransform attributeName="transform" type="translate" values="-260 0;-260 0;1060 0;1060 0" '
             f'keyTimes="0;{fk(a)};{fk(b)};1" dur="{f(T)}s" repeatCount="indefinite"/></rect>')
    p.append('</g>')
    p.append(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="none" stroke="{LINE}"/>')
    return svg(W, H, "\n".join(p), defs, alt)


# ---------------------------------------------------------------- section titles + footer
def section(handle, cmd, label):
    W, H, fs = 1000, 56, 20
    cw = fs * CW
    x, y = 44, 36
    segs = prompt_segs(handle, "ls " + cmd)
    n = sum(len(s) for s, _ in segs)
    xend = x + n * cw
    xl, R = xend + 44, W - 20
    defs = f'''<linearGradient id="car" x1="0" x2="1"><stop offset="0" stop-color="{RED}" stop-opacity="0"/><stop offset=".85" stop-color="{HOT}"/><stop offset="1" stop-color="#fff"/></linearGradient>
<clipPath id="lane"><rect x="{f(xl)}" y="20" width="{f(R - xl)}" height="18"/></clipPath>'''
    body = [frame(W, H, 10), f'<polygon points="24,10 32,10 24,46 16,46" fill="{RED}"/>', grid_text(segs, x, y, fs),
            f'<rect x="{f(xend + 3)}" y="{y - 17}" width="{f(cw * .6)}" height="22" fill="{HOT}">'
            f'<animate attributeName="opacity" calcMode="discrete" values="1;0" keyTimes="0;.5" dur="1s" repeatCount="indefinite"/></rect>',
            f'<rect x="{f(xl)}" y="28" width="{f(R - xl)}" height="1" fill="{LINE}"/>',
            f'<g clip-path="url(#lane)"><rect x="0" y="27" width="110" height="3" fill="url(#car)">'
            f'<animateTransform attributeName="transform" type="translate" from="{f(xl - 110)} 0" to="{R} 0" dur="2.8s" repeatCount="indefinite"/></rect></g>']
    return svg(W, H, "\n".join(body), defs, label)


def footer(handle, text):
    W, H = 1000, 110
    defs = f'''<pattern id="chk" width="20" height="20" patternUnits="userSpaceOnUse"><rect width="10" height="10" fill="{TXT}"/><rect x="10" y="10" width="10" height="10" fill="{TXT}"/></pattern>
<clipPath id="strip"><rect y="10" width="{W}" height="20"/></clipPath>'''
    segs = [(f"{handle}@pitwall", GREEN), (":", DIM), ("~", BLUE), ("$", DIM), (" exit  ", TXT), ("# " + clip(text, 40), DIM)]
    n = sum(len(s) for s, _ in segs)
    body = [frame(W, H),
            f'<g clip-path="url(#strip)" opacity=".92"><g><rect x="-20" y="10" width="{W + 40}" height="20" fill="url(#chk)"/>'
            f'<animateTransform attributeName="transform" type="translate" from="0 0" to="20 0" dur="1.1s" repeatCount="indefinite"/></g></g>',
            f'<rect y="34" width="{W}" height="3" fill="{RED}"/>',
            grid_text(segs, (W - n * 10.8) / 2, 78, 18)]
    return svg(W, H, "\n".join(body), defs, text)


# ---------------------------------------------------------------- project cards
def chips(items, x, y, fs=12, h=22, xmax=466):
    cw, out = fs * CW, []
    for it in items:
        it = clip(it, 14)
        w = len(it) * cw + 18
        if x + w > xmax:
            break
        out.append(f'<rect x="{f(x)}" y="{y}" width="{f(w)}" height="{h}" rx="6" fill="{PANEL}" stroke="#34373D"/>')
        out.append(grid_text([(it, TXT)], x + 9, y + h / 2 + fs * .35, fs))
        x += w + 8
    return "\n".join(out)


def card_base(W, H, accent):
    defs = CARBON_DEFS + SWEEP_DEF + f'''
<clipPath id="cr"><rect width="{W}" height="{H}" rx="14"/></clipPath>
<linearGradient id="top" x1="0" x2="1"><stop offset="0" stop-color="{accent}"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/></linearGradient>'''
    head = (f'<g clip-path="url(#cr)"><rect width="{W}" height="{H}" fill="{INK}"/><rect width="{W}" height="{H}" fill="url(#cf)" opacity=".55"/>'
            f'<rect width="{W}" height="4" fill="url(#top)"/></g>'
            f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="{LINE}"/>')
    return defs, head


def _trace(a1, a2, hot):
    d = "M24,206 L52,206 C70,206 76,176 96,176 L140,176 C156,176 160,214 176,214 L196,214 C214,214 214,182 236,182 L290,182 C306,182 310,204 326,204 L346,204 C364,204 366,172 388,172 L430,172 C446,172 452,188 466,188"
    T = 5.0
    return ("", [
        f'<line x1="24" y1="222" x2="466" y2="222" stroke="{LINE}"/>',
        f'<path d="{d}" transform="translate(0,-8)" fill="none" stroke="{a2}" stroke-width="1.6" opacity=".7" pathLength="1" stroke-dasharray="1 1" stroke-linecap="round" stroke-linejoin="round">'
        f'<animate attributeName="stroke-dashoffset" values="1;1;0;0" keyTimes="0;.06;.86;1" dur="{T}s" repeatCount="indefinite"/></path>',
        f'<path d="{d}" fill="none" stroke="{hot}" stroke-width="2.4" pathLength="1" stroke-dasharray="1 1" stroke-linecap="round" stroke-linejoin="round">'
        f'<animate attributeName="stroke-dashoffset" values="1;0;0" keyTimes="0;.8;1" dur="{T}s" repeatCount="indefinite"/></path>',
        f'<circle r="4.5" fill="#fff"><animateMotion dur="{T}s" repeatCount="indefinite" path="{d}" calcMode="linear" keyPoints="0;1;1" keyTimes="0;.8;1"/></circle>'])


def _equalizer(a1, a2, seed):
    rng = random.Random(seed)
    n, cy, step = 40, 194, 442 / 40
    bars = []
    for i in range(n):
        env = .3 + .7 * math.sin(math.pi * (i + .5) / n) ** .7
        hs = [4 + rng.random() * 44 * env for _ in range(5)]
        hs.append(hs[0])
        dur = 1.0 + rng.random() * 1.3
        x = 24 + i * step + step * .21
        bars.append(f'<rect x="{f(x)}" y="{f(cy - hs[0] / 2)}" width="{f(step * .58)}" height="{f(hs[0])}" rx="2" fill="url(#eq)">'
                    f'<animate attributeName="height" values="{";".join(f(v) for v in hs)}" dur="{f(dur)}s" repeatCount="indefinite"/>'
                    f'<animate attributeName="y" values="{";".join(f(cy - v / 2) for v in hs)}" dur="{f(dur)}s" repeatCount="indefinite"/></rect>')
    defs = f'<linearGradient id="eq" gradientUnits="userSpaceOnUse" x1="24" x2="466"><stop offset="0" stop-color="{a1}"/><stop offset="1" stop-color="{a2}"/></linearGradient>'
    return defs, [f'<line x1="24" y1="194" x2="466" y2="194" stroke="{LINE}"/>'] + bars


def _activity(series, a1, a2):
    """52 weekly commit counts drawn as bars; a light sweep runs across them."""
    series = list(series or [])[-52:]
    series = [0] * (52 - len(series)) + series
    mx = max(series) or 1
    step, base = 442 / 52, 218
    bars = []
    for i, v in enumerate(series):
        h = 3 if v == 0 else 5 + 34 * v / mx
        col = LINE if v == 0 else a1
        bars.append(f'<rect x="{f(24 + i * step + step * .15)}" y="{f(base - h)}" width="{f(step * .7)}" height="{f(h)}" rx="1.5" fill="{col}"/>')
    defs = '<clipPath id="band"><rect x="24" y="170" width="442" height="50"/></clipPath>'
    sweep = (f'<g clip-path="url(#band)"><rect x="0" y="170" width="120" height="50" fill="url(#sw)" opacity=".28">'
             f'<animateTransform attributeName="transform" type="translate" from="-120 0" to="490 0" dur="4.5s" repeatCount="indefinite"/></rect></g>')
    cap = f'<text x="466" y="176" font-size="10" fill="{DIM}" text-anchor="end">commits per week, last year</text>'
    return defs, bars + [sweep, cap]


def project_card(p):
    """p: normalized project dict (see build.py)."""
    W, H = 490, 262
    a1, a2, hot = ACCENTS.get(p.get("accent", "red"), ACCENTS["red"])
    defs, head = card_base(W, H, a1)
    title = clip(p["title"], 22)
    tfs = 26 if len(title) <= 14 else max(15, int(26 * 14 / len(title)))
    status = clip(p.get("status", ""), 16)
    kind = p.get("status_kind", "idle")
    sw = len(status) * 7.8
    body = [head, f'<text x="24" y="52" font-size="{tfs}" font-weight="800" fill="{TXT}">{escape(title)}</text>']
    if status:
        dot = {"live": GREEN, "dev": PURPLE}.get(kind, DIM)
        cx = 466 - sw - 14
        body.append(f'<circle cx="{f(cx)}" cy="45" r="4" fill="{dot}"/>')
        if kind == "live":
            body.append(f'<circle cx="{f(cx)}" cy="45" r="4" fill="{dot}" opacity=".6"><animate attributeName="r" values="4;10;4" dur="2s" repeatCount="indefinite"/>'
                        f'<animate attributeName="opacity" values=".6;0;.6" dur="2s" repeatCount="indefinite"/></circle>')
        body.append(grid_text([(status, DIM)], 466 - sw, 50, 13))
    body.append(f'<text x="24" y="80" font-size="14" fill="{DIM}">{escape(clip(p.get("subtitle", ""), 52))}</text>')
    for i, b in enumerate(p.get("bullets", [])[:3]):
        body.append(grid_text([("+", a1), (" ", DIM), (clip(b, 48), TXT)], 24, 110 + i * 22, 14))
    style = p.get("style", "activity")
    if style == "trace":
        vd, vb = _trace(a1, a2, hot)
    elif style == "equalizer":
        vd, vb = _equalizer(a1, a2, sum(map(ord, p["title"])))
    else:
        vd, vb = _activity(p.get("series"), a1, a2)
    body += vb
    body.append(chips(p.get("tags", []), 24, 230))
    return svg(W, H, "\n".join(body), defs + vd, p.get("alt") or f'{p["title"]}: {p.get("subtitle", "")}')


# ---------------------------------------------------------------- stats
def stats_card(s):
    W, H = 490, 232
    defs = CARBON_DEFS + SWEEP_DEF
    rows = [("Contributions, 12 months", s.get("contrib")), ("Current streak", s.get("streak_txt")),
            ("Longest streak", s.get("longest_txt")), ("Public repos", s.get("repos")), ("Stars earned", s.get("stars"))]
    body = [frame(W, H, 14), f'<rect width="{W}" height="{H}" rx="14" fill="url(#cf)" opacity=".4"/>',
            f'<text x="25" y="38" font-size="18" font-weight="800" fill="{RED}">Telemetry</text>']
    for i, (lab, val) in enumerate(rows):
        y = 74 + i * 30
        body.append(f'<rect x="25" y="{y - 9}" width="8" height="8" rx="2" fill="{RED}"/>')
        body.append(f'<text x="44" y="{y}" font-size="13" fill="{DIM}">{escape(lab)}</text>')
        body.append(f'<text x="278" y="{y}" font-size="13" font-weight="700" fill="{TXT}" text-anchor="end">{escape(str(val if val is not None else "-"))}</text>')
    cx, cy, r = 388, 118, 46
    frac = min(1.0, (s.get("active_days") or 0) / 365)
    circ = 2 * math.pi * r
    body.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{LINE}" stroke-width="7"/>')
    body.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{RED}" stroke-width="7" stroke-linecap="round" '
                f'stroke-dasharray="{f(max(0.5, circ * frac))} {f(circ)}" transform="rotate(-90 {cx} {cy})"/>')
    body.append(f'<g><circle cx="{cx}" cy="{cy - r}" r="3.6" fill="#fff"/><animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" dur="6s" repeatCount="indefinite"/></g>')
    body.append(f'<text x="{cx}" y="{cy + 2}" font-size="26" font-weight="800" fill="{TXT}" text-anchor="middle">{escape(str(s.get("active_days", 0)))}</text>')
    body.append(f'<text x="{cx}" y="{cy + 20}" font-size="11" fill="{DIM}" text-anchor="middle">active days</text>')
    body.append(f'<text x="{cx}" y="{cy + r + 26}" font-size="11" fill="{DIM}" text-anchor="middle">of the last 365</text>')
    return svg(W, H, "\n".join(body), defs, "GitHub stats")


def langs_card(langs, n_repos):
    W, H = 490, 232
    defs = SWEEP_DEF + f'<clipPath id="bar"><rect x="25" y="56" width="440" height="12" rx="6"/></clipPath>'
    top = langs[:5]
    other = round(100 - sum(p for _, p in top), 1)
    if other >= 0.5:
        top = top + [("Other", other)]
    body = [frame(W, H, 14), f'<text x="25" y="38" font-size="18" font-weight="800" fill="{RED}">Top languages</text>']
    x, segs = 25, []
    for i, (name, pct) in enumerate(top):
        w = 440 * pct / 100
        segs.append(f'<rect x="{f(x)}" y="56" width="{f(w)}" height="12" fill="{LANG_COLORS[i % len(LANG_COLORS)]}"/>')
        x += w
    if not top:
        segs.append(f'<rect x="25" y="56" width="440" height="12" fill="{LINE}"/>')
    body.append(f'<g clip-path="url(#bar)">{"".join(segs)}<rect x="0" y="56" width="110" height="12" fill="url(#sw)" opacity=".4">'
                f'<animateTransform attributeName="transform" type="translate" from="-110 0" to="470 0" dur="3.6s" repeatCount="indefinite"/></rect></g>')
    for i, (name, pct) in enumerate(top):
        cx, cy = 25 + (i % 2) * 225, 106 + (i // 2) * 32
        body.append(f'<circle cx="{cx + 5}" cy="{cy - 4}" r="5" fill="{LANG_COLORS[i % len(LANG_COLORS)]}"/>')
        body.append(f'<text x="{cx + 18}" y="{cy}" font-size="13" fill="{TXT}">{escape(clip(name, 14))}</text>')
        body.append(f'<text x="{cx + 205}" y="{cy}" font-size="13" fill="{DIM}" text-anchor="end">{pct:.1f}%</text>')
    body.append(f'<text x="25" y="{H - 18}" font-size="11" fill="{DIM}">by code size across {n_repos} public repos</text>')
    return svg(W, H, "\n".join(body), defs, "Top languages")


# ---------------------------------------------------------------- contribution heatmap
def heatmap(cal):
    days = sorted(cal["days"], key=lambda d: d["date"])
    W, H = 1000, 210
    if not days:
        return None
    d0 = date.fromisoformat(days[0]["date"])
    w0 = (d0.weekday() + 1) % 7  # Sunday = 0
    cols = (len(days) - 1 + w0) // 7 + 1
    x0, y0 = 58, 50
    pitch = min(17.0, (W - x0 - 24) / cols)
    cell = pitch - 3.5
    defs = SWEEP_DEF + f'<clipPath id="grid"><rect x="{x0 - 2}" y="{y0 - 2}" width="{f(cols * pitch + 4)}" height="{f(7 * pitch + 4)}"/></clipPath>'
    body = [frame(W, H, 14)]
    seen_m, last_lab = None, -9
    for i, d in enumerate(days):
        c, r = divmod(i + w0, 7)
        dt = date.fromisoformat(d["date"])
        if (dt.month != seen_m) and r == 0 or (seen_m is None):
            if c - last_lab >= 3:
                body.append(f'<text x="{f(x0 + c * pitch)}" y="{y0 - 12}" font-size="11" fill="{DIM}">{dt.strftime("%b")}</text>')
                last_lab = c
            seen_m = dt.month
    for lab, row in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
        body.append(f'<text x="{x0 - 10}" y="{f(y0 + row * pitch + cell - 1)}" font-size="10" fill="{DIM}" text-anchor="end">{lab}</text>')
    cells = []
    for i, d in enumerate(days):
        c, r = divmod(i + w0, 7)
        lvl = max(0, min(4, int(d.get("level", 0))))
        cells.append(f'<rect x="{f(x0 + c * pitch)}" y="{f(y0 + r * pitch)}" width="{f(cell)}" height="{f(cell)}" rx="3" fill="{HEAT[lvl]}"/>')
    body.append("".join(cells))
    gw = cols * pitch
    body.append(f'<g clip-path="url(#grid)"><rect x="0" y="{y0 - 2}" width="140" height="{f(7 * pitch + 4)}" fill="url(#sw)" opacity=".22">'
                f'<animateTransform attributeName="transform" type="translate" from="{x0 - 140} 0" to="{f(x0 + gw)} 0" dur="5s" repeatCount="indefinite"/></rect></g>')
    yb = y0 + 7 * pitch + 26
    body.append(f'<text x="{x0}" y="{f(yb)}" font-size="13" fill="{TXT}"><tspan font-weight="800">{cal["total"]}</tspan> <tspan fill="{DIM}">contributions in the last year</tspan></text>')
    lx = W - 24 - 5 * 16 - 70
    body.append(f'<text x="{lx}" y="{f(yb)}" font-size="11" fill="{DIM}" text-anchor="end">less</text>')
    for i in range(5):
        body.append(f'<rect x="{lx + 8 + i * 16}" y="{f(yb - 10)}" width="12" height="12" rx="3" fill="{HEAT[i]}"/>')
    body.append(f'<text x="{lx + 8 + 5 * 16 + 4}" y="{f(yb)}" font-size="11" fill="{DIM}">more</text>')
    return svg(W, H, "\n".join(body), defs, f'Contribution graph: {cal["total"]} contributions in the last year')


# ---------------------------------------------------------------- git log
def gitlog(handle, events):
    if not events:
        return None
    W, fs = 1000, 15
    cw = fs * CW
    rows = events[:6]
    H = 78 + 27 * len(rows)
    segs = prompt_segs(handle, f"git log --oneline -{len(rows)}")
    body = [frame(W, H, 14), grid_text(segs, 28, 42, 16),
            f'<rect x="{f(28 + sum(len(s) for s, _ in segs) * 16 * CW + 4)}" y="27" width="9" height="19" fill="{HOT}"><animate attributeName="opacity" calcMode="discrete" values="1;0" keyTimes="0;.5" dur="1s" repeatCount="indefinite"/></rect>',
            f'<rect x="28" y="56" width="{W - 56}" height="1" fill="{LINE}"/>']
    for i, e in enumerate(rows):
        y = 88 + i * 27
        sha, repo, msg = e["sha"][:7], clip(e["repo"], 16), clip(e["msg"], 58)
        body.append(grid_text([(sha, YEL), (" ", DIM), (repo.ljust(16), BLUE), (" ", DIM), (msg, TXT)], 28, y, fs))
        body.append(f'<text x="{W - 28}" y="{y}" font-size="13" fill="{DIM}" text-anchor="end">{escape(e.get("ago", ""))}</text>')
        if i == 0:
            body.append(f'<circle cx="16" cy="{y - 5}" r="3.5" fill="{HOT}"><animate attributeName="opacity" values="1;.25;1" dur="1.6s" repeatCount="indefinite"/></circle>')
    return svg(W, H, "\n".join(body), "", "Latest commits")
