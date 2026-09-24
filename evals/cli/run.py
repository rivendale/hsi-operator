#!/usr/bin/env python3
"""End-to-end checks for `hsi`, run against the real CLI with real files.

    python3 evals/cli/run.py

Each case runs the actual command and asserts on its exit code and its output, because a
function returning the right value proves less than the command a person types. The cases
that matter most are the refusals: a check nobody has watched fail is a check nobody should
trust.

The clock is fixed with --today so a test written in September still means something in
March. That flag exists for this and nothing else.
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
HSI = os.path.join(ROOT, "skills", "hsi-operator", "bin", "hsi")
ITEMS = os.path.join(ROOT, "examples", "items.example.json")
SETPOINT = os.path.join(ROOT, "examples", "setpoint.example.json")


def run(*args):
    r = subprocess.run([sys.executable, HSI, *args], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def main():
    failures = 0

    def check(name, ok, detail=""):
        nonlocal failures
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            failures += 1
            print(f"      {detail.strip()[:400]}")

    with tempfile.TemporaryDirectory() as tmp:
        use = os.path.join(tmp, ".hsi", "use.json")

        rc, out = run(ITEMS)
        check("the board works with no usage record at all", rc == 0 and "need you" in out, out)

        rc, out = run(ITEMS, "--use", use, "--today", "2026-09-22")
        check("a missing usage file is a first run, not neglect",
              rc == 0 and "need you" in out and "furniture" not in out, out)

        rc, out = run("answered", "--use", use, "--today", "2026-09-22")
        check("recording an answer writes the date", rc == 0 and os.path.exists(use), out)
        got = json.load(open(use)).get("last_answered_at") if os.path.exists(use) else None
        check("and the date it wrote is the one asked for", got == "2026-09-22", str(got))

        rc, out = run(ITEMS, "--use", use, "--today", "2026-09-30")
        check("eight days later the board is still a board",
              rc == 0 and "need you" in out and "furniture" not in out, out)

        rc, out = run(ITEMS, "--use", use, "--today", "2026-10-05")
        check("thirteen days is still inside the promise",
              rc == 0 and "furniture" not in out, out)

        # The one that matters: the promise in the README, kept by the code.
        rc, out = run(ITEMS, "--use", use, "--today", "2026-10-06")
        check("fourteen days and the only item is that nobody is using this",
              rc == 0 and "furniture" in out and "need you" not in out, out)
        check("and it still says where the board went, rather than hiding it",
              "--all" in out, out)

        # Refusals. Each one was a real failure mode before it was a test.
        rc, out = run(ITEMS, "--sittng", use)
        check("a typo'd flag is refused, not ignored",
              rc == 2 and "unknown flag" in out, out)

        rc, out = run(ITEMS, "--use")
        check("a flag with no value is refused", rc == 2 and "needs a value" in out, out)

        rc, out = run("answered")
        check("recording an answer with nowhere to record it is refused",
              rc == 2 and "--use" in out, out)

        # #6: evidence marked [RECONSTRUCTED] must not score. Held back means ranked lower,
        # never dropped, and the board says what it held back.
        def items_file(name, items):
            p = os.path.join(tmp, name)
            json.dump({"items": items}, open(p, "w"))
            return p

        def held_line(out, i):
            return any(i in line and "held" in line.lower() and "RECONSTRUCTED" in line
                       for line in out.splitlines())

        def item(i, **kw):
            base = {"id": i, "kind": "DECIDE", "question": f"Question {i}?", "why_you": "judgement",
                    "options": [], "if_ignored_30d": "nothing", "blocks": [], "reversible": "yes",
                    "cost": "minutes", "deadline": None, "evidence": f"notes/{i}.md:1"}
            base.update(kw)
            return base

        recon = item("recon-big", reversible="no", blocks=["a", "b"],
                     evidence="[RECONSTRUCTED] from a compacted session summary")
        plain = item("plain-small")
        f1 = items_file("recon.json", [recon, plain])
        rc, out = run(f1, "--all")
        check("a [RECONSTRUCTED] item ranks below a plain one it would otherwise beat",
              rc == 0 and out.find("Question plain-small?") != -1
              and out.find("Question plain-small?") < out.find("Question recon-big?"), out)
        rc, out = run(f1)
        check("the board names what it held back for reconstructed evidence, on one line",
              rc == 0 and held_line(out, "recon-big"), out)
        rc, out = run(f1, "--why", "recon-big")
        check("--why shows the item is unscored because its evidence is reconstructed",
              rc == 0 and "RECONSTRUCTED" in out and "+40" not in out, out)
        f2 = items_file("recon-dated.json", [item("recon-dated", deadline="2026-10-01",
                                                  evidence="[RECONSTRUCTED] recalled date"), plain])
        rc, out = run(f2, "--all")
        check("a hard deadline does not lift a [RECONSTRUCTED] item above a plain one",
              rc == 0 and -1 < out.find("Question plain-small?") < out.find("Question recon-dated?"), out)
        f3 = items_file("recon-only.json", [recon])
        rc, out = run(f3)
        check("a board whose only item is reconstructed still shows it, and says why",
              rc == 0 and "Question recon-big?" in out and held_line(out, "recon-big"), out)

        # Found by a cross-vendor review of the first implementation: the gate must not depend
        # on the evidence being a string or on the marker's case, and an explicit null signal
        # is the same as no signal.
        f5 = items_file("recon-list.json", [item("recon-list", reversible="no", blocks=["a", "b"],
                                                 evidence=["[RECONSTRUCTED] recalled from a summary"]), plain])
        rc, out = run(f5, "--all")
        check("evidence given as a list is still held when it is reconstructed",
              rc == 0 and -1 < out.find("Question plain-small?") < out.find("Question recon-list?"), out)
        f6 = items_file("recon-lower.json", [item("recon-lower", reversible="no", blocks=["a", "b"],
                                                  evidence="[reconstructed] from memory"), plain])
        rc, out = run(f6, "--all")
        check("a lowercase marker is still held",
              rc == 0 and -1 < out.find("Question plain-small?") < out.find("Question recon-lower?"), out)
        rc, out = run(items_file("nullsignal.json", [item("null-signal", signal=None)]))
        check("an explicit null signal is a proposal, not a refusal", rc == 0 and "need you" in out, out)

        # #4: `signal` says why an item exists. `error` is a failed check against a setpoint and
        # scores a printed +25; an unknown value is refused like an unknown kind; `stale` waits
        # for the ledger (#3), because a term nothing can set is an instrument with one answer.
        err = item("check-failing", signal="error", evidence="python3 tools/check.py exits 1")
        prop = item("new-idea", signal="proposal")
        f4 = items_file("signal.json", [prop, err])
        rc, out = run(f4, "--why", "check-failing")
        check("--why prints the +25 residual for signal error", rc == 0 and "+25" in out and "residual" in out, out)
        rc, out = run(f4, "--all")
        check("an error outranks an otherwise identical proposal",
              rc == 0 and -1 < out.find("Question check-failing?") < out.find("Question new-idea?"), out)
        rc, out = run(items_file("nosignal.json", [item("no-signal")]), "--why", "no-signal")
        check("a missing signal is a proposal and adds no term", rc == 0 and "+25" not in out, out)
        rc, out = run(items_file("badsignal.json", [item("typo", signal="eror")]))
        check("an unknown signal is refused and named, not scored as a proposal",
              rc == 2 and "typo" in out and "signal" in out, out)
        rc, out = run(items_file("stale.json", [item("old-answer", signal="stale")]))
        check("signal stale is refused until the ledger can produce it",
              rc == 2 and ("ledger" in out or "#3" in out), out)
        rc, out = run("--schema")
        check("--schema documents signal", rc == 0 and '"signal"' in out, out[:300])
        rc, out = run(ITEMS)
        check("the worked example still ranks and prints a board", rc == 0 and "need you" in out, out)

        # Nothing above should have disturbed the other commands.
        rc, out = run("done", SETPOINT)
        check("hsi done still accepts the worked example",
              rc == 0 and "Done is checkable" in out, out)
        rc, out = run("--schema")
        check("--schema still prints both contracts",
              rc == 0 and '"setpoint"' in out and '"items"' in out, out[:200])

    print(f"\n{failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
