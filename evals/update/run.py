#!/usr/bin/env python3
"""Run the `update` skill's fixtures against skills/update/bin/update-report.

  python3 evals/update/run.py                       run every fixture
  python3 evals/update/run.py --only 07,12          run fixtures whose id starts with 07 or 12
  python3 evals/update/run.py --list                list fixtures, their failure-list item and tag
  python3 evals/update/run.py --bin PATH            test another copy of the script
  python3 evals/update/run.py --timing              print each run's time

WHO WROTE THIS. The fixtures were written from the spec's failure list alone, by someone other than the person who
built the script, before the script existed. Each fixture is a directory under fixtures/ holding one case.json:
the input (files, a git history, a fake `gh` or none), and what the report must do (exit code, lines it must print,
lines it must not, order, per-section contents). The runner builds a fresh temporary directory per fixture, runs
the script there with a clean environment, and checks.

TAGS. `spec`: the spec states the literal line or exit code. `principle`: the spec states a rule (never read a
failure as "nothing", never crash, never write) and this checks it. `assumption`: the spec is silent on a format
and the fixture assumed one; if the skill documents another, change the fixture and say so in the PR. `extra`:
a case the failure list missed. A failing `spec` fixture is a bug in the script; a failing `assumption` fixture is
a question for whoever owns the spec.

HOW A RUN IS ISOLATED. Fresh directory; cwd is that directory; HOME is empty; git reads no user or system config;
git may not look above the directory; TZ=UTC; the PATH holds only a directory of symlinks to common tools
(never `gh`) plus, when the fixture asks for one, a fake `gh` that logs every call to $GH_LOG. A fixture cannot
pass by reaching the network or the real `gh`.
"""
import argparse, datetime, json, os, pathlib, re, shutil, stat, subprocess, sys, tempfile, time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
DEFAULT_BIN = ROOT / "skills" / "update" / "bin" / "update-report"

# the five sections, in the order the page must print them
SECTIONS = [
    ("needs", "needs you now"),
    ("gates", "human gates and blockers"),
    ("objectives", "objectives"),
    ("completed", "recently completed"),
    ("agents", "other agents"),
]
TOOLS = ("sh bash dash python3 python env date cat sed awk grep egrep head tail sort uniq tr cut wc mktemp ls dirname "
         "basename readlink realpath stat find xargs printf expr test true false git tee mkdir rm cp mv touch id uname "
         "hostname sleep tac rev").split()
WRITE_VERBS = {"merge", "close", "comment", "create", "edit", "review", "delete", "reopen", "ready", "lock", "unlock",
               "transfer", "archive", "rename", "fork", "clone", "sync"}


def fmt_dates(text, today, now):
    """{{today-N}} -> a date N days ago; {{now-Nh}} -> an ISO time N hours ago; {{ESC}} etc. come from JSON escapes."""
    def d(m):
        return (today - datetime.timedelta(days=int(m.group(2)))).isoformat() if m.group(1) == "-" else \
               (today + datetime.timedelta(days=int(m.group(2)))).isoformat()
    def h(m):
        t = now - datetime.timedelta(hours=int(m.group(2))) if m.group(1) == "-" else now + datetime.timedelta(hours=int(m.group(2)))
        return t.strftime("%Y-%m-%dT%H:%M:%SZ")
    text = text.replace("{{NOW}}", now.strftime("%Y-%m-%dT%H:%M:%SZ"))
    text = re.sub(r"\{\{today([-+])(\d+)\}\}", d, text)
    return re.sub(r"\{\{now([-+])(\d+)h\}\}", h, text)


def make_toolbin(root):
    tb = root / "toolbin"
    tb.mkdir()
    for t in TOOLS:
        p = shutil.which(t)
        if p and not (tb / t).exists():
            (tb / t).symlink_to(p)
    return tb


FAKE_GH = r'''#!/bin/sh
# fake gh: logs every call; behaviour chosen by $GH_MODE
echo "$*" >> "$GH_LOG"
case "$GH_MODE" in
  unauth)
    case "$1 $2" in "auth status") echo "You are not logged into any GitHub hosts. To log in, run: gh auth login" >&2; exit 1;; esac
    echo "gh: To use GitHub CLI in an Actions workflow or script, run: gh auth login" >&2; exit 4;;
  error)
    case "$1 $2" in "auth status") echo "Logged in to github.com account fixture-bot" ; exit 0;; esac
    echo "HTTP 502: Bad Gateway (https://api.github.com/graphql)" >&2; exit 1;;
  ok-empty)
    case "$1 $2" in "auth status") echo "Logged in to github.com account fixture-bot"; exit 0;; esac
    case "$1" in --version) echo "gh version 2.99.0 (fixture)"; exit 0;; esac
    case " $* " in
      *" pr list "*" merged "*) [ -n "$GH_MERGED" ] && { cat "$GH_MERGED"; exit 0; };;
      *" pr list "*" open "*) [ -n "$GH_OPEN" ] && { cat "$GH_OPEN"; exit 0; };;
    esac
    case " $* " in *" --jq "*|*" -q "*) exit 0;; *" --json "*) echo "[]"; exit 0;; esac
    exit 0;;
esac
exit 0
'''


def git(cwd, *args, env=None, date=None):
    e = dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_SYSTEM="/dev/null", GIT_AUTHOR_NAME="Fixture",
             GIT_AUTHOR_EMAIL="fixture@example.invalid", GIT_COMMITTER_NAME="Fixture", GIT_COMMITTER_EMAIL="fixture@example.invalid")
    if date:
        e["GIT_AUTHOR_DATE"] = e["GIT_COMMITTER_DATE"] = date
    r = subprocess.run(["git", *args], cwd=cwd, env=e, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"fixture setup failed: git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def snapshot(path):
    """name -> (size, mtime_ns, mode) for every file under path, to prove a run wrote nothing."""
    out = {}
    for p in sorted(pathlib.Path(path).rglob("*")):
        try:
            s = p.lstat()
        except OSError:
            continue
        out[str(p.relative_to(path))] = (s.st_size, s.st_mtime_ns, s.st_mode)
    return out


def build(case, root, today, now):
    work = root / "work"
    work.mkdir()
    g = case.get("git", {"repo": True})
    if g.get("repo", True):
        git(work, "init", "-q", "-b", "main")
    for name, content in case.get("files", {}).items():
        p = work / name
        p.parent.mkdir(parents=True, exist_ok=True)
        data = fmt_dates(content, today, now)
        p.write_bytes(data.encode("utf-8", "surrogateescape") if not case.get("binary_files", {}).get(name) else
                      bytes.fromhex(case["binary_files"][name]))
    for name, spec in case.get("files_gen", {}).items():
        p = work / name
        body = fmt_dates(spec.get("head", ""), today, now)
        block = fmt_dates(spec.get("repeat", ""), today, now)
        n = spec.get("times", 0)
        parts = [body] + [block.replace("{n}", str(i)) for i in range(n)]
        if spec.get("long_line"):
            parts.append("note: " + "x" * spec["long_line"] + "\n")
        p.write_text("".join(parts))
    for name, hexdata in case.get("binary_files", {}).items():
        p = work / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(bytes.fromhex(hexdata))
    if g.get("repo", True):
        git(work, "add", "-A")
        for c in g.get("commits", []):
            when = (now - datetime.timedelta(hours=c.get("age_hours", 1))).strftime("%Y-%m-%dT%H:%M:%S+0000")
            git(work, "commit", "-q", "--allow-empty", "-m", c["subject"], date=when)
    for name, mode in case.get("chmod", {}).items():
        os.chmod(work / name, int(mode, 8))
    for name in case.get("mkdirs", []):
        (work / name).mkdir(parents=True, exist_ok=True)
    return work


def sections(text):
    """-> {name: text of that section}; a heading is a line whose stripped text is the name (optionally with a parenthesis)."""
    lines = text.split("\n")
    marks = []
    for i, line in enumerate(lines):
        s = re.sub(r"^[\s#*_=\-]+|[\s#*_=\-:]+$", "", line).lower()
        for key, name in SECTIONS:
            if s == name or re.fullmatch(re.escape(name) + r"\s*\(.*\)", s):
                marks.append((i, key))
                break
    out = {}
    for n, (i, key) in enumerate(marks):
        end = marks[n + 1][0] if n + 1 < len(marks) else len(lines)
        out.setdefault(key, "\n".join(lines[i + 1:end]))
    return out, [k for _, k in marks]


def deep_fmt(x, today, now):
    if isinstance(x, str):
        return fmt_dates(x, today, now)
    if isinstance(x, list):
        return [deep_fmt(i, today, now) for i in x]
    if isinstance(x, dict):
        return {k: deep_fmt(v, today, now) for k, v in x.items()}
    return x


def run_case(case, binpath, timing=False):
    today = datetime.datetime.now(datetime.timezone.utc).date()
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    case = dict(case, expect=deep_fmt(case["expect"], today, now))
    root = pathlib.Path(tempfile.mkdtemp(prefix="update-fx-"))
    try:
        work = build(case, root, today, now)
        tb = make_toolbin(root)
        for t in case.get("remove_tools", []):
            (tb / t).unlink(missing_ok=True)
        path = str(tb)
        gh_mode = case.get("gh", "absent")
        gh_log = root / "gh.log"
        gh_log.write_text("")
        if gh_mode != "absent":
            fb = root / "fakegh"
            fb.mkdir()
            (fb / "gh").write_text(FAKE_GH)
            (fb / "gh").chmod(0o755)
            path = f"{fb}:{tb}"
        home = root / "home"
        home.mkdir()
        env = {"PATH": path, "HOME": str(home), "TZ": "UTC", "LC_ALL": "C.UTF-8", "LANG": "C.UTF-8",
               "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null",
               "GIT_CEILING_DIRECTORIES": str(root), "GH_MODE": gh_mode, "GH_LOG": str(gh_log), "PYTHONDONTWRITEBYTECODE": "1"}
        for key, var in (("merged", "GH_MERGED"), ("open", "GH_OPEN")):
            if key in case.get("gh_data", {}):
                f = root / f"gh-{key}.json"
                f.write_text(fmt_dates(json.dumps(case["gh_data"][key]), today, now))
                env[var] = str(f)
        env.update(case.get("env", {}))
        before = snapshot(work)
        git_before = git(work, "rev-parse", "--verify", "-q", "HEAD") if (work / ".git").exists() and case.get("git", {}).get("commits") else ""
        cmd = [str(binpath)] + [fmt_dates(a, today, now) for a in case.get("args", [])]
        runs = []
        for _ in range(2 if case["expect"].get("deterministic") else 1):
            t0 = time.time()
            try:
                r = subprocess.run(cmd, cwd=work, env=env, capture_output=True, timeout=case.get("timeout", 30))
                runs.append((r.returncode, r.stdout, r.stderr, time.time() - t0))
            except subprocess.TimeoutExpired:
                runs.append((124, b"", b"TIMEOUT", time.time() - t0))
            except OSError as e:
                runs.append((127, b"", str(e).encode(), time.time() - t0))
        rc, out_b, err_b, secs = runs[0]
        after = snapshot(work)
        calls = [l.strip() for l in gh_log.read_text().splitlines() if l.strip()]
        git_after = git(work, "rev-parse", "--verify", "-q", "HEAD") if git_before else ""
        status_after = git(work, "status", "--porcelain") if (work / ".git").exists() else ""
        return dict(expect=case["expect"], rc=rc, out=out_b, err=err_b, secs=secs, runs=runs, before=before, after=after, gh_calls=calls,
                    git_before=git_before, git_after=git_after, status_after=status_after)
    finally:
        for dp, dn, fn in os.walk(root):
            for n in dn + fn:
                try:
                    os.chmod(os.path.join(dp, n), 0o700 if n in dn else 0o600)
                except OSError:
                    pass
        shutil.rmtree(root, ignore_errors=True)


def check(case, res):
    e = case["expect"]
    problems = []
    text = res["out"].decode("utf-8", "replace")
    both = text + "\n" + res["err"].decode("utf-8", "replace")
    if "exit" in e and res["rc"] not in e["exit"]:
        problems.append(f"exit code {res['rc']}, expected one of {e['exit']}")
    if res["rc"] == 127:
        problems.append("the script could not be executed: " + res["err"].decode("utf-8", "replace").strip()[:120])
    if "Traceback (most recent call last)" in both or re.search(r"(?m)^\S*: line \d+: .*(command not found|syntax error|unbound variable)", both):
        problems.append("the script crashed or the shell reported an error: " + both.strip().splitlines()[-1][:120])
    for rx in e.get("contains", []):
        if not re.search(rx, text, re.M):
            problems.append(f"missing line matching /{rx}/")
    for rx in e.get("not_contains", []):
        m = re.search(rx, text, re.M)
        if m:
            problems.append(f"forbidden text /{rx}/ printed: {m.group(0)[:80]!r}")
    for rx in e.get("exact_lines", []):
        if not any(l.strip() == rx for l in text.split("\n")):
            problems.append(f"no line that is exactly {rx!r}")
    secs, order = sections(text)
    if e.get("section_order"):
        want = [k for k, _ in SECTIONS]
        if order != want:
            problems.append(f"sections printed {order}, expected {want} in that order")
    for key, rules in e.get("in_section", {}).items():
        body = secs.get(key)
        if body is None:
            problems.append(f"section {key!r} is not on the page")
            continue
        for rx in rules.get("contains", []):
            if not re.search(rx, body, re.M):
                problems.append(f"section {key!r} lacks /{rx}/")
        for rx in rules.get("not_contains", []):
            m = re.search(rx, body, re.M)
            if m:
                problems.append(f"section {key!r} must not contain /{rx}/: {m.group(0)[:80]!r}")
    for key, n in e.get("count_in_section", {}).items():
        body = secs.get(key, "")
        rx, lo = n["rx"], n["at_least"]
        found = len(re.findall(rx, body, re.M))
        if found < lo:
            problems.append(f"section {key!r}: /{rx}/ found {found}x, expected at least {lo}")
    for rx_count in e.get("count", []):
        found = len(re.findall(rx_count["rx"], text, re.M))
        if "exactly" in rx_count and found != rx_count["exactly"]:
            problems.append(f"/{rx_count['rx']}/ found {found}x, expected exactly {rx_count['exactly']}")
        if "at_least" in rx_count and found < rx_count["at_least"]:
            problems.append(f"/{rx_count['rx']}/ found {found}x, expected at least {rx_count['at_least']}")
    if e.get("no_control_chars"):
        bad = re.findall(rb"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]|\x1b|\r", res["out"])
        if bad:
            problems.append(f"control characters in the output: {sorted(set(b.hex() for b in bad))}")
    if e.get("no_invisible_format_chars"):
        bad = re.findall("[​-‏‪-‮⁦-⁩﻿]", text)
        if bad:
            problems.append(f"invisible format characters in the output: {[hex(ord(c)) for c in set(bad)]}")
    if e.get("max_seconds") and res["secs"] > e["max_seconds"]:
        problems.append(f"took {res['secs']:.1f}s, limit {e['max_seconds']}s")
    if e.get("max_line_length"):
        longest = max((len(l) for l in text.split("\n")), default=0)
        if longest > e["max_line_length"]:
            problems.append(f"a printed line is {longest} characters, limit {e['max_line_length']}")
    if e.get("deterministic") and len(res["runs"]) == 2 and res["runs"][0][1] != res["runs"][1][1]:
        problems.append("two runs on the same input printed different pages")
    if e.get("read_only"):
        if res["before"] != res["after"]:
            diff = sorted(set(res["before"]) ^ set(res["after"]) | {k for k in res["before"] if k in res["after"] and res["before"][k] != res["after"][k]})
            problems.append(f"the run wrote to the working directory: {diff[:4]}")
        if res["git_before"] != res["git_after"]:
            problems.append("the run moved HEAD")
        for call in res["gh_calls"]:
            words = set(re.findall(r"[a-z]+", call.lower()))
            if words & WRITE_VERBS or re.search(r"(-X|--method)\s*(POST|PUT|PATCH|DELETE)", call, re.I):
                problems.append(f"gh was called with a write verb: gh {call}")
    if "gh_called" in e:
        if bool(res["gh_calls"]) != e["gh_called"]:
            problems.append(f"gh_called={bool(res['gh_calls'])}, expected {e['gh_called']}")
    return problems


def load_cases(only=None):
    cases = []
    for p in sorted((HERE / "fixtures").glob("*/case.json")):
        c = json.loads(p.read_text())
        c["_dir"] = p.parent.name
        if only and not any(c["id"].startswith(o) for o in only):
            continue
        cases.append(c)
    return cases


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--bin", default=str(DEFAULT_BIN))
    ap.add_argument("--timing", action="store_true")
    ap.add_argument("--tags", help="comma-separated tags to run, e.g. spec,principle")
    a = ap.parse_args(argv)
    cases = load_cases(a.only.split(",") if a.only else None)
    if a.tags:
        want = set(a.tags.split(","))
        cases = [c for c in cases if c["tag"] in want]
    if not cases:
        print("no fixtures selected", file=sys.stderr)
        return 3
    if a.list:
        for c in cases:
            print(f"{c['id']:<34} item {str(c.get('spec_item', '-')):<3} {c['tag']:<10} {c['title']}")
        return 0
    binpath = pathlib.Path(a.bin)
    if not binpath.exists():
        print(f"NOT RUN: {binpath} does not exist (the script has not been built yet)", file=sys.stderr)
        return 3
    if not os.access(binpath, os.X_OK):
        print(f"NOT RUN: {binpath} is not executable", file=sys.stderr)
        return 3
    results = []
    for c in cases:
        if c.get("skip_if_root") and os.geteuid() == 0:
            print(f"  skip {c['id']:<34} [{c['tag']}] running as root; permissions cannot be tested")
            continue
        res = run_case(c, binpath)
        probs = check(dict(c, expect=res["expect"]), res)
        results.append((c, probs, res))
        mark = "ok  " if not probs else "FAIL"
        extra = f" ({res['secs']:.2f}s)" if a.timing else ""
        print(f"  {mark} {c['id']:<34} [{c['tag']}] {c['title']}{extra}")
        for p in probs:
            print(f"         - {p}")
    failed = [c for c, p, _ in results if p]
    by_tag = {}
    for c, p, _ in results:
        t = by_tag.setdefault(c["tag"], [0, 0])
        t[0] += 1
        t[1] += 0 if p else 1
    print()
    print(f"{len(results) - len(failed)}/{len(results)} fixtures pass. " + ", ".join(f"{k}: {v[1]}/{v[0]}" for k, v in sorted(by_tag.items())))
    items = sorted({c.get("spec_item") for c, _, _ in results if isinstance(c.get("spec_item"), int)})
    missing = [i for i in range(1, 16) if i not in items]
    if missing and not a.only and not a.tags:
        print(f"NOTE: no fixture for failure-list item(s) {missing}", file=sys.stderr)
    if failed:
        print("FAILED: " + ", ".join(c["id"] for c in failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
