#!/usr/bin/env python3
"""Start the project's preview server, run a capture spec in headless Chromium, stop the server.

    capture.py SPEC --label after --serve "make dev" --url http://localhost:3000 [--reuse] [--out DIR]

Prints one line per file written. Evidence goes to <git dir>/adlc/evidence/<label>/ unless --out is given."""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = Path(os.environ.get("ADLC_PLAYWRIGHT_HOME", Path.home() / ".cache" / "adlc-playwright"))
PLAYWRIGHT = "1.49.1"


def answers(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.status < 500
    except urllib.error.HTTPError as exc:
        return exc.code < 500
    except (urllib.error.URLError, OSError):
        return False


def ensure_playwright() -> None:
    if (TOOLS / "node_modules" / "playwright").exists() and (TOOLS / ".chromium").exists():
        return
    TOOLS.mkdir(parents=True, exist_ok=True)
    print(f"Installing Playwright {PLAYWRIGHT} into {TOOLS} (first run only)...", file=sys.stderr)
    subprocess.run(["npm", "install", "--prefix", str(TOOLS), "--no-audit", "--no-fund", f"playwright@{PLAYWRIGHT}"],
                   check=True, stdout=sys.stderr)
    # --with-deps needs root on Linux; try it there, fall back to the browser alone.
    cli = [str(TOOLS / "node_modules" / ".bin" / "playwright"), "install", "chromium"]
    if sys.platform.startswith("linux") and subprocess.run([*cli, "--with-deps"], stdout=sys.stderr).returncode == 0:
        pass
    else:
        subprocess.run(cli, check=True, stdout=sys.stderr)
    (TOOLS / ".chromium").touch()


def git_dir() -> Path:
    out = subprocess.run(["git", "rev-parse", "--absolute-git-dir"], check=True, capture_output=True, text=True)
    return Path(out.stdout.strip())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec")
    parser.add_argument("--label", required=True, help="before | after | any name")
    parser.add_argument("--url", required=True, help="base URL of the running app")
    parser.add_argument("--serve", help="command that starts the app (the repo's ADLC preview command)")
    parser.add_argument("--ready", action="append", default=[],
                        help="another URL that must answer before capturing, e.g. the API's health check (repeatable)")
    parser.add_argument("--reuse",action="store_true", help="use a server that's already answering at --url")
    parser.add_argument("--out", help="output directory (default: <git dir>/adlc/evidence/<label>)")
    parser.add_argument("--startup-timeout", type=int, default=420)
    args = parser.parse_args()

    out = Path(args.out) if args.out else git_dir() / "adlc" / "evidence" / args.label
    out.mkdir(parents=True, exist_ok=True)
    spec = json.loads(Path(args.spec).read_text())  # fail early on a bad spec, before starting anything
    ensure_playwright()

    server = None
    if answers(args.url):
        if not args.reuse:
            print(f"{args.url} already answers: another server is running (maybe another checkout). Stop it, or "
                  "pass --reuse if it serves this working tree.", file=sys.stderr)
            return 2
    elif args.serve:
        log = open(out / "server.log", "w")
        # Own process group, so stopping it stops everything the command started.
        server = subprocess.Popen(args.serve, shell=True, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        deadline = time.monotonic() + args.startup_timeout
        while not all(answers(url) for url in [args.url, *args.ready]):
            if server.poll() is not None:
                print(f"Preview command exited with {server.returncode}; see {out / 'server.log'}", file=sys.stderr)
                return 2
            if time.monotonic() > deadline:
                print(f"{' / '.join([args.url, *args.ready])} didn't all answer within {args.startup_timeout}s; see {out / 'server.log'}",
                      file=sys.stderr)
                os.killpg(server.pid, signal.SIGTERM)
                return 2
            time.sleep(2)
    else:
        print(f"Nothing answers at {args.url} and no --serve command was given.", file=sys.stderr)
        return 2

    try:
        env = {**os.environ, "NODE_PATH": str(TOOLS / "node_modules")}
        done = subprocess.run(["node", str(HERE / "capture.mjs"), json.dumps(spec), args.url, str(out)], env=env)
        return done.returncode
    finally:
        if server and server.poll() is None:
            os.killpg(server.pid, signal.SIGTERM)
            try:
                server.wait(timeout=20)
            except subprocess.TimeoutExpired:
                os.killpg(server.pid, signal.SIGKILL)


if __name__ == "__main__":
    sys.exit(main())
