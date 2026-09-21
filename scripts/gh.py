"""Everything that talks to GitHub. Every call fails soft: if something can't be fetched,
build.py falls back to the last good snapshot instead of breaking the profile."""
import json, re, time, urllib.request, urllib.error
from datetime import datetime, timezone

API = "https://api.github.com"
UA = "profile-readme-builder"
MANIFESTS = ("requirements.txt", "package.json", "pyproject.toml")


class GH:
    def __init__(self, token=None, log=print):
        self.token, self.log = token, log

    def _req(self, url, data=None, accept="application/vnd.github+json"):
        h = {"User-Agent": UA, "Accept": accept}
        host = url.split("/")[2]
        if self.token and host == "api.github.com":
            h["Authorization"] = f"Bearer {self.token}"
        elif self.token and host == "raw.githubusercontent.com":
            h["Authorization"] = f"token {self.token}"  # only ever sent to GitHub's own hosts
        if data is not None:
            h["Content-Type"] = "application/json"
            data = json.dumps(data).encode()
        return urllib.request.Request(url, data=data, headers=h)

    def get(self, path, raw=False, retries=1):
        url = path if path.startswith("http") else API + path
        for attempt in range(retries + 1):
            try:
                with urllib.request.urlopen(self._req(url), timeout=25) as r:
                    body = r.read().decode("utf-8", "replace")
                    if r.status == 202 and attempt < retries:  # stats are being computed
                        time.sleep(2.5)
                        continue
                    if r.status == 202 or not body.strip():
                        return None
                    return body if raw else json.loads(body)
            except urllib.error.HTTPError as e:
                if e.code != 404:
                    self.log(f"  ! {e.code} {url.split('?')[0]}")
                return None
            except Exception as e:
                self.log(f"  ! {type(e).__name__} {url.split('?')[0]}")
                return None
        return None

    def paginate(self, path, limit=300):
        out, page = [], 1
        while len(out) < limit:
            sep = "&" if "?" in path else "?"
            chunk = self.get(f"{path}{sep}per_page=100&page={page}")
            if not chunk or not isinstance(chunk, list):
                break
            out += chunk
            if len(chunk) < 100:
                break
            page += 1
        return out

    def graphql(self, query, variables):
        try:
            with urllib.request.urlopen(self._req(API + "/graphql", {"query": query, "variables": variables}), timeout=25) as r:
                j = json.load(r)
                return j.get("data") if not j.get("errors") else None
        except Exception as e:
            self.log(f"  ! graphql {type(e).__name__}")
            return None


# ---------------------------------------------------------------- parsers
def parse_manifest(name, text):
    """Return lowercase dependency names found in a manifest."""
    out = set()
    if name == "requirements.txt":
        for line in text.splitlines():
            line = line.split("#")[0].strip()
            if not line or line.startswith(("-", "git+", "http")):
                continue
            m = re.match(r"([A-Za-z0-9_.\-]+)", line)
            if m:
                out.add(m.group(1).lower().replace("_", "-"))
    elif name == "package.json":
        try:
            j = json.loads(text)
            for k in ("dependencies", "devDependencies"):
                out |= {d.lower() for d in (j.get(k) or {})}
        except Exception:
            pass
    elif name == "pyproject.toml":
        for m in re.finditer(r"""["']([A-Za-z0-9_.\-]+)\s*(?:[<>=!~\[;(].*?)?["']""", text):
            out.add(m.group(1).lower().replace("_", "-"))
    return out


def parse_calendar_html(html):
    days = []
    for m in re.finditer(r"<td\b[^>]*data-date=\"(\d{4}-\d\d-\d\d)\"[^>]*>", html):
        tag = m.group(0)
        lvl = re.search(r'data-level="(\d)"', tag)
        cid = re.search(r'id="(contribution-day-component-[\d-]+)"', tag)
        days.append({"date": m.group(1), "level": int(lvl.group(1)) if lvl else 0, "id": cid.group(1) if cid else None, "count": 0})
    tips = {}
    for m in re.finditer(r'<tool-tip[^>]*for="(contribution-day-component-[\d-]+)"[^>]*>\s*([^<]*?)\s*</tool-tip>', html):
        n = re.match(r"(\d+)\s+contribution", m.group(2))
        tips[m.group(1)] = int(n.group(1)) if n else 0
    for d in days:
        d["count"] = tips.get(d.pop("id"), 0)
    total = re.search(r">\s*([\d,]+)\s+contributions?\s+in\s+the\s+last\s+year", html)
    return {"total": int(total.group(1).replace(",", "")) if total else sum(d["count"] for d in days), "days": sorted(days, key=lambda d: d["date"])}


LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
CAL_QUERY = """query($login:String!){user(login:$login){contributionsCollection{
 totalCommitContributions totalPullRequestContributions totalIssueContributions
 contributionCalendar{totalContributions weeks{contributionDays{date contributionCount contributionLevel}}}}}}"""


# ---------------------------------------------------------------- fetch
def fetch(username, token, private_token=None, featured_repos=None, log=print):
    """featured_repos: repo names to pull commit-activity for (None = all)."""
    gh = GH(private_token or token, log)
    data = {}

    u = gh.get(f"/users/{username}")
    if u:
        data["user"] = {"name": u.get("name"), "public_repos": u.get("public_repos", 0), "followers": u.get("followers", 0)}

    path = "/user/repos?affiliation=owner&visibility=all&sort=pushed" if private_token else f"/users/{username}/repos?type=owner&sort=pushed"
    repos = []
    for r in gh.paginate(path):
        if r.get("owner", {}).get("login", "").lower() != username.lower():
            continue
        repos.append({"name": r["name"], "full": r["full_name"], "description": r.get("description"), "language": r.get("language"),
                      "stars": r.get("stargazers_count", 0), "forks": r.get("forks_count", 0), "topics": r.get("topics") or [],
                      "homepage": r.get("homepage") or "", "pushed_at": r.get("pushed_at"), "fork": r.get("fork", False),
                      "archived": r.get("archived", False), "private": r.get("private", False), "url": r.get("html_url"),
                      "branch": r.get("default_branch", "main"), "languages": {}, "deps": []})
    if repos or u:
        data["repos"] = repos
    want = None if featured_repos is None else {n.lower() for n in featured_repos}
    for r in [x for x in repos if not x["fork"]][:20]:
        r["languages"] = gh.get(f"/repos/{r['full']}/languages") or {}
        deps = set()
        for m in MANIFESTS:
            t = gh.get(f"https://raw.githubusercontent.com/{r['full']}/{r['branch']}/{m}", raw=True)
            if t:
                deps |= parse_manifest(m, t)
        r["deps"] = sorted(deps)
        if want is None or r["name"].lower() in want:
            part = gh.get(f"/repos/{r['full']}/stats/participation", retries=2)
            if part:
                ser = part.get("owner") or []
                r["activity"] = ser if sum(ser) else (part.get("all") or [])

    for r in repos:  # private repos only ever feed the stack + language stats; their identity is never stored
        if r["private"]:
            r.update(name="private", full="", description=None, homepage="", url="", pushed_at=None, activity=None)

    cal = None
    if gh.token:
        g = gh.graphql(CAL_QUERY, {"login": username})
        try:
            cc = g["user"]["contributionsCollection"]
            days = [{"date": d["date"], "count": d["contributionCount"], "level": LEVELS.get(d["contributionLevel"], 0)}
                    for w in cc["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
            cal = {"total": cc["contributionCalendar"]["totalContributions"], "days": days}
        except Exception:
            cal = None
    if not cal:
        html = gh.get(f"https://github.com/users/{username}/contributions", raw=True)
        if html:
            c = parse_calendar_html(html)
            cal = c if c["days"] else None
    if cal:
        data["calendar"] = cal

    events = []
    for e in gh.get(f"/users/{username}/events/public?per_page=50") or []:
        if e.get("type") != "PushEvent" or len(events) >= 6:
            continue
        repo, pl = e["repo"]["name"], e.get("payload", {})
        commits = pl.get("commits") or []
        sha, msg = pl.get("head"), None
        if commits:
            sha, msg = commits[-1].get("sha", sha), commits[-1].get("message")
        elif sha:
            c = gh.get(f"/repos/{repo}/commits/{sha}")
            msg = (c or {}).get("commit", {}).get("message")
        if sha and msg:
            events.append({"repo": repo.split("/")[-1], "sha": sha, "msg": msg.splitlines()[0], "time": e["created_at"]})
    if events:
        data["events"] = events
    return data
