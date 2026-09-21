#!/usr/bin/env python3
"""Check that each skill's DESCRIPTION would route the prompts it claims.

    python3 evals/trigger/run.py             # every skill in skills/
    python3 evals/trigger/run.py --verbose   # print every case's score
    python3 evals/trigger/run.py --selftest  # prove the check still refuses bad input

A skill is loaded by its description and nothing else. The body can be perfect and still
never run, because the description did not contain the words a person actually types. So
the description is the only surface this checks, lexically, with no model involved: it is
deterministic, it costs nothing, and `--selftest` is the evidence that it can still fail.

WHAT IT CATCHES
  1. A description missing the vocabulary people use, so its own prompts score low.
  2. A description broad enough to outrank the skill that should have won.
  3. Two descriptions that share more than half their vocabulary.
  4. Omissions and stale artifacts: a skill with no cases, or cases for a skill that is gone.

WHAT IT CANNOT DO. It cannot judge meaning. Word overlap is a proxy; a real harness routes
semantically. A pass says the words are present, not that the skill is good or that it will
be chosen. A failure means FIX THE DESCRIPTION, not the case.

WRITE THE CASES FROM OUTSIDE THE DESCRIPTION. If the prompts are paraphrases of the
description, this grades the description against itself and passes for that reason. The
near-misses must share real vocabulary with the description they have to lose to; a
near-miss scoring zero proves nothing and is reported as a weak contrast.

Idea from addyosmani/agent-skills (MIT), found via Shubhamsaboo/awesome-llm-apps
(Apache-2.0). Rewritten here, not vendored.
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
SKILLS = os.path.join(ROOT, "skills")
CASES = os.path.join(HERE, "cases")

# A positive must beat the strongest near-miss by a ratio AND by an absolute floor. The
# floor matters: with a multiplicative margin alone, a contrast set that scores 0.00 waves
# everything through, which is how a check ends up able to print only one answer.
MARGIN = 1.15
FLOOR = 0.15

STOP = set("""a an the and or of to in on for with is are was were be been being it its this
that those these you your yours i me my mine we our ours us they them their he she his her
do does did done have has had can could should would shall will just very really some any all not no nor
yes if then than as at by from into out up down over under again more most other own same
so too s t what when where which who whom how why about""".split())


def stem(w):
    """Fold a word to a crude stem. Symmetric by construction: every branch ends by
    stripping a trailing 'e', so 'evaluate', 'evaluates' and 'evaluating' all land on
    'evaluat'. An earlier version folded only the plural and quietly split every silent-e
    verb into two clusters that could never match."""
    if w.endswith("ies") and len(w) > 4:
        w = w[:-3] + "y"
    elif w.endswith(("sses", "shes", "ches", "xes", "zes")):
        w = w[:-2]
    elif w.endswith("s") and not w.endswith("ss") and len(w) > 3:
        w = w[:-1]
    if w.endswith("ing") and len(w) > 5:
        w = w[:-3]
    elif w.endswith("ed") and len(w) > 4:
        w = w[:-2]
    if w.endswith("e") and len(w) > 4:
        w = w[:-1]
    return w


def words(text):
    return {stem(w) for w in re.findall(r"[a-z0-9'/]+", text.lower())
            if len(w) >= 3 and w not in STOP}


def description(skill_dir):
    """The description from SKILL.md's FRONTMATTER. A file with no frontmatter is not a
    skill any harness can load, so it is an error rather than a zero."""
    path = os.path.join(skill_dir, "SKILL.md")
    text = open(path, encoding="utf-8").read()
    fm = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not fm:
        raise ValueError(f"{path}: no frontmatter block, so no harness can load it")
    m = re.search(r"^description:\s*(.+?)(?=^[a-zA-Z_-]+:|\Z)", fm.group(1), re.S | re.M)
    if not m or not m.group(1).strip():
        raise ValueError(f"{path}: frontmatter has no description, so nothing can route to it")
    desc = re.sub(r"\s+", " ", m.group(1)).strip()
    # Every skill description in this ecosystem opens "Use when ...". A word every
    # description shares carries no routing signal, so it is dropped before scoring
    # rather than handed out as free overlap to whichever prompt happens to say "use".
    return re.sub(r"^use (this )?when\s+", "", desc, flags=re.I)


def load_cases(path):
    """Read one cases file, refusing the shapes that would pass while meaning nothing."""
    data = json.load(open(path, encoding="utf-8"))
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError(f"{path}: 'cases' must be a non-empty list")
    seen = set()
    for i, c in enumerate(cases):
        if not isinstance(c.get("id"), str) or not c["id"].strip():
            raise ValueError(f"{path}: case {i} has no id")
        if c["id"] in seen:
            raise ValueError(f"{path}: duplicate case id {c['id']!r}")
        seen.add(c["id"])
        if not isinstance(c.get("prompt"), str) or not c["prompt"].strip():
            raise ValueError(f"{path}: case {c['id']!r} has no prompt")
        if c.get("lexical") is not False and len(words(c["prompt"])) < 3:
            raise ValueError(f"{path}: case {c['id']!r} has fewer than three content words, "
                             f"which is a keyword rather than a routing test")
        if "lexical" in c and not isinstance(c["lexical"], bool):
            raise ValueError(f"{path}: case {c['id']!r} has a non-boolean 'lexical'")
        if not isinstance(c.get("should_trigger"), bool):
            raise ValueError(f"{path}: case {c['id']!r} needs should_trigger true or false, "
                             f"as a JSON boolean, not {c.get('should_trigger')!r}")
    return cases


def score(prompt, desc):
    """How much of what the person said this description covers: 0 to 1.

    An earlier version divided by the square root of the prompt length, which let a long
    near-miss with two incidental matches outscore a short, obviously-on-target prompt.
    Coverage is the question that matters — of the words they typed, how many does this
    description contain — and it is bounded, so the FLOOR below means the same thing for
    every skill."""
    return len(prompt & desc) / len(prompt) if prompt else 0.0


def check(verbose=False, out=print):
    failures = warnings = 0
    skills = {}
    for name in sorted(os.listdir(SKILLS)):
        if os.path.exists(os.path.join(SKILLS, name, "SKILL.md")):
            try:
                skills[name] = words(description(os.path.join(SKILLS, name)))
            except ValueError as e:
                out(f"FAIL  {e}")
                failures += 1
    if not skills:
        out(f"FAIL  no skills found under {SKILLS}")
        return 1

    names = sorted(skills)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            shared = len(skills[a] & skills[b]) / max(1, min(len(skills[a]), len(skills[b])))
            if shared > 0.5:
                out(f"FAIL  {a} and {b} near-collide: {shared:.0%} shared vocabulary")
                failures += 1

    # A stale artifact: cases left behind when a skill was renamed or removed.
    for f in sorted(os.listdir(CASES)) if os.path.isdir(CASES) else []:
        if f.endswith(".json") and f[:-5] not in skills:
            out(f"FAIL  evals/trigger/cases/{f} has no skill — renamed or deleted?")
            failures += 1

    for name in names:
        path = os.path.join(CASES, f"{name}.json")
        if not os.path.exists(path):
            out(f"FAIL  {name} has no cases at evals/trigger/cases/{name}.json")
            failures += 1
            continue
        try:
            cases = load_cases(path)
        except ValueError as e:
            out(f"FAIL  {e}")
            failures += 1
            continue
        hits, misses, skipped = [], [], 0
        for c in cases:
            if c.get("lexical") is False:
                # A prompt that only a semantic router could catch ("found this on HN,
                # should we use it"). Kept in the file as an honest record of what this
                # check cannot do, and excluded from the arithmetic rather than quietly
                # dragging the bar down.
                skipped += 1
                continue
            pw = words(c["prompt"])
            s = score(pw, skills[name])
            (hits if c["should_trigger"] else misses).append((s, c["id"]))
            if verbose:
                out(f"      {name:<16} {c['id']:<24} {s:5.2f} "
                    f"{'trigger' if c['should_trigger'] else 'near-miss'}")
            if c["should_trigger"]:
                ranked = sorted(((score(pw, skills[k]), k) for k in skills), reverse=True)
                top, winner = ranked[0]
                if top == 0.0:
                    out(f"FAIL  {name}: {c['id']!r} matches no description at all (0.00 everywhere)")
                    failures += 1
                elif winner != name:
                    out(f"FAIL  {name}: {c['id']!r} routes to {winner} instead ({top:.2f} vs {s:.2f})")
                    failures += 1
        if not hits or not misses:
            out(f"FAIL  {name}: cases need both a should-trigger and a near-miss to mean anything")
            failures += 1
            continue
        weakest, weak_id = min(hits)
        strongest, strong_id = max(misses)
        if weakest <= strongest or weakest - strongest < FLOOR or weakest <= strongest * MARGIN:
            out(f"FAIL  {name}: {weak_id!r} ({weakest:.2f}) does not clear the near-miss "
                f"{strong_id!r} ({strongest:.2f}) by {FLOOR} — the description is missing "
                f"words people say, or the near-miss shares too many of them")
            failures += 1
        else:
            if strongest == 0.0:
                out(f"WARN  {name}: every near-miss scores 0.00, so this contrast proves little; "
                    f"write near-misses that share real vocabulary")
                warnings += 1
            out(f"PASS  {name}: {len(hits)} prompt(s) clear {len(misses)} near-miss(es); "
                f"weakest {weakest:.2f} vs strongest {strongest:.2f}"
                + (f"; {skipped} case(s) marked non-lexical and skipped" if skipped else ""))

    out(f"\n{len(names)} skill(s), {failures} failure(s), {warnings} warning(s)")
    return 1 if failures else 0


def selftest():
    """Prove the check still refuses what it must, and leave the result as an artifact.

    Every mutation below was a real finding once. Asserting them here means the evidence
    is a command anyone can re-run, not a table in a pull request nobody reads twice.
    """
    mutations = [
        ("a vague description", "skills/repo-triage/SKILL.md",
         lambda t: re.sub(r"^description: .*$", "description: Evaluates things carefully.",
                          t, count=1, flags=re.M), "FAIL"),
        ("two colliding descriptions", "skills/hsi-operator/SKILL.md",
         lambda t: re.sub(r"^description: .*$",
                          "description: " + description(os.path.join(SKILLS, "repo-triage")),
                          t, count=1, flags=re.M), "near-collide"),
        ("a SKILL.md with no frontmatter", "skills/context-steward/SKILL.md",
         lambda t: re.sub(r"^---\n.*?\n---\n", "", t, flags=re.S), "no frontmatter"),
        ("a near-miss relabelled as a string", "evals/trigger/cases/repo-triage.json",
         lambda t: t.replace('"should_trigger": false', '"should_trigger": "false"', 1),
         "JSON boolean"),
    ]
    ok = True
    for label, rel, mutate, expect in mutations:
        with tempfile.TemporaryDirectory() as tmp:
            work = os.path.join(tmp, "repo")
            shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns(".git"))
            target = os.path.join(work, rel)
            # Read, then write. Opening the write handle inside the same expression
            # truncates the file before mutate() reads it, which silently turned three
            # of these mutations into "the file is empty" and passed for the wrong reason.
            original = open(target, encoding="utf-8").read()
            with open(target, "w", encoding="utf-8") as fh:
                fh.write(mutate(original))
            r = subprocess.run([sys.executable, os.path.join(work, "evals/trigger/run.py")],
                               capture_output=True, text=True)
            passed = r.returncode == 1 and expect in r.stdout
            ok &= passed
            print(f"{'PASS' if passed else 'FAIL'}  refuses {label} "
                  f"(exit {r.returncode}, expected 1 and {expect!r})")
    # And the unmutated tree must still pass, or the mutations proved nothing.
    r = subprocess.run([sys.executable, os.path.abspath(__file__)], capture_output=True, text=True)
    ok &= r.returncode == 0
    print(f"{'PASS' if r.returncode == 0 else 'FAIL'}  accepts the real tree (exit {r.returncode}, expected 0)")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(check(verbose="--verbose" in sys.argv))
