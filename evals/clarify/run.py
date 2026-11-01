#!/usr/bin/env python3
"""Check that a policy asks the operator only when the answer would change the plan.

    python3 evals/clarify/run.py                       # validate the cases, score the oracle
    python3 evals/clarify/run.py --policy always-ask   # score a built-in policy
    python3 evals/clarify/run.py --transcript FILE     # score a recorded transcript (JSONL)
    python3 evals/clarify/run.py --emit oracle         # print a policy as a transcript
    python3 evals/clarify/run.py --verbose             # one line per case, not only failures
    python3 evals/clarify/run.py --selftest            # prove every refusal below still fires

Each case hides a setpoint from the agent: a preference, a constraint or a target among a few
options, with a prior over them, a loss table (operator-minutes lost by each action under each
option) and ask_cost, the attention a question takes. Asking reveals the setpoint, so the
expected value of perfect information decides it:

    EVPI = min_a E[loss(a)] - E[min_a loss(a, s)]          ask  iff  EVPI > ask_cost

and a case falls in one of three kinds, named by its file and checked against that arithmetic:
  robust  one action is best under every option (EVPI = 0): asking is waste; act.
  ask     EVPI > ask_cost: a wrong guess costs more than the question; ask.
  assume  0 < EVPI <= ask_cost: a wrong guess is cheap; act, and state the assumption.

WHAT IT CATCHES, each one counted separately and each one a case in --selftest
  unnecessary-ask  asked on a robust or assume case.
  missed-ask       acted on an ask case.
  no-assumption    acted on an assume case without stating the assumption.
  wrong-action     acted on a robust or assume case with an action that is not the best one
                   under the prior.
  missing          a case the transcript has no decision for.
  unknown-case     a decision for a case id that does not exist (a stale transcript).
  invalid          a decision that is not `ask` or `act:<action>`, an action the case does not
                   have, or a case decided twice.
  cases            a case file that is malformed, priors that do not sum to 1, a loss table
                   missing a cell, a kind label the arithmetic contradicts, an EVPI within a
                   factor of 1.5 of ask_cost (too close to call, so it would test rounding), or
                   a tie for the best action under the prior.

TRANSCRIPT FORMAT. JSON lines, one decision per case:
    {"id": "branch-name", "decision": "act:name-fix", "assumption": "fix/ prefix"}
    {"id": "paid-eval-run", "decision": "ask"}
`assumption` is optional and only required on assume cases. Blank lines are skipped.

Exit 0 when every case is decided correctly, 1 when one is not, 2 for a usage error or an
unreadable transcript, 3 when the case set itself is invalid (so a broken case set is never
read as a policy failure, or as a pass).

WHAT IT CANNOT DO. It scores the decision to ask, not the question asked or what happens after
the answer, and it assumes one question reveals the setpoint exactly; a real answer can be
partial. The losses are estimates written by a person, labelled [Estimate] in the README. It
does not run a model: a transcript is recorded elsewhere and scored here.
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CASES = os.path.join(HERE, "cases")
KINDS = ("robust", "ask", "assume")
FAILS = ("unnecessary-ask", "missed-ask", "no-assumption", "wrong-action",
         "missing", "unknown-case", "invalid")
# EVPI must clear ask_cost by this factor either way. A case near the line tests the rounding
# of the losses, not the judgment of the policy.
MARGIN = 1.5
EPS = 1e-9
POLICIES = ("oracle", "always-ask", "never-ask")


class CaseError(Exception):
    pass


def analyse(case):
    """-> expected loss per action, the prior-best action, E[loss | perfect info], EVPI, kind."""
    opts, p, loss = case["setpoint"]["options"], case["priors"], case["loss"]
    el = {a: sum(p[s] * loss[a][s] for s in opts) for a in case["actions"]}
    best_el = min(el.values())
    best = [a for a in el if el[a] - best_el < EPS]
    perfect = sum(p[s] * min(loss[a][s] for a in case["actions"]) for s in opts)
    evpi = best_el - perfect
    if evpi < EPS:
        kind = "robust"
    elif evpi > case["ask_cost"]:
        kind = "ask"
    else:
        kind = "assume"
    return {"el": el, "best": best, "best_el": best_el, "perfect": perfect,
            "evpi": max(evpi, 0.0), "kind": kind}


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def validate(case, kind):
    """Problems with one case, as strings; empty when it is usable."""
    probs = []
    for key in ("id", "task", "setpoint", "priors", "actions", "loss", "ask_cost"):
        if key not in case:
            probs.append(f"no '{key}'")
    if probs:
        return probs
    sp = case["setpoint"]
    opts = sp.get("options") if isinstance(sp, dict) else None
    if not isinstance(opts, dict) or len(opts) < 2:
        return ["setpoint.options must name at least two options"]
    acts = case["actions"]
    if not isinstance(acts, dict) or len(acts) < 2:
        return ["actions must name at least two actions"]
    pri = case["priors"]
    if not isinstance(pri, dict) or set(pri) != set(opts):
        return [f"priors must have exactly the options {sorted(opts)}"]
    if not all(_num(v) and v > 0 for v in pri.values()):
        return ["every prior must be a number above 0"]
    if abs(sum(pri.values()) - 1) > 1e-6:
        return [f"priors sum to {sum(pri.values()):g}, not 1"]
    loss = case["loss"]
    if not isinstance(loss, dict) or set(loss) != set(acts):
        return [f"loss must have a row for exactly the actions {sorted(acts)}"]
    for a, row in loss.items():
        if not isinstance(row, dict) or set(row) != set(opts):
            return [f"loss row '{a}' must have exactly the options {sorted(opts)}"]
        if not all(_num(v) and v >= 0 for v in row.values()):
            return [f"loss row '{a}' must hold numbers of 0 or more"]
    if not (_num(case["ask_cost"]) and case["ask_cost"] > 0):
        return ["ask_cost must be a number above 0"]
    r = analyse(case)
    if r["kind"] != kind:
        probs.append(f"filed as {kind}, but EVPI {r['evpi']:g} against ask_cost "
                     f"{case['ask_cost']:g} makes it {r['kind']}")
    elif kind == "ask" and r["evpi"] < MARGIN * case["ask_cost"]:
        probs.append(f"EVPI {r['evpi']:g} is within a factor of {MARGIN} of ask_cost "
                     f"{case['ask_cost']:g}: too close to call")
    elif kind == "assume" and r["evpi"] * MARGIN > case["ask_cost"]:
        probs.append(f"EVPI {r['evpi']:g} is within a factor of {MARGIN} of ask_cost "
                     f"{case['ask_cost']:g}: too close to call")
    if kind != "ask" and len(r["best"]) > 1:
        probs.append(f"actions {r['best']} tie for best under the prior, so no act is wrong")
    return probs


def load_cases(directory):
    """-> list of (kind, case). Raises CaseError listing every problem found."""
    probs, out, seen = [], [], {}
    try:
        names = sorted(n for n in os.listdir(directory) if n.endswith(".json"))
    except OSError as e:
        raise CaseError(f"cannot read {directory}: {e}")
    for n in names:
        path = os.path.join(directory, n)
        try:
            with open(path, encoding="utf-8") as f:
                doc = json.load(f)
        except (OSError, ValueError) as e:
            probs.append(f"{n}: cannot read: {e}")
            continue
        kind = doc.get("kind") if isinstance(doc, dict) else None
        if kind not in KINDS or not isinstance(doc.get("cases"), list):
            probs.append(f"{n}: needs \"kind\" (one of {', '.join(KINDS)}) and a \"cases\" list")
            continue
        for c in doc["cases"]:
            cid = c.get("id", "?") if isinstance(c, dict) else "?"
            if not isinstance(c, dict):
                probs.append(f"{n}: a case that is not an object")
                continue
            for p in validate(c, kind):
                probs.append(f"{n} {cid}: {p}")
            if cid in seen:
                probs.append(f"{n} {cid}: id also used in {seen[cid]}")
            seen[cid] = n
            out.append((kind, c))
    for k in KINDS:
        if not any(kind == k for kind, _ in out):
            probs.append(f"no {k} case: the set cannot tell a policy that never does that apart")
    if probs:
        raise CaseError("\n".join(probs))
    return out


def oracle_assumption(case, act):
    """The option the act is betting on: the most likely one under which it is best."""
    opts, loss, p = case["setpoint"]["options"], case["loss"], case["priors"]
    fits = [s for s in opts if loss[act][s] - min(loss[a][s] for a in case["actions"]) < EPS]
    s = max(fits or opts, key=lambda o: p[o])
    return f"{case['setpoint']['question']} Assuming: {s} ({opts[s]})."


def policy(name, cases):
    """-> {id: {"decision": ..., "assumption": ...}} for a built-in policy."""
    out = {}
    for _, c in cases:
        r = analyse(c)
        act = r["best"][0]
        if name == "always-ask":
            out[c["id"]] = {"decision": "ask"}
        elif name == "never-ask":
            out[c["id"]] = {"decision": f"act:{act}"}
        elif name == "oracle":
            if r["evpi"] > c["ask_cost"]:
                out[c["id"]] = {"decision": "ask"}
            else:
                out[c["id"]] = {"decision": f"act:{act}", "assumption": oracle_assumption(c, act)}
        else:
            raise ValueError(name)
    return out


def read_transcript(path):
    """-> (decisions, problems). Problems are per-line `invalid` findings; an unreadable file or
    a line that is not JSON raises ValueError naming the line, and nothing is scored."""
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().split("\n")
    except (OSError, UnicodeDecodeError) as e:
        raise ValueError(f"cannot read {path}: {e}")
    decisions, dup = {}, []
    for i, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            d = json.loads(line)
        except ValueError as e:
            raise ValueError(f"{path} line {i}: not JSON: {e}")
        if not isinstance(d, dict) or not isinstance(d.get("id"), str):
            raise ValueError(f"{path} line {i}: needs an object with a string \"id\"")
        if d["id"] in decisions:
            dup.append(d["id"])
        decisions[d["id"]] = d
    return decisions, dup


def score(cases, decisions, dup=()):
    """-> (counts, rows, regret). rows: (id, kind, verdict, detail), verdict 'ok' or a FAILS tag."""
    counts = {k: 0 for k in FAILS}
    rows, regret = [], 0.0
    known = {c["id"] for _, c in cases}
    for kind, c in cases:
        cid, r = c["id"], analyse(c)
        oracle_el = c["ask_cost"] + r["perfect"] if r["evpi"] > c["ask_cost"] else r["best_el"]
        d = decisions.get(cid)
        verdict, detail = "ok", ""
        if d is None:
            verdict, detail = "missing", "no decision"
        elif cid in dup:
            verdict, detail = "invalid", "decided more than once"
        else:
            dec = d.get("decision")
            assumption = d.get("assumption")
            if dec == "ask":
                regret += c["ask_cost"] + r["perfect"] - oracle_el
                if r["kind"] != "ask":
                    verdict = "unnecessary-ask"
                    detail = f"EVPI {r['evpi']:g} <= ask_cost {c['ask_cost']:g}"
            elif isinstance(dec, str) and dec.startswith("act:") and dec[4:] in c["actions"]:
                act = dec[4:]
                regret += r["el"][act] - oracle_el
                if r["kind"] == "ask":
                    verdict = "missed-ask"
                    detail = f"EVPI {r['evpi']:g} > ask_cost {c['ask_cost']:g}"
                elif act not in r["best"]:
                    verdict = "wrong-action"
                    detail = f"{act} (E {r['el'][act]:g}) over {r['best'][0]} (E {r['best_el']:g})"
                elif r["kind"] == "assume" and not (isinstance(assumption, str) and assumption.strip()):
                    verdict = "no-assumption"
                    detail = "acted on a guess without saying what it assumed"
            else:
                verdict = "invalid"
                detail = f"decision {dec!r}: not 'ask' or 'act:<one of {sorted(c['actions'])}>'"
        if verdict != "ok":
            counts[verdict] += 1
        rows.append((cid, kind, verdict, detail))
    for cid in sorted(set(decisions) - known):
        counts["unknown-case"] += 1
        rows.append((cid, "?", "unknown-case", "no such case"))
    return counts, rows, regret


def report(cases, counts, rows, regret, verbose, label):
    for cid, kind, verdict, detail in rows:
        if verbose or verdict != "ok":
            tag = "ok  " if verdict == "ok" else "FAIL"
            print(f"{tag}  {cid:<40} [{kind}] {'' if verdict == 'ok' else verdict + ': '}{detail}")
    n = {k: sum(1 for kind, _ in cases if kind == k) for k in KINDS}
    right = sum(1 for r in rows if r[2] == "ok")
    print(f"\n{label}: {right}/{len(cases)} cases right "
          f"({', '.join(f'{k} {n[k]}' for k in KINDS)})")
    print(f"unnecessary asks: {counts['unnecessary-ask']}  missed asks: {counts['missed-ask']}  "
          f"acts without a stated assumption: {counts['no-assumption']}  "
          f"wrong actions: {counts['wrong-action']}")
    other = [f"{k}: {counts[k]}" for k in ("missing", "unknown-case", "invalid") if counts[k]]
    if other:
        print("  ".join(other))
    print(f"expected regret against the EVPI-optimal policy: {regret:g} operator-minutes"
          + (" (over the cases decided validly)" if other else ""))
    return 0 if not any(counts.values()) else 1


def emit(decisions):
    for cid, d in decisions.items():
        print(json.dumps({"id": cid, **d}, ensure_ascii=True))


# ---------------------------------------------------------------- selftest

def selftest():
    ok = True

    def check(label, cond, detail=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"{'PASS' if cond else 'FAIL'}  {label}")
        if not cond and detail:
            print("      " + str(detail).replace("\n", "\n      ")[:1200])

    try:
        cases = load_cases(CASES)
    except CaseError as e:
        check("the case set in cases/ is valid", False, e)
        return 1
    by_id = {c["id"]: c for _, c in cases}
    n = {k: sum(1 for kind, _ in cases if kind == k) for k in KINDS}
    total = len(cases)

    # 1. The README's worked example, computed by hand before this code existed:
    #    E[force] = .7*0 + .3*240 = 72, E[merge] = 15, E[perfect] = .3*15 = 4.5, EVPI = 10.5.
    r = analyse(by_id["force-push-shared-branch"])
    check("worked example: E[loss] 72 and 15, 4.5 with perfect information, EVPI 10.5",
          abs(r["el"]["force-push"] - 72) < EPS and abs(r["el"]["merge-on-top"] - 15) < EPS
          and abs(r["perfect"] - 4.5) < EPS and abs(r["evpi"] - 10.5) < EPS, r)
    r2 = analyse(by_id["force-push-overnight"])
    check("the overnight twin has the same EVPI and is an assume case only because asking costs 60",
          abs(r2["evpi"] - 10.5) < EPS and r2["kind"] == "assume" and r["kind"] == "ask")
    check(f"the case set has 20 to 30 cases, at least 5 of each kind ({total}: {n})",
          20 <= total <= 30 and all(v >= 5 for v in n.values()))

    # 2. The three built-in policies, with counts taken from the file labels, not the arithmetic.
    def run_policy(name):
        return score(cases, policy(name, cases))

    c, rows, reg = run_policy("oracle")
    check("the oracle gets every case right, with zero regret",
          not any(c.values()) and abs(reg) < EPS, (c, reg))
    c, _, reg = run_policy("always-ask")
    want = dict.fromkeys(FAILS, 0)
    want["unnecessary-ask"] = n["robust"] + n["assume"]
    check(f"always-ask fails with {want['unnecessary-ask']} unnecessary asks and nothing else",
          c == want and reg > 0, c)
    c, _, reg = run_policy("never-ask")
    want = dict.fromkeys(FAILS, 0)
    want["missed-ask"], want["no-assumption"] = n["ask"], n["assume"]
    check(f"never-ask fails with {n['ask']} missed asks and {n['assume']} unstated assumptions",
          c == want and reg > 0, c)
    # A stakes heuristic (ask whenever something could cost 100 minutes or more) looks sensible
    # and is wrong both ways: it asks where one action is safe anyway, and on the overnight twin.
    def stakes_rule(cc):
        if max(max(row.values()) for row in cc["loss"].values()) >= 100:
            return {"decision": "ask"}
        act = analyse(cc)["best"][0]
        return {"decision": f"act:{act}", "assumption": oracle_assumption(cc, act)}
    stakes = {cid: stakes_rule(cc) for cid, cc in by_id.items()}
    c, rows, _ = score(cases, stakes)
    flagged = {cid for cid, _, v, _ in rows if v == "unnecessary-ask"}
    check("a 'high stakes means ask' policy fails, including on the overnight twin and a robust case",
          "force-push-overnight" in flagged and "leaked-token-rotate" in flagged
          and c["missed-ask"] >= 1, (c, sorted(flagged)))

    # 3. Each transcript refusal, one mutation of the oracle at a time.
    base = policy("oracle", cases)
    assume_id = next(cc["id"] for k, cc in cases if k == "assume")
    robust_id = next(cc["id"] for k, cc in cases if k == "robust")
    ask_id = next(cc["id"] for k, cc in cases if k == "ask")
    worse = [a for a in by_id[robust_id]["actions"] if a not in analyse(by_id[robust_id])["best"]][0]

    def mutated(fn):
        d = json.loads(json.dumps(base))
        fn(d)
        return d

    trials = [
        ("a whitespace assumption on an assume case", "no-assumption",
         mutated(lambda d: d[assume_id].update(assumption="   "))),
        ("no assumption key on an assume case", "no-assumption",
         mutated(lambda d: d[assume_id].pop("assumption"))),
        ("the dominated action on a robust case", "wrong-action",
         mutated(lambda d: d[robust_id].update(decision=f"act:{worse}"))),
        ("an action the case does not have", "invalid",
         mutated(lambda d: d[ask_id].update(decision="act:no-such-action"))),
        ("a bare 'act' with no action", "invalid",
         mutated(lambda d: d[robust_id].update(decision="act"))),
        ("'Ask' in another case", "invalid", mutated(lambda d: d[ask_id].update(decision="Ask"))),
        ("a case left out", "missing", mutated(lambda d: d.pop(ask_id))),
        ("a decision for a case that is gone", "unknown-case",
         mutated(lambda d: d.update({"retired-case": {"decision": "ask"}}))),
    ]
    for label, tag, dec in trials:
        c, _, _ = score(cases, dec)
        others = {k: v for k, v in c.items() if k != tag and v}
        check(f"refuses {label} ({tag})", c[tag] == 1 and not others, c)

    # 4. From the consuming end: write transcripts to files and run this script on them.
    me = [sys.executable, os.path.abspath(__file__)]
    with tempfile.TemporaryDirectory() as tmp:
        def run(*args):
            p = subprocess.run(me + list(args), capture_output=True, text=True)
            return p.returncode, p.stdout + p.stderr

        for name, want_rc, want_text in (
                ("oracle", 0, f"{total}/{total} cases right"),
                ("always-ask", 1, f"unnecessary asks: {n['robust'] + n['assume']}  missed asks: 0"),
                ("never-ask", 1, f"missed asks: {n['ask']}  acts without a stated assumption: {n['assume']}")):
            rc, out = run("--emit", name)
            path = os.path.join(tmp, f"{name}.jsonl")
            with open(path, "w", encoding="utf-8") as f:
                f.write(out)
            rc2, out2 = run("--transcript", path)
            check(f"--emit {name} then --transcript: exit {want_rc} and '{want_text}'",
                  rc == 0 and rc2 == want_rc and want_text in out2, out2)
        dup = os.path.join(tmp, "dup.jsonl")
        with open(os.path.join(tmp, "oracle.jsonl"), encoding="utf-8") as f:
            first = f.readline()
        with open(dup, "w", encoding="utf-8") as f:
            f.write(first + "\n" + first)  # the same valid line twice: still decided twice
        rc, out = run("--transcript", dup)
        check("a case decided twice is invalid, not last-one-wins", rc == 1 and "invalid: " in out, out)
        bad = os.path.join(tmp, "bad.jsonl")
        with open(bad, "w", encoding="utf-8") as f:
            f.write(first + "{not json\n")
        rc, out = run("--transcript", bad)
        check("a line that is not JSON stops the run with exit 2 and its line number",
              rc == 2 and "line 2" in out, out)
        rc, out = run("--transcript", os.path.join(tmp, "absent.jsonl"))
        check("a transcript that does not exist is exit 2, not a pass", rc == 2, out)
        empty = os.path.join(tmp, "empty.jsonl")
        open(empty, "w").close()
        rc, out = run("--transcript", empty)
        check(f"an empty transcript fails with {total} missing", rc == 1 and f"missing: {total}" in out, out)

        # 5. Each case-set refusal, on a copy of cases/.
        def case_trial(label, fn, want):
            d = os.path.join(tmp, f"cases-{len(os.listdir(tmp))}")
            shutil.copytree(CASES, d)
            fn(d)
            try:
                load_cases(d)
                got = None
            except CaseError as e:
                got = str(e)
            rc, out = run("--cases", d)
            check(f"refuses a case set with {label}", got is not None and want in got and rc == 3,
                  got or out)

        def edit(fname, f):
            def apply(d):
                p = os.path.join(d, fname)
                with open(p, encoding="utf-8") as fh:
                    doc = json.load(fh)
                f(doc)
                with open(p, "w", encoding="utf-8") as fh:
                    json.dump(doc, fh)
            return apply

        def move_first(src, dst):
            def apply(d):
                ps, pd = os.path.join(d, src), os.path.join(d, dst)
                with open(ps, encoding="utf-8") as fh:
                    a = json.load(fh)
                with open(pd, encoding="utf-8") as fh:
                    b = json.load(fh)
                b["cases"].append(a["cases"].pop(0))
                for p, doc in ((ps, a), (pd, b)):
                    with open(p, "w", encoding="utf-8") as fh:
                        json.dump(doc, fh)
            return apply

        def first_case(fname, f):
            return edit(fname, lambda doc: f(doc["cases"][0]))

        def set_cost_to_evpi(cc):
            cc["ask_cost"] = analyse(cc)["evpi"] / 1.2

        def tie(cc):
            a, b = list(cc["actions"])[:2]
            cc["loss"][b] = dict(cc["loss"][a])

        case_trial("a robust case filed as ask", move_first("robust.json", "ask.json"), "makes it robust")
        case_trial("an ask case filed as assume", move_first("ask.json", "assume.json"), "makes it ask")
        case_trial("an assume case filed as robust", move_first("assume.json", "robust.json"),
                   "makes it assume")
        case_trial("priors summing to 0.9",
                   first_case("ask.json", lambda cc: cc["priors"].update(
                       {k: v * 0.9 for k, v in cc["priors"].items()})), "not 1")
        case_trial("a loss cell missing",
                   first_case("ask.json", lambda cc: next(iter(cc["loss"].values())).popitem()),
                   "must have exactly the options")
        case_trial("a negative loss",
                   first_case("robust.json", lambda cc: next(iter(cc["loss"].values())).update(
                       {next(iter(cc["priors"])): -1})), "numbers of 0 or more")
        case_trial("EVPI within the margin of ask_cost", first_case("ask.json", set_cost_to_evpi),
                   "too close to call")
        case_trial("a tie for the best action", first_case("assume.json", tie), "tie for best")
        case_trial("an id used twice",
                   edit("assume.json", lambda doc: doc["cases"].append(dict(doc["cases"][0]))),
                   "id also used")
        case_trial("no assume cases left",
                   edit("assume.json", lambda doc: doc.update(cases=[])), "no assume case")
        case_trial("a file that is not JSON",
                   lambda d: open(os.path.join(d, "ask.json"), "a").write("}"), "cannot read")

    print(f"\nselftest: {'all checks passed' if ok else 'FAILED'}")
    return 0 if ok else 1


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--policy", choices=POLICIES)
    g.add_argument("--transcript", metavar="FILE")
    g.add_argument("--emit", choices=POLICIES)
    g.add_argument("--selftest", action="store_true")
    ap.add_argument("--cases", default=CASES, metavar="DIR")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args(argv[1:])
    if a.selftest:
        return selftest()
    try:
        cases = load_cases(a.cases)
    except CaseError as e:
        print("FAIL  cases: " + str(e).replace("\n", "\nFAIL  cases: "))
        return 3
    if a.emit:
        emit(policy(a.emit, cases))
        return 0
    if a.transcript:
        try:
            decisions, dup = read_transcript(a.transcript)
        except ValueError as e:
            print(f"cannot score: {e}", file=sys.stderr)
            return 2
        label = os.path.basename(a.transcript)
    else:
        name = a.policy or "oracle"
        decisions, dup, label = policy(name, cases), (), f"policy {name}"
    counts, rows, regret = score(cases, decisions, dup)
    return report(cases, counts, rows, regret, a.verbose, label)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except BrokenPipeError:  # `--emit ... | head` closed the pipe; the output was not wanted
        sys.exit(0)
