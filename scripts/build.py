#!/usr/bin/env python3
"""Rebuilds README.md and assets/*.svg from profile.toml + live GitHub data.

  python scripts/build.py             fetch fresh data (uses GITHUB_TOKEN if set), then rebuild
  python scripts/build.py --offline   rebuild from the last saved snapshot only (no network)

You never need to edit this file. Edit profile.toml.
"""
import argparse, html, json, os, sys, tomllib
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import art, catalog, gh  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------- data
def load_json(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return {}


def get_data(cfg, snap_path, offline):
    snap = load_json(snap_path)
    if offline:
        return snap
    me = cfg["me"]["username"]
    projects = cfg.get("project", [])
    auto = cfg.get("featured", {}).get("mode", "manual") == "auto"
    featured = None if auto else [p["repo"] for p in projects if p.get("repo")]
    print(f"Fetching GitHub data for {me} ...")
    fresh = gh.fetch(me, os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"), os.environ.get("PROFILE_TOKEN"), featured)
    merged = dict(snap)
    for k, v in fresh.items():  # a failed fetch never wipes what we already had
        if v:
            merged[k] = v
    Path(snap_path).parent.mkdir(parents=True, exist_ok=True)
    Path(snap_path).write_text(json.dumps(merged, indent=1), encoding="utf-8")
    return merged


# ---------------------------------------------------------------- derived data
def owned(data):
    return [r for r in data.get("repos", []) if not r.get("fork")]


def language_shares(cfg, data):
    hide = {h.lower() for h in cfg.get("stats", {}).get("hide_languages", [])}
    tot = {}
    for r in owned(data):
        for l, b in (r.get("languages") or {}).items():
            if l.lower() not in hide:
                tot[l] = tot.get(l, 0) + b
    s = sum(tot.values()) or 1
    return sorted(((l, round(100 * b / s, 1)) for l, b in tot.items()), key=lambda x: -x[1])


def detect_stack(cfg, data):
    sc = cfg.get("stack", {})
    hide = {h.lower() for h in sc.get("hide", [])}
    found = {}

    def add(name):
        e = catalog.find(name)
        if e and e[0].lower() not in hide and str(name).lower() not in hide:
            found.setdefault(e[0], e)

    if sc.get("auto", True):
        minshare = sc.get("min_language_share", 3)
        for l, pct in language_shares(cfg, data):
            if pct >= minshare:
                add(l)
        for r in owned(data):
            for t in r.get("topics", []):
                add(t)
            for d in r.get("deps", []):
                add(d)
    for x in sc.get("extra", []):
        e = catalog.find(x)
        if e:
            if e[0].lower() not in hide:
                found.setdefault(e[0], e)
        elif str(x).lower() not in hide:
            found.setdefault(x, (x, "", "Other"))
    pin = [str(p).lower() for p in sc.get("pin", [])]
    rows = []
    for cat in catalog.CATEGORIES + ["Other"]:
        items = [e for e in found.values() if e[2] == cat]
        items.sort(key=lambda e: (pin.index(e[0].lower()) if e[0].lower() in pin else 99))
        if items:
            rows.append((cat, items))
    return rows


def streaks(days):
    counts = [d["count"] for d in sorted(days, key=lambda d: d["date"])]
    longest = run = 0
    for c in counts:
        run = run + 1 if c > 0 else 0
        longest = max(longest, run)
    i = len(counts) - 1
    if i >= 0 and counts[i] == 0:
        i -= 1
    cur = 0
    while i >= 0 and counts[i] > 0:
        cur, i = cur + 1, i - 1
    return cur, longest, sum(1 for c in counts if c > 0)


def plural(n, w):
    return f"{n} {w}{'' if n == 1 else 's'}"


def norm_project(p, data):
    repos = {r["name"].lower(): r for r in data.get("repos", [])}
    r = repos.get(str(p.get("repo", "")).lower())
    o = dict(p)
    o["title"] = p.get("title") or p.get("name") or (r or {}).get("name") or "project"
    o["subtitle"] = p.get("description") or (r or {}).get("description") or ""
    if r:
        pushed = r.get("pushed_at")
        recent = pushed and (datetime.now(timezone.utc) - datetime.fromisoformat(pushed.replace("Z", "+00:00"))).days < 45
        if not p.get("status"):
            if r.get("homepage"):
                o["status"], o["status_kind"] = r["homepage"].split("//")[-1].strip("/"), "live"
            elif recent:
                o["status"], o["status_kind"] = "active", "live"
            elif r.get("archived"):
                o["status"], o["status_kind"] = "archived", "idle"
            elif pushed:
                o["status"], o["status_kind"] = "updated " + datetime.fromisoformat(pushed.replace("Z", "+00:00")).strftime("%b %Y"), "idle"
        if not p.get("bullets"):
            langs = r.get("languages") or {}
            tot = sum(langs.values()) or 1
            b = []
            if langs:
                top = max(langs, key=langs.get)
                b.append(f"mostly {top} ({round(100 * langs[top] / tot)}%)")
            if pushed:
                b.append(f"last push {art.ago(pushed)}")
            b.append(f"{plural(r['stars'], 'star')}, {plural(r['forks'], 'fork')}" if r.get("stars") or r.get("forks") else "open source on GitHub")
            o["bullets"] = b
        if not p.get("tags"):
            known = [catalog.find(t)[0].lower() for t in r.get("topics", []) if catalog.find(t)]
            rest = [t for t in r.get("topics", []) if not catalog.find(t)]
            o["tags"] = known + rest or [r.get("language") or ""]
        o.setdefault("url", r.get("homepage") or r.get("url"))
        o["series"] = r.get("activity")
    o.setdefault("style", "activity" if r else "equalizer")
    o.setdefault("accent", "red")
    o.setdefault("status_kind", "idle")
    o["alt"] = f'{o["title"]}: {o["subtitle"]}'
    return o


def pick_projects(cfg, data):
    if cfg.get("featured", {}).get("mode", "manual") == "auto":
        me = cfg["me"]["username"].lower()
        cand = [r for r in owned(data) if not r.get("archived") and r["name"].lower() != me and not r.get("private")]
        cand.sort(key=lambda r: (r.get("stars", 0), r.get("pushed_at") or ""), reverse=True)
        accents = ["red", "purple", "blue", "green", "yellow"]
        items = [{"repo": r["name"], "accent": accents[i % 5]} for i, r in enumerate(cand[: cfg["featured"].get("auto_count", 4)])]
    else:
        items = cfg.get("project", [])
    return [norm_project(p, data) for p in items]


# ---------------------------------------------------------------- README
def social_badges(cfg):
    spec = {"linkedin": ("LinkedIn", "linkedin"), "x": ("X", "x"), "instagram": ("Instagram", "instagram"), "youtube": ("YouTube", "youtube"),
            "reddit": ("Reddit", "reddit"), "website": ("Website", ""), "email": ("Email", "")}
    out = []
    for k, v in cfg.get("social", {}).items():
        if k not in spec or not v:
            continue
        label, slug = spec[k]
        href = v
        if k == "email":
            href = f"mailto:{v}"
            d = v.split("@")[-1].lower()
            slug = "gmail" if d.startswith(("gmail", "googlemail")) else "microsoftoutlook" if d.startswith(("outlook", "hotmail", "live")) else "protonmail" if d.startswith(("proton", "pm.me")) else ""
        elif k == "x" and not v.startswith("http"):
            href = "https://x.com/" + v.lstrip("@")
        out.append(f'<a href="{href}"><img src="{catalog.badge_url(label, slug)}" alt="{label}"></a>')
    return "\n&nbsp;&nbsp;\n".join(out)


def build(cfg, data, out_dir):
    out_dir = Path(out_dir)
    assets = out_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    for old in assets.glob("*.svg"):
        old.unlink()
    me = cfg["me"]
    name = me.get("name") or me["username"]
    handle = (me.get("handle") or name.split()[0]).lower()
    sec = {"projects": True, "stack": True, "stats": True, "activity": True, "recent": True, **cfg.get("sections", {})}
    events = data.get("events", [])
    for e in events:
        e["ago"] = datetime.fromisoformat(e["time"].replace("Z", "+00:00")).strftime("%b %d").replace(" 0", " ")

    def w(fn, s):
        if s:
            (assets / fn).write_text(s, encoding="utf-8")
        return bool(s)

    lines = list(cfg.get("header", {}).get("lines", []))
    if cfg.get("header", {}).get("show_last_push", True) and events:
        lines.append(f"last push: {events[0]['repo']}, {events[0]['ago']}")
    w("header.svg", art.header(handle, name, lines, f"{name}: {lines[0] if lines else ''}"))
    md = ['<!-- Generated by scripts/build.py. To change anything, edit profile.toml instead of this file. -->',
          '<div align="center">', "",
          f'<img src="./assets/header.svg" alt="{html.escape(name + ", " + (lines[0] if lines else "GitHub profile"))}" width="100%">', "", "<br><br>", "",
          social_badges(cfg), "", "</div>", "", "<br>", ""]

    def heading(key, cmd, label):
        w(f"sec-{key}.svg", art.section(handle, cmd, label))
        md.extend([f'<img src="./assets/sec-{key}.svg" alt="{label}" width="100%">', ""])

    summary = {"projects": [], "stack": [], "events": len(events)}
    if sec["projects"]:
        projects = pick_projects(cfg, data)
        if projects:
            heading("projects", "./projects", "projects")
            md.append('<div align="center">')
            for i, p in enumerate(projects):
                w(f"card-{i + 1}.svg", art.project_card(p))
                img = f'<img src="./assets/card-{i + 1}.svg" alt="{html.escape(p["alt"])}" width="49%">'
                md.append(f'<a href="{p["url"]}">{img}</a>' if p.get("url") else img)
            md += ["</div>", "", "<br>", ""]
            summary["projects"] = [p["title"] for p in projects]

    if sec["stack"]:
        rows = detect_stack(cfg, data)
        if rows:
            heading("stack", "./stack", "tech stack")
            md.append('<div align="center">')
            md.append("\n<br>\n".join("\n".join(f'<img src="{catalog.badge_url(e[0], e[1])}" alt="{e[0]}">' for e in items) for _, items in rows))
            md += ["", "</div>", "", "<br>", ""]
            summary["stack"] = [e[0] for _, items in rows for e in items]

    cal = data.get("calendar")
    if sec["stats"]:
        cur, longest, active = streaks(cal["days"]) if cal else (0, 0, 0)
        repos = data.get("user", {}).get("public_repos") or len([r for r in data.get("repos", []) if not r.get("private")])
        st = {"contrib": cal["total"] if cal else None, "streak_txt": plural(cur, "day"), "longest_txt": plural(longest, "day"),
              "repos": repos, "stars": sum(r.get("stars", 0) for r in owned(data)), "active_days": active}
        heading("stats", "./stats", "github stats")
        w("stats.svg", art.stats_card(st))
        w("langs.svg", art.langs_card(language_shares(cfg, data), len([r for r in owned(data) if not r.get("private")])))
        md += ['<div align="center">', '<img src="./assets/stats.svg" alt="GitHub stats" width="49%">',
               '<img src="./assets/langs.svg" alt="Top languages" width="49%">', "</div>", "", "<br>", ""]

    if sec["activity"] and cal and cal.get("days"):
        heading("activity", "./activity", "contribution graph")
        w("heatmap.svg", art.heatmap(cal))
        md += [f'<img src="./assets/heatmap.svg" alt="Contribution graph: {cal["total"]} contributions in the last year" width="100%">', "", "<br>", ""]

    if sec["recent"] and events and w("gitlog.svg", art.gitlog(handle, events)):
        md += ['<img src="./assets/gitlog.svg" alt="Latest commits" width="100%">', "", "<br>", ""]

    w("footer.svg", art.footer(handle, cfg.get("footer", {}).get("text", "thanks for stopping by")))
    md.append('<img src="./assets/footer.svg" alt="Thanks for stopping by" width="100%">')
    (out_dir / "README.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="use the saved snapshot, no network")
    ap.add_argument("--config", default=str(ROOT / "profile.toml"))
    ap.add_argument("--snapshot", default=str(ROOT / "data" / "snapshot.json"))
    ap.add_argument("--out", default=str(ROOT))
    a = ap.parse_args()
    cfg = tomllib.loads(Path(a.config).read_text(encoding="utf-8"))
    data = get_data(cfg, a.snapshot, a.offline)
    s = build(cfg, data, a.out)
    print("Built README.md + assets/  |  projects:", s["projects"], "| stack:", len(s["stack"]), "badges | recent commits:", s["events"])


if __name__ == "__main__":
    main()
