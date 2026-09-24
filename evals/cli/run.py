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
