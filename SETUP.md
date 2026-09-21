# Setup (about 5 minutes, one time)

This repo is your GitHub profile. `profile.toml` is the only file you edit; `README.md` and `assets/` are generated.

## 1. Put it on GitHub
Your profile repo is `user-is-surya/user-is-surya`. Replace its contents with this folder:

```bash
git clone https://github.com/user-is-surya/user-is-surya.git
cd user-is-surya
# delete the old files, then copy everything from this folder in (including the hidden .github folder)
git add -A
git commit -m "new profile"
git push
```

## 2. Run it once
Repo → **Actions** tab → enable workflows if asked → **update-profile** → **Run workflow**.
It fetches your GitHub data, redraws everything, and commits the result. Takes about 30 seconds.

## 3. Count private work on the graph (recommended)
GitHub profile → **Contribution settings** → tick **Private contributions**.
Commits to private repos (F1Intel, S.A.G.E) then show up in the heatmap, streaks and stats. Repo names stay hidden.

## Everyday use
| I want to... | Do this |
|---|---|
| Change tagline, socials, footer, sections | Edit `profile.toml` (pencil icon on github.com), commit. Rebuilds in about a minute. |
| Add or remove a featured project | Copy or delete a `[[project]]` block in `profile.toml`. Order in the file = order on the page. |
| Feature a GitHub repo | `[[project]]` with `repo = "name"`. Description, language, stars, topics and commit activity fill in on their own. |
| Feature a private or external project | `[[project]]` with `title`, `description`, `bullets`, `tags` written by hand. |
| Let it pick projects for me | `[featured]` → `mode = "auto"` |
| Add a technology the scan can't see | Add it to `extra` under `[stack]` |
| Force a refresh right now | Actions → update-profile → Run workflow |
| Preview locally | `python scripts/build.py` (Python 3.11+), then open `README.md` and `assets/` |

## What updates by itself (every 3 hours, and whenever you edit `profile.toml`)
- Tech stack badges: languages, repo topics, and dependencies in `requirements.txt` / `package.json` / `pyproject.toml`
- Top-languages card and stats card (contributions, streaks, active days, repos, stars)
- Contribution heatmap
- Git log of your latest public commits, plus the "last push" line in the header typing
- Featured repo cards: description, stars, last push, commit-activity bars

## Optional extras
**Include private repos in the stack and language stats.** Create a fine-grained personal access token
(Contents: read-only, Metadata: read-only, on all your repos), then repo → Settings → Secrets and variables → Actions →
new secret named `PROFILE_TOKEN`. Private repo names and descriptions are never written to the profile, only their
languages and dependencies are counted.

**Refresh the moment you push to another repo.** In that repo add `.github/workflows/ping-profile.yml`:

```yaml
name: ping-profile
on:
  push:
    branches: [main]
jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - run: >
          curl -s -X POST
          -H "Authorization: Bearer ${{ secrets.PROFILE_PING_TOKEN }}"
          -H "Accept: application/vnd.github+json"
          https://api.github.com/repos/user-is-surya/user-is-surya/dispatches
          -d '{"event_type":"refresh"}'
```
`PROFILE_PING_TOKEN` is a fine-grained token with Contents: read and write on the profile repo only.

## Good to know
- GitHub pauses scheduled workflows after 60 days with no activity in a repo. If that ever happens, click Run workflow once.
- The stats use GitHub's own API, so there is no third-party service that can go down or rate-limit you.
