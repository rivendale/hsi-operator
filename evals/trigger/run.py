#!/usr/bin/env python3
"""Check that each skill's DESCRIPTION would route the prompts it claims.

    python3 evals/trigger/run.py            # every skill in skills/
    python3 evals/trigger/run.py --verbose  # print each case's score

A skill is loaded by its description and nothing else. The body can be perfect and
still never run, because the description did not contain the words a person actually
types. So the description is the only surface this checks, lexically, with no model
involved: it is deterministic, it runs in CI, and it costs nothing.

TWO FAILURES IT CATCHES, which are the two that happen:
  1. A description missing the vocabulary people use, so its own prompts score low.
  2. A description broad enough to outrank the skill that should have won.

WHAT IT CANNOT DO. It cannot judge meaning. Word overlap is a proxy for routing, and a
real harness routes semantically. A pass here says the words are present, not that the
skill is good or that it will be chosen. Treat a failure as "fix the description", and
never treat a pass as evidence the skill works.

Adapting an idea from addyosmani/agent-skills by way of
Shubhamsaboo/awesome-llm-apps (Apache-2.0), rewritten here.
"""
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SKILLS = os.path.join(ROOT, "skills")
CASES = os.path.join(HERE, "cases")

# A positive must beat the strongest near-miss by this much. Not tuned on anything: it
# is a margin, so a case that only just clears is reported as a warning rather than a pass.
MARGIN = 1.15

STOP = set("""a an the and or of to in on for with is are was were be been being it its this
that those these you your yours i me my we our us they them their he she his her do does did
done can could should would will shall just very really some any all not no nor yes if then
than as at by from into out up down over under again more most other own same so too s t
what when where which who whom how why about""".split())


def words(text):
    """Lowercase content words, crudely stemmed so 'compacting' matches 'compact'."""
    out = set()
    for w in re.findall(r"[a-z0-9']+", text.lower()):
        if len(w) < 3 or w in STOP:
            continue
        # Crude stemming, but symmetric: an earlier version turned "evaluates" into
        # "evaluat" while leaving "evaluate" alone, so the two never matched and the
        # check blamed the description for the tool's own bug.
        if w.endswith("ies") and len(w) > 4:
            w = w[:-3] + "y"
        elif w.endswith(("sses", "shes", "ches", "xes", "zes")):
            w = w[:-2]
        elif w.endswith("s") and not w.endswith("ss") and len(w) > 3:
            w = w[:-1]
        elif w.endswith("ing") and len(w) > 5:
            w = w[:-3]
        elif w.endswith("ed") and len(w) > 4:
            w = w[:-2]
        out.add(w)
    return out


def description(skill_dir):
    """The description field from SKILL.md frontmatter, folded blocks included."""
    text = open(os.path.join(skill_dir, "SKILL.md"), encoding="utf-8").read()
    m = re.search(r"^description:\s*(.+?)^(?=[a-zA-Z_-]+:|---)", text, re.S | re.M)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def score(prompt, desc):
    """Shared words, damped by prompt length so a long prompt cannot win by volume."""
    if not prompt:
        return 0.0
    return len(prompt & desc) / math.sqrt(len(prompt))


def main(argv):
    verbose = "--verbose" in argv
    skills = {}
    for name in sorted(os.listdir(SKILLS)):
        if os.path.exists(os.path.join(SKILLS, name, "SKILL.md")):
            d = description(os.path.join(SKILLS, name))
            if not d:
                print(f"FAIL  {name}: SKILL.md has no description, so nothing can route to it")
                return 1
            skills[name] = words(d)
    if not skills:
        print(f"no skills found under {SKILLS}")
        return 1

    failures = warnings = 0

    # Two descriptions that share most of their vocabulary cannot be told apart.
    names = sorted(skills)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            shared = len(skills[a] & skills[b]) / max(1, min(len(skills[a]), len(skills[b])))
            if shared > 0.5:
                print(f"FAIL  {a} and {b} near-collide: {shared:.0%} shared vocabulary")
                failures += 1

    for name in names:
        path = os.path.join(CASES, f"{name}.json")
        if not os.path.exists(path):
            print(f"WARN  {name} has no cases at evals/trigger/cases/{name}.json")
            warnings += 1
            continue
        cases = json.load(open(path, encoding="utf-8"))["cases"]
        hits, misses = [], []
        for c in cases:
            s = score(words(c["prompt"]), skills[name])
            (hits if c["should_trigger"] else misses).append((s, c["id"]))
            if verbose:
                print(f"      {name:<16} {c['id']:<22} {s:5.2f} "
                      f"{'should trigger' if c['should_trigger'] else 'near miss'}")
            if c["should_trigger"] and len(skills) > 1:
                best = max(skills, key=lambda k: score(words(c["prompt"]), skills[k]))
                if best != name:
                    print(f"FAIL  {name}: {c['id']!r} routes to {best} instead")
                    failures += 1
        if not hits or not misses:
            print(f"WARN  {name}: cases need both a should-trigger and a near-miss to mean anything")
            warnings += 1
            continue
        weakest, weak_id = min(hits)
        strongest, strong_id = max(misses)
        if weakest <= strongest:
            print(f"FAIL  {name}: {weak_id!r} ({weakest:.2f}) scores no higher than the "
                  f"near-miss {strong_id!r} ({strongest:.2f}) — the description is missing "
                  f"words people say, or the near-miss shares too many of them")
            failures += 1
        elif weakest <= strongest * MARGIN:
            print(f"WARN  {name}: {weak_id!r} ({weakest:.2f}) clears {strong_id!r} "
                  f"({strongest:.2f}) by less than {MARGIN:.0%}")
            warnings += 1
        else:
            print(f"PASS  {name}: {len(hits)} prompt(s) clear {len(misses)} near-miss(es); "
                  f"weakest {weakest:.2f} vs strongest {strongest:.2f}")

    print(f"\n{len(names)} skill(s), {failures} failure(s), {warnings} warning(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
