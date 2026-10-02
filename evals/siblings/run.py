#!/usr/bin/env python3
"""Check that this repo still routes to its sibling repos, and that each sibling links back.

    python3 evals/siblings/run.py                  # this repo's own files
    python3 evals/siblings/run.py --siblings DIR   # and each sibling, checked out at DIR/<name>
    python3 evals/siblings/run.py --selftest       # prove every refusal below still fires

This repo is the one a person points an agent at. The siblings are maintained separately, so
the only thing joining them is a handful of links, and a link nobody checks rots silently:
the hub once named one sibling, in a docs page, and no sibling named the hub.

`repos.json` holds the routing facts (name, URL, where to start, what each is for, when to
read it). Pinned commits live only in `.claude-plugin/marketplace.json`, so each fact has
one home and this check compares the two.

WHAT IT CATCHES, each one a case in --selftest
  index             repos.json missing, unreadable, a row without name, url, start, purpose or
                    read_when, a URL that names a different repo, or a name listed twice.
  hub-omits         README.md or AGENTS.md here has no link to a sibling's URL. A lookalike
                    such as `.../local-ai-extra` does not count.
  unpinned          a marketplace entry with a git source (github, url, git-subdir) and no
                    40-hex `sha`. A `ref` alone is a branch, and a branch is tracking, not a
                    reviewed commit. Any other non-relative source is refused the same way.
  unknown-entry     a marketplace entry that is neither this repo nor a row in repos.json.
  drift             a marketplace entry whose description differs from its repos.json purpose.
  version-pin       a `version` in plugin.json or in any marketplace entry. Claude Code reads
                    the manifest's version first and treats an unchanged string as "no
                    update", so users stay on their cached copy however many commits land.
                    This repo pins by commit instead.
  missing-sibling   --siblings was given and a sibling's directory is not there.
  pin-unverifiable  a sibling is pinned, and the pinned commit is not in its checkout (or the
                    checkout is not a git repository).
  missing-start     the file repos.json says to start at does not exist in the sibling.
  no-backlink       a sibling's README.md or AGENTS.md has no link to this repo in its first
                    12 lines. A reader who stops after the title should still find the hub.

  Backlinks are read at the pinned commit when there is one, else at the checkout's HEAD, so
  a `git clone --filter=blob:none --no-checkout` is enough. Without --siblings they are not
  checked, and the output says SKIP rather than passing quietly.

WHAT IT CANNOT DO. It proves the links exist, not that the routing is right: whether a
sibling's purpose line still describes it is read by a person. It does not fetch anything;
CI clones the siblings first.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
BACKLINK_LINES = 12
GIT_SOURCES = ("github", "url", "git-subdir")
SHA = re.compile(r"^[0-9a-f]{40}$")
FIELDS = ("name", "url", "start", "purpose", "read_when")


def link_to(url, text):
    """True when `text` holds a markdown link whose target is `url` or a path under it."""
    return re.search(r"\]\(" + re.escape(url) + r"(?:[)/#])", text) is not None


def read(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return None


def load_json(path):
    text = read(path)
    if text is None:
        return None, "missing"
    try:
        return json.loads(text), None
    except ValueError as exc:
        return None, f"not valid JSON ({exc})"


def git(repo, *args):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    return r.returncode, r.stdout


def is_git(repo):
    return git(repo, "rev-parse", "--git-dir")[0] == 0


def sibling_file(repo, rev, rel):
    """A file's text at `rev` (a commit, or HEAD), or from disk when `repo` is not git."""
    if rev is None:
        return read(os.path.join(repo, rel))
    code, out = git(repo, "show", f"{rev}:{rel}")
    return out if code == 0 else None


def check(root, siblings_dir):
    fails = []

    def fail(tag, msg):
        fails.append(tag)
        print(f"FAIL  {tag}: {msg}")

    # --- the index -------------------------------------------------------------------
    index, err = load_json(os.path.join(root, "repos.json"))
    if err:
        fail("index", f"repos.json {err}")
        return fails
    hub = index.get("hub") if isinstance(index, dict) else None
    repos = index.get("repos") if isinstance(index, dict) else None
    if not isinstance(hub, dict) or not all(isinstance(hub.get(k), str) and hub.get(k)
                                            for k in ("name", "url", "start")):
        fail("index", "repos.json needs a hub object with name, url and start")
        return fails
    if not isinstance(repos, list) or not repos:
        fail("index", "repos.json needs a non-empty repos list")
        return fails
    good, seen = [], set()
    for i, row in enumerate(repos):
        where = f"repos[{i}]"
        if not isinstance(row, dict):
            fail("index", f"{where} is not an object")
            continue
        missing = [k for k in FIELDS[:4] if not (isinstance(row.get(k), str) and row[k].strip())]
        rw = row.get("read_when")
        if not (isinstance(rw, list) and rw and all(isinstance(x, str) and x.strip() for x in rw)):
            missing.append("read_when")
        if missing:
            fail("index", f"{where} lacks {', '.join(missing)}")
            continue
        if not re.fullmatch(r"https://github\.com/[\w.-]+/" + re.escape(row["name"]), row["url"]):
            fail("index", f"{where} url {row['url']} does not name the repo {row['name']}")
            continue
        if row["name"] in seen or row["name"] == hub["name"]:
            fail("index", f"{row['name']} is listed twice, or is the hub itself")
            continue
        seen.add(row["name"])
        good.append(row)
    if not os.path.exists(os.path.join(root, hub["start"])):
        fail("index", f"hub start file {hub['start']} does not exist here")
    if len(good) == len(repos):
        print(f"PASS  index: {len(good)} sibling(s) read from repos.json")
    by_name = {r["name"]: r for r in good}

    # --- this repo names every sibling ---------------------------------------------------
    for page in ("README.md", "AGENTS.md"):
        text = read(os.path.join(root, page)) or ""
        absent = [r["name"] for r in good if not link_to(r["url"], text)]
        if absent:
            fail("hub-omits", f"{page} has no link to {', '.join(absent)}")
        else:
            print(f"PASS  hub links: {page} links every sibling")

    # --- manifests ------------------------------------------------------------------------
    pins = {}
    plugin, err = load_json(os.path.join(root, ".claude-plugin", "plugin.json"))
    if plugin is not None and "version" in plugin:
        fail("version-pin", f"plugin.json sets version {plugin['version']!r}; users stay on "
                            f"their cached copy until it changes. Pin by commit instead")
    market, err = load_json(os.path.join(root, ".claude-plugin", "marketplace.json"))
    if err:
        fail("unpinned", f"marketplace.json {err}")
        market = {}
    entries = market.get("plugins", []) if isinstance(market, dict) else []
    for e in entries:
        name = e.get("name", "?")
        if "version" in e:
            fail("version-pin", f"marketplace entry {name} sets version {e['version']!r}")
        src = e.get("source")
        if isinstance(src, str):
            if name != hub["name"]:
                fail("unknown-entry", f"marketplace entry {name} has a relative source; only "
                                      f"{hub['name']} lives in this repo")
            continue
        kind = src.get("source") if isinstance(src, dict) else None
        if kind not in GIT_SOURCES or not SHA.match(str(src.get("sha", ""))):
            fail("unpinned", f"marketplace entry {name} ({kind or 'no'} source) has no 40-hex "
                             f"sha; a ref alone tracks a branch")
            continue
        if name not in by_name:
            fail("unknown-entry", f"marketplace entry {name} is not in repos.json")
            continue
        if e.get("description") != by_name[name]["purpose"]:
            fail("drift", f"marketplace entry {name}: description differs from its repos.json "
                          f"purpose")
            continue
        pins[name] = src["sha"]
    if not any(t in fails for t in ("version-pin", "unpinned", "unknown-entry", "drift")):
        pinned = f"{len(pins)} sibling pin(s), each a 40-hex sha" if pins else "no sibling pinned"
        print(f"PASS  manifests: no version field; {pinned}")

    # --- each sibling links back ------------------------------------------------------------
    if siblings_dir is None:
        print("SKIP  backlinks: not checked; pass --siblings DIR (CI clones each sibling there)")
        return fails
    for r in good:
        repo = os.path.join(siblings_dir, r["name"])
        if not os.path.isdir(repo):
            fail("missing-sibling", f"{repo} does not exist; clone {r['url']} there")
            continue
        git_repo = is_git(repo)
        rev = pins.get(r["name"])
        if rev:
            if not git_repo or git(repo, "cat-file", "-e", f"{rev}^{{commit}}")[0] != 0:
                fail("pin-unverifiable", f"{r['name']} is pinned at {rev[:12]}, which its "
                                         f"checkout does not contain")
                continue
        elif git_repo:
            rev = "HEAD"
        at = rev[:12] if rev and rev != "HEAD" else ("HEAD" if rev else "the working tree")
        if sibling_file(repo, rev, r["start"]) is None:
            fail("missing-start", f"{r['name']} has no {r['start']} at {at}")
        ok = True
        for page in ("README.md", "AGENTS.md"):
            text = sibling_file(repo, rev, page)
            head = "\n".join((text or "").splitlines()[:BACKLINK_LINES])
            if not link_to(hub["url"], head):
                ok = False
                fail("no-backlink", f"{r['name']}/{page} at {at} has no link to {hub['url']} "
                                    f"in its first {BACKLINK_LINES} lines")
        if ok:
            print(f"PASS  backlink: {r['name']} at {at}")
    return fails


# --------------------------------------------------------------------------------------------
# selftest: the failure list above, as mutations that must each be refused
# --------------------------------------------------------------------------------------------

def _edit_json(rel, fn):
    def apply(work):
        path = os.path.join(work, rel)
        data = json.loads(read(path))
        fn(data)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
    return apply


def _edit_text(rel, fn):
    def apply(work):
        path = os.path.join(work, rel)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(fn(read(path)))
    return apply


def _index():
    return json.loads(read(os.path.join(ROOT, "repos.json")))


def _siblings(tmp, hub_url, names, page_text=None, git_for=()):
    """Plain sibling directories with a correct backlink, unless page_text overrides one.

    A name in git_for becomes a one-commit git repository; returns {name: sha} for those."""
    base = os.path.join(tmp, "siblings")
    shas = {}
    good = f"# x\n\n> Start at [hub]({hub_url}).\n"
    for n in names:
        d = os.path.join(base, n)
        os.makedirs(d, exist_ok=True)
        for page in ("README.md", "AGENTS.md"):
            text = (page_text or {}).get((n, page), good)
            with open(os.path.join(d, page), "w", encoding="utf-8") as fh:
                fh.write(text)
        if n in git_for:
            env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid",
                       GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")
            for cmd in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "fixture"]):
                subprocess.run(["git", "-C", d, *cmd], check=True, env=env, capture_output=True)
            shas[n] = git(d, "rev-parse", "HEAD")[1].strip()
    return base, shas


def _pin(name, sha, description=None, **extra):
    def fn(m):
        purpose = next((r["purpose"] for r in _index()["repos"] if r["name"] == name), "")
        src = {"source": "github", "repo": f"owner/{name}", "ref": "main"}
        if sha:
            src["sha"] = sha
        entry = {"name": name, "description": description or purpose, "source": src}
        entry.update(extra)
        m["plugins"].append(entry)
    return _edit_json(".claude-plugin/marketplace.json", fn)


def selftest():
    idx = _index()
    hub_url, names = idx["hub"]["url"], [r["name"] for r in idx["repos"]]
    first, last = idx["repos"][0], idx["repos"][-1]
    lookalike = first["url"] + "-extra"
    buried = "# x\n" + "\n" * 40 + f"[hub]({hub_url})\n"

    # (label, mutation of the copied repo or None, siblings spec or None, expected tag)
    # siblings spec: dict(page_text=..., git_for=..., drop=..., pin=...) built per case.
    cases = [
        ("the real tree", None, None, None),
        ("the real tree, every sibling linking back", None, {}, None),
        ("a sibling pinned to a commit its checkout holds", "PIN", {"git_for": [first["name"]]},
         None),
        ("repos.json missing", lambda w: os.remove(os.path.join(w, "repos.json")), None, "index"),
        ("a row with an empty read_when",
         _edit_json("repos.json", lambda d: d["repos"][0].update(read_when=[])), None, "index"),
        ("a URL naming a different repo",
         _edit_json("repos.json", lambda d: d["repos"][0].update(url=last["url"])), None, "index"),
        ("a sibling listed twice",
         _edit_json("repos.json", lambda d: d["repos"].append(dict(d["repos"][0]))), None, "index"),
        ("README.md drops a sibling",
         _edit_text("README.md", lambda t: t.replace(f"]({last['url']}", "](#")), None,
         "hub-omits"),
        ("AGENTS.md drops a sibling",
         _edit_text("AGENTS.md", lambda t: t.replace(f"]({first['url']}", "](#")), None,
         "hub-omits"),
        ("README.md links a lookalike instead",
         _edit_text("README.md", lambda t: t.replace(f"]({first['url']}", f"]({lookalike}")),
         None, "hub-omits"),
        ("unpinned: a github entry with ref main and no sha", _pin(first["name"], None), None,
         "unpinned"),
        ("a pin that is not 40 hex", _pin(first["name"], "abc123"), None, "unpinned"),
        ("an entry nobody indexed", _pin("not-a-sibling", "0" * 40), None, "unknown-entry"),
        ("an entry whose description drifted", _pin(first["name"], "0" * 40, "Something else."),
         None, "drift"),
        ("plugin.json pins a version",
         _edit_json(".claude-plugin/plugin.json", lambda d: d.update(version="0.1.0")), None,
         "version-pin"),
        ("a marketplace entry pins a version",
         _edit_json(".claude-plugin/marketplace.json",
                    lambda d: d["plugins"][0].update(version="1.0.0")), None, "version-pin"),
        ("--siblings without one sibling", None, {"drop": last["name"]}, "missing-sibling"),
        ("a pin on a sibling that is not a git checkout", "PIN", {}, "pin-unverifiable"),
        ("a pin the sibling's history does not hold", "PIN-WRONG", {"git_for": [first["name"]]},
         "pin-unverifiable"),
        ("a start file that is not there",
         _edit_json("repos.json", lambda d: d["repos"][0].update(start="no-such-file.md")), {},
         "missing-start"),
        ("no-backlink: a sibling README without the hub", None,
         {"page_text": {(first["name"], "README.md"): "# x\n\nNo link here.\n"}}, "no-backlink"),
        ("a backlink buried past the first lines", None,
         {"page_text": {(last["name"], "AGENTS.md"): buried}}, "no-backlink"),
    ]
    ok = True
    for label, mutate, sib, expect in cases:
        with tempfile.TemporaryDirectory() as tmp:
            work = os.path.join(tmp, "repo")
            shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns(".git"))
            args = [sys.executable, os.path.join(work, "evals", "siblings", "run.py")]
            if sib is not None:
                keep = [n for n in names if n != sib.get("drop")]
                base, shas = _siblings(tmp, hub_url, keep, sib.get("page_text"),
                                       sib.get("git_for", ()))
                args += ["--siblings", base]
            if mutate == "PIN":
                # Pin the first sibling to its fixture commit, or, with no fixture repository,
                # to a commit that cannot be there.
                mutate = _pin(first["name"], shas.get(first["name"], "f" * 40))
            elif mutate == "PIN-WRONG":
                mutate = _pin(first["name"], "f" * 40)
            before = {p: read(os.path.join(work, p)) for p in
                      ("repos.json", "README.md", "AGENTS.md", ".claude-plugin/plugin.json",
                       ".claude-plugin/marketplace.json")}
            if mutate:
                mutate(work)
                after = {p: read(os.path.join(work, p)) for p in before}
                if after == before:
                    # Unchanged, it would be checked as the real tree and prove nothing.
                    ok = False
                    print(f"FAIL  could not apply: {label}")
                    continue
            r = subprocess.run(args, capture_output=True, text=True)
            if expect is None:
                passed = r.returncode == 0 and "FAIL" not in r.stdout
                want = "exit 0, no FAIL"
            else:
                passed = r.returncode == 1 and f"FAIL  {expect}:" in r.stdout
                want = f"exit 1 and '{expect}'"
            ok &= passed
            print(f"{'PASS' if passed else 'FAIL'}  {'accepts' if expect is None else 'refuses'} "
                  f"{label} (exit {r.returncode}, expected {want})")
            if not passed:
                print("      " + r.stdout.strip().replace("\n", "\n      ")[:800])
    return 0 if ok else 1


def main(argv):
    if argv[1:2] == ["--selftest"]:
        return selftest()
    siblings = None
    if argv[1:2] == ["--siblings"] and len(argv) == 3:
        siblings = os.path.abspath(argv[2])
    elif len(argv) > 1:
        print(__doc__.split("\n\n")[1])
        return 2
    fails = check(ROOT, siblings)
    print(f"\n{len(fails)} failure(s)" + ("" if siblings else "; backlinks not checked"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
