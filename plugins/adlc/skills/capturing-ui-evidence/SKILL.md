---
name: capturing-ui-evidence
description: Capture screenshots or a video of the app in headless Chromium (Playwright) to prove a UI change or a fixed visual bug, and attach them to the pull request so the reviewer sees the UI before merging. Use whenever a PR's diff touches the repo's UI paths, to record a visual bug before fixing it, or when asked for screenshots or a recording of a feature.
---

# Capturing UI evidence

A PR that changes what users see carries pictures of it, so the human merging it can judge the UI without
checking the branch out: `after` for new or changed UI, `before` and `after` for a visual bug. Interactions
(something that happens after a click, a stream, an animation) get a video; static layout gets screenshots.

## Configuration

Read the repo's `## ADLC preview` section (in `AGENTS.md`, or `CLAUDE.md` if there is no `AGENTS.md`):

```markdown
## ADLC preview
- Command: `npm run dev`                 # starts the app in mock/offline mode, no real credentials
- URL: http://localhost:3000
- Ready URL: http://localhost:8000/health   # optional, repeatable: a backend that must answer too
- UI paths: `frontend/**`, `src/components/**`
```

Set **Ready URL** when the frontend answers before its backend does; otherwise the capture shows the app's
error state.

- **UI paths** decide whether a PR needs evidence: if any changed file matches, it does.
- **No section?** The repo hasn't opted in. Skip evidence and say so in the PR report ("no ADLC preview
  configured, no UI evidence") — never guess a command.

## When a PR needs evidence

```bash
git diff --name-only <base>...HEAD
```

If any path matches a UI-paths glob, this PR needs evidence. A diff that only touches tests, types or styling
tokens that render nothing new may still need it — when in doubt, capture.

## 1. Write a capture spec

A JSON file outside the working tree, in `$(git rev-parse --absolute-git-dir)/adlc/`, describing what to do in
the browser:

```json
{
  "viewport": {"width": 1280, "height": 800},
  "video": true,
  "steps": [
    {"goto": "/"},
    {"fill": ["textarea", "What soils are at this site?"]},
    {"press": "Enter"},
    {"wait_for": "text=Stop"},
    {"screenshot": "streaming"},
    {"wait_for": "text=Hydrologic soil group", "timeout": 30000},
    {"screenshot": "answer", "full_page": true}
  ]
}
```

Steps: `goto` (path or URL), `click`, `fill` [selector, text], `press` (key, or [selector, key]), `hover`,
`wait_for` (selector), `wait` (ms; avoid when a `wait_for` works), `screenshot` (name; optional `full_page`, or
`selector` to shoot one element). Selectors are Playwright selectors: CSS, `text=...`,
`role=button[name="Send"]`. Any step can take `timeout` in ms (default 15000).

Shoot the thing the ticket is about, framed so a reviewer sees it without reading the code. Cover each
acceptance criterion that is visible. The preview command should run the app in mock mode, so no real model,
account or data is involved.

## 2. Capture

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/capturing-ui-evidence/scripts/capture.py <spec.json> --label after \
  --serve "<preview command>" --url <preview URL> [--ready <ready URL> ...]
```

It starts the preview command in its own process group, waits for the URL and every ready URL (up to 7 minutes, for a first Docker
build), runs the spec in headless Chromium, stops the server, and prints the files it wrote to
`<git dir>/adlc/evidence/<label>/`. Video lands as `recording.webm`; a failing step leaves
`failed-step-N.png` and exits non-zero. The server's output is in `server.log` next to the evidence.

- The first run installs Playwright and Chromium into `~/.cache/adlc-playwright` (override with
  `ADLC_PLAYWRIGHT_HOME`); it takes a few minutes. It needs `node` and `npm`.
- **`before` for a bug:** capture with `--label before` on the unchanged code, before you write the fix.
- **URL already answers:** the script refuses, because something else (maybe another worktree) is serving it
  and you'd capture the wrong code. Stop that server, or pass `--reuse` only if you're sure it serves this
  working tree.

**Look at every screenshot** (Read the PNG) before attaching it. A blank page, a sign-in screen, an error
overlay, a loading spinner or the wrong state is a failed capture: fix the spec and rerun. Don't attach a
capture you haven't looked at.

## 3. Attach

```bash
gh pr comment <pr> --body "$(cat <<'EOF'
## UI evidence
<one line per file: what it shows, and which acceptance criterion it covers>
EOF
)" --attach "<file>#<alt text>" [--attach "<file>#<alt text>" ...]
```

`--attach` uploads images and video to GitHub and needs gh 2.99 or newer; check with
`gh pr comment --help | grep -- --attach`. If it's missing, stop and tell the user to upgrade gh.

- **Never commit evidence files** to the branch. They live under the git dir, outside the working tree.
- Mention the evidence comment in the PR report.
- After later commits change the UI again, capture and attach again: evidence must match the head commit.

## Integration

- `creating-pull-requests` runs this after opening any PR whose diff touches the UI paths.
- `execution-orchestration` runs it for the feature PR (phase PRs merge automatically, so the feature PR is
  where the human looks).
- `babysitting-prs` won't report a UI PR as ready to merge until it has an evidence comment newer than the last
  UI change.
