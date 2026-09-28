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
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import time
from html.parser import HTMLParser
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
HSI = os.path.join(ROOT, "skills", "hsi-operator", "bin", "hsi")
ITEMS = os.path.join(ROOT, "examples", "items.example.json")
SETPOINT = os.path.join(ROOT, "examples", "setpoint.example.json")
EXAMPLE_LEDGER = os.path.join(ROOT, "examples", "ledger.example.jsonl")
TIMELINE_LEDGER = os.path.join(ROOT, "examples", "timeline.example.jsonl")
TIMELINE_PAGE = os.path.join(ROOT, "examples", "timeline.example.html")
LEDGER_ADAPTER = os.path.join(ROOT, "adapters", "ledger", "collect.py")


def run(*args, input=None):
    r = subprocess.run([sys.executable, HSI, *args], capture_output=True, text=True, input=input)
    return r.returncode, r.stdout + r.stderr


def run_adapter(*args):
    r = subprocess.run([sys.executable, LEDGER_ADAPTER, *args], capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


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
        # scores a printed +25; an unknown value is refused like an unknown kind. `stale` was
        # refused here until the ledger (#3) could produce it; it is accepted now, tested below.
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
        rc, out = run("--schema")
        check("--schema documents signal", rc == 0 and '"signal"' in out, out[:300])
        rc, out = run(ITEMS)
        check("the worked example still ranks and prints a board", rc == 0 and "need you" in out, out)

        # #1, the owner's call (2026-09-24): "failing check i think outranks dated proposal as it
        # needs fixing before we move on - i don't want to leave bugs/issues behind". A residual
        # beats a deadline; proposals keep deadline-first among themselves.
        dated_prop = item("dated-proposal", deadline="2026-09-25", reversible="no")
        undated_err = item("undated-error", signal="error", evidence="python3 tools/check.py exits 1")
        f7 = items_file("errors-first.json", [dated_prop, undated_err])
        rc, out = run(f7, "--all")
        check("an undated error outranks a dated proposal",
              rc == 0 and -1 < out.find("Question undated-error?") < out.find("Question dated-proposal?"), out)
        rc, out = run(f7)
        check("and it is first on the default board too",
              rc == 0 and out.find("Question undated-error?") != -1
              and out.find("Question undated-error?") < out.find("Question dated-proposal?"), out)
        rule = out.split("\n\n")[0].lower()
        check("the printed ranking rule says errors come first",
              rc == 0 and "error" in rule and rule.find("error") < rule.find("deadline"), out)
        dated_err = item("dated-error", signal="error", deadline="2026-10-20", evidence="python3 tools/other.py exits 1")
        f8 = items_file("two-errors.json", [undated_err, dated_err, dated_prop])
        rc, out = run(f8, "--all")
        check("among errors, a dated one comes before an undated one",
              rc == 0 and -1 < out.find("Question dated-error?") < out.find("Question undated-error?")
              < out.find("Question dated-proposal?"), out)
        held_err = item("held-error", signal="error", evidence="[RECONSTRUCTED] recalled failure")
        f9 = items_file("held-error.json", [held_err, dated_prop])
        rc, out = run(f9, "--all")
        check("a reconstructed error is still held below direct evidence",
              rc == 0 and -1 < out.find("Question dated-proposal?") < out.find("Question held-error?"), out)
        p1 = item("prop-late", deadline="2026-11-01"); p2 = item("prop-soon", deadline="2026-10-01")
        rc, out = run(items_file("props.json", [p1, p2]), "--all")
        check("proposals keep deadline-first order among themselves",
              rc == 0 and -1 < out.find("Question prop-soon?") < out.find("Question prop-late?"), out)
        rc, out = run(f7, "--why", "undated-error")
        check("--why says an error ranks ahead of every proposal",
              rc == 0 and "ahead" in out.lower() and "proposal" in out.lower(), out)

        # Nothing above should have disturbed the other commands.
        rc, out = run("done", SETPOINT)
        check("hsi done still accepts the worked example",
              rc == 0 and "Done is checkable" in out, out)
        rc, out = run("--schema")
        check("--schema still prints both contracts",
              rc == 0 and '"setpoint"' in out and '"items"' in out, out[:200])

        # #3: the ledger. `hsi record` refuses an answer that is not accountable: the
        # operator's own words and the reasoning behind them, a real kind and basis, a real
        # date, and a stated invalidation condition. Written before any of it exists.
        def answer(item_id, **kw):
            a = {
                "item_id": item_id,
                "setpoint_id": None,
                "question": f"Keep doing the thing for {item_id}?",
                "answer": "Yes, keep doing it",
                "words": "yeah let's keep doing that, it's working",
                "reasoning": "Nothing has changed since we last looked, and the numbers still hold.",
                "kind": "DECIDE",
                "date": "2026-09-24",
                "invalidated_by": "the underlying numbers change",
                "basis": "Data",
            }
            a.update(kw)
            return a

        def omit(d, *keys):
            d = dict(d)
            for k in keys:
                d.pop(k, None)
            return d

        def answer_file(name, obj):
            p = os.path.join(tmp, name)
            json.dump(obj, open(p, "w"))
            return p

        def ledger_lines(path):
            if not os.path.exists(path):
                return []
            return [json.loads(l) for l in open(path) if l.strip()]

        bad_ledger = os.path.join(tmp, "ledger-validate.jsonl")

        rc, out = run("record", "--ledger", bad_ledger, "--from",
                      answer_file("no-words.json", omit(answer("no-words"), "words")))
        check("a ledger answer missing words is refused", rc == 2 and "words" in out, out)

        rc, out = run("record", "--ledger", bad_ledger, "--from",
                      answer_file("blank-words.json", answer("blank-words", words="   ")))
        check("a ledger answer with blank words is refused", rc == 2 and "words" in out, out)

        rc, out = run("record", "--ledger", bad_ledger, "--from",
                      answer_file("no-reasoning.json", omit(answer("no-reasoning"), "reasoning")))
        check("a ledger answer missing reasoning is refused", rc == 2 and "reasoning" in out, out)

        rc, out = run("record", "--ledger", bad_ledger, "--from",
                      answer_file("blank-reasoning.json", answer("blank-reasoning", reasoning="")))
        check("a ledger answer with blank reasoning is refused", rc == 2 and "reasoning" in out, out)

        rc, out = run("record", "--ledger", bad_ledger, "--from",
                      answer_file("bad-kind.json", answer("bad-kind", kind="MAYBE")))
        check("an unknown kind is refused and named", rc == 2 and "kind" in out, out)

        rc, out = run("record", "--ledger", bad_ledger, "--from",
                      answer_file("bad-basis.json", answer("bad-basis", basis="Vibes")))
        check("an unknown basis is refused and named", rc == 2 and "basis" in out, out)

        rc, out = run("record", "--ledger", bad_ledger, "--from",
                      answer_file("bad-date.json", answer("bad-date", date="not-a-date")))
        check("a date that is not a date is refused", rc == 2 and "date" in out, out)

        # Review finding, 2026-09-24: an answer carrying a stray top-level `invalidated` key
        # (one letter from `invalidated_by`) was appended, then read back as a malformed
        # invalidation row, and every later command on that ledger failed. Append-only means
        # no in-tool recovery, so the refusal has to happen before the write.
        poison_ledger = os.path.join(tmp, "ledger-poison.jsonl")
        rc, out = run("record", "--ledger", poison_ledger, "--from",
                      answer_file("healthy-first.json", answer("healthy-first")))
        rc, out = run("record", "--ledger", poison_ledger, "--from",
                      answer_file("poison.json", answer("poison", invalidated="oops")))
        check("an answer with a stray top-level invalidated key is refused before append",
              rc == 2 and "invalidated" in out and len(ledger_lines(poison_ledger)) == 1, out)
        rc, out = run("record", "--ledger", poison_ledger, "--lookup", "healthy-first")
        check("the ledger still reads after that refusal", rc == 0 and "keep doing" in out, out)

        rc, out = run("record", "--ledger", bad_ledger, "--from",
                      answer_file("no-invalidated-by.json",
                                  omit(answer("no-invalidated-by"), "invalidated_by")))
        check("an answer missing invalidated_by is refused",
              rc == 2 and "invalidated_by" in out, out)

        rc, out = run("record", "--ledger", bad_ledger, "--from",
                      answer_file("good-after-bad.json", answer("good-after-bad")))
        check("a valid answer still works on a ledger that only ever saw refused ones",
              rc == 0, out)
        check("none of the eight invalid answers above ever reached the ledger, only the valid one",
              [r.get("item_id") for r in ledger_lines(bad_ledger)] == ["good-after-bad"],
              str(ledger_lines(bad_ledger)))

        # The standing answer is an item's latest row. Re-answering it silently would let a
        # stale judgment be overwritten with nothing to say anyone reconsidered it.
        flow_ledger = os.path.join(tmp, "ledger-flow.jsonl")
        item_x = "vendor-choice"

        rc, out = run("record", "--ledger", flow_ledger, "--from",
                      answer_file("x1.json", answer(item_x)))
        check("the first answer for an item is recorded", rc == 0, out)

        rc, out = run("record", "--ledger", flow_ledger, "--from",
                      answer_file("x2.json", answer(item_x, answer="No, switch vendors")))
        check("re-answering a standing item without --supersede is refused",
              rc == 2 and "supersede" in out.lower(), out)

        rc, out = run("record", "--ledger", flow_ledger, "--supersede",
                      "the vendor raised prices 40%",
                      "--from", answer_file("x3.json", answer(item_x, answer="No, switch vendors")))
        check("--supersede lets a standing answer be re-answered", rc == 0, out)
        rows = ledger_lines(flow_ledger)
        last_row = rows[-1] if rows else {}
        check("--supersede's reason is stored on the new row as supersedes_reason",
              last_row.get("supersedes_reason") == "the vendor raised prices 40%", str(last_row))

        rc, out = run("record", "--ledger", flow_ledger, "--today", "2026-09-24",
                      "--invalidate", item_x, "--evidence", "the new vendor's contract fell through")
        check("invalidating the standing answer is recorded", rc == 0, out)

        rc, out = run("record", "--ledger", flow_ledger, "--today", "2026-09-24",
                      "--invalidate", item_x, "--evidence", "one more time")
        check("invalidating an already-invalidated item is refused",
              rc == 2 and "invalidat" in out.lower(), out)

        rc, out = run("record", "--ledger", flow_ledger, "--from",
                      answer_file("x4.json", answer(item_x, answer="Back to the original vendor")))
        check("an item may be answered again after its standing answer is invalidated, "
              "without --supersede", rc == 0, out)

        # --invalidate has its own refusals: nothing to invalidate, and evidence that says
        # nothing.
        rc, out = run("record", "--ledger", os.path.join(tmp, "ledger-never-answered.jsonl"),
                      "--invalidate", "never-answered", "--evidence", "something happened")
        check("invalidating an item with no standing answer is refused",
              rc == 2 and "standing answer" in out.lower(), out)

        blank_ev_ledger = os.path.join(tmp, "ledger-blank-evidence.jsonl")
        run("record", "--ledger", blank_ev_ledger, "--from",
            answer_file("blank-ev-item.json", answer("blank-ev-item")))
        rc, out = run("record", "--ledger", blank_ev_ledger, "--invalidate", "blank-ev-item",
                      "--evidence", "   ")
        check("invalidating with blank evidence is refused",
              rc == 2 and "evidence" in out.lower(), out)

        # A malformed line stops the command cold, with the line number, rather than being
        # skipped -- skipping it would silently drop whatever it recorded.
        malformed_ledger = os.path.join(tmp, "ledger-malformed.jsonl")
        with open(malformed_ledger, "w") as f:
            f.write(json.dumps(answer("first-item")) + "\n")
            f.write("{not json at all\n")
            f.write(json.dumps(answer("third-item")) + "\n")
        rc, out = run("record", "--ledger", malformed_ledger, "--lookup", "first-item")
        check("a malformed ledger line stops the command with its line number, not skipped",
              rc == 2 and "line 2" in out.lower(), out)

        # Happy paths: --from a file and from stdin, --lookup, and a ledger that does not
        # exist yet being no different from an empty one.
        lookup_ledger = os.path.join(tmp, "ledger-lookup.jsonl")
        run("record", "--ledger", lookup_ledger, "--from", answer_file("lookup-item.json",
            answer("lookup-item", words="we're keeping the current plan, it still fits",
                   reasoning="Costs are flat and nobody has asked for more capacity.")))
        rc, out = run("record", "--ledger", lookup_ledger, "--lookup", "lookup-item")
        check("--lookup prints the operator's own words",
              rc == 0 and "we're keeping the current plan, it still fits" in out, out)
        check("--lookup prints the reasoning",
              "Costs are flat and nobody has asked for more capacity." in out, out)

        rc, out = run("record", "--ledger", lookup_ledger, "--lookup", "no-such-item")
        check("--lookup on an absent item exits 1 and states the absence",
              rc == 1 and "no standing answer for no-such-item" in out.lower(), out)

        rc, out = run("record", "--ledger", os.path.join(tmp, "never-created.jsonl"),
                      "--lookup", "anything")
        check("a missing ledger file is treated as an empty ledger, not an error",
              rc == 1 and "no standing answer for anything" in out.lower(), out)

        rc, out = run("record", "--ledger", lookup_ledger, "--today", "2026-09-24",
                      "--invalidate", "lookup-item", "--evidence", "the plan changed in October")
        check("invalidating the lookup item works", rc == 0, out)
        rc, out = run("record", "--ledger", lookup_ledger, "--lookup", "lookup-item")
        check("--lookup says an invalidated answer has been invalidated, with its evidence",
              rc == 0 and "invalidat" in out.lower() and "the plan changed in October" in out, out)

        stdin_ledger = os.path.join(tmp, "ledger-stdin.jsonl")
        rc, out = run("record", "--ledger", stdin_ledger, "--from", "-",
                      input=json.dumps(answer("from-stdin")))
        check("--from - reads the answer from stdin", rc == 0, out)
        check("the stdin answer actually reached the ledger",
              any(r.get("item_id") == "from-stdin" for r in ledger_lines(stdin_ledger)), "")

        nested_ledger = os.path.join(tmp, "new-dir", "deeper", "ledger.jsonl")
        rc, out = run("record", "--ledger", nested_ledger, "--from",
                      answer_file("nested.json", answer("nested-item")))
        check("--from creates the ledger file and its directory when neither exists",
              rc == 0 and os.path.exists(nested_ledger), out)

        rc, out = run("--schema")
        check("--schema documents the ledger contract beside items and setpoint",
              rc == 0 and '"ledger"' in out and '"items"' in out and '"setpoint"' in out, out[:300])

        # #4: a standing answer whose condition fired becomes signal: stale, worth +20, and
        # ranked with proposals -- below every error, per #28's rule that errors come first.
        stale_err = item("live-error", signal="error", evidence="python3 tools/check.py exits 1")
        stale_it = item("stale-item", signal="stale")
        plain_prop = item("plain-prop")
        f_stale = items_file("stale-ranked.json", [plain_prop, stale_it, stale_err])
        rc, out = run(f_stale, "--all")
        check("signal stale is accepted rather than refused", rc == 0, out)
        check("an error still outranks a stale item",
              rc == 0 and -1 < out.find("Question live-error?") < out.find("Question stale-item?"), out)
        check("a stale item outranks an equivalent plain proposal",
              rc == 0 and -1 < out.find("Question stale-item?") < out.find("Question plain-prop?"), out)
        rc, out = run(f_stale, "--why", "stale-item")
        check("--why prices a stale item at +20 for the invalidated standing answer",
              rc == 0 and "+20" in out and "invalidated standing answer" in out, out)

        # The round trip #3 -> #4 -> #7: a standing answer is invalidated, the adapter turns
        # that into a stale item, and the board puts it first with the +20 visible.
        rt_ledger = os.path.join(tmp, "ledger-roundtrip.jsonl")
        rc, out = run("record", "--ledger", rt_ledger, "--from",
                      answer_file("rt1.json", answer("renewal-terms", kind="APPROVE")))
        check("round trip: recording the standing answer", rc == 0, out)
        rc, out = run("record", "--ledger", rt_ledger, "--today", "2026-09-24",
                      "--invalidate", "renewal-terms",
                      "--evidence", "the counterparty sent new terms")
        check("round trip: invalidating it", rc == 0, out)

        rc, adapter_out, adapter_err = run_adapter(rt_ledger)
        check("round trip: the ledger adapter runs against the invalidated ledger",
              rc == 0, adapter_err)
        rt_items = json.loads(adapter_out or "{}").get("items", [])
        check("round trip: the adapter emits exactly one item for the one invalidated answer",
              len(rt_items) == 1, adapter_out)
        rt_item = rt_items[0] if rt_items else {}
        check("round trip: the item id is the ledger's item_id",
              rt_item.get("id") == "renewal-terms", str(rt_item))
        check("round trip: the item keeps the original kind",
              rt_item.get("kind") == "APPROVE", str(rt_item))
        check("round trip: the question is framed as a re-decision",
              str(rt_item.get("question", "")).startswith("Re-decide:"), str(rt_item))
        check("round trip: signal is stale", rt_item.get("signal") == "stale", str(rt_item))
        check("round trip: the adapter invents no options",
              rt_item.get("options") == [], str(rt_item))
        check("round trip: deadline is null, not a soft date",
              "deadline" in rt_item and rt_item.get("deadline") is None, str(rt_item))
        check("round trip: reversible and blocks are omitted, not guessed",
              rt_item.get("id") == "renewal-terms"
              and "reversible" not in rt_item and "blocks" not in rt_item, str(rt_item))
        expected_evidence = f"{rt_ledger}:2 invalidated 2026-09-24: the counterparty sent new terms"
        check("round trip: evidence cites the ledger, the line, the date and the reason",
              rt_item.get("evidence") == expected_evidence, str(rt_item.get("evidence")))

        rt_board = items_file("roundtrip-board.json", rt_items)
        rc, out = run(rt_board)
        check("round trip: the stale item is first on the board",
              rc == 0 and "1. [APPROVE] Re-decide:" in out, out)
        rc, out = run(rt_board, "--why", "renewal-terms")
        check("round trip: --why shows the +20 for the invalidated standing answer",
              rc == 0 and "+20" in out and "invalidated standing answer" in out, out)

        # `hsi timeline LEDGER -o OUT.html`: the ledger drawn as a page. Written before the
        # code, against the failure list in the pull request. The assertions read the page,
        # because the page is what a person reads.
        def ledger_file(name, lines):
            p = os.path.join(tmp, name)
            with open(p, "wb") as f:
                for line in lines:
                    f.write(line if isinstance(line, bytes) else line.encode("utf-8"))
                    f.write(b"\n")
            return p

        def timeline(ledger, *extra):
            out_path = os.path.join(tmp, os.path.basename(ledger) + ".html")
            if os.path.exists(out_path):
                os.remove(out_path)
            rc, out = run("timeline", ledger, "-o", out_path, *extra)
            page = open(out_path, encoding="utf-8").read() if os.path.exists(out_path) else ""
            return rc, out, page

        def row(item_id, **kw):
            return json.dumps(answer(item_id, **kw))

        allowed_tags = {"html", "head", "meta", "title", "style", "body", "main", "header",
                        "footer", "section", "figure", "figcaption", "h1", "h2", "p", "ol",
                        "ul", "li", "div", "span", "strong", "code", "a", "table", "caption",
                        "thead", "tbody", "tr", "th", "td", "svg", "g", "rect", "line", "path",
                        "circle", "polygon", "text"}

        class Tags(HTMLParser):
            """The tags a browser would build, read by a parser rather than a regex: escaped
            text inside an attribute is not a tag, and a regex cannot tell the difference."""
            def __init__(self):
                super().__init__(convert_charrefs=True)
                self.found = []

            def handle_starttag(self, tag, attrs):
                self.found.append((tag, attrs))

            handle_startendtag = handle_starttag

        def tags(page):
            parser = Tags()
            parser.feed(page)
            parser.close()
            return parser.found

        missing = os.path.join(tmp, "no-such-ledger.jsonl")
        rc, out = run("timeline", missing, "-o", missing + ".html")
        check("timeline: a missing ledger is refused, not drawn as an empty run",
              rc == 2 and "not found" in out.lower() and not os.path.exists(missing + ".html"), out)

        rc, out = run("timeline", tmp, "-o", os.path.join(tmp, "dir.html"))
        check("timeline: a directory is refused without a traceback",
              rc == 2 and "cannot read" in out and "Traceback" not in out, out)

        rc, out, page = timeline(ledger_file("tl-empty.jsonl", []))
        check("timeline: an empty ledger renders a page that says it is empty",
              rc == 0 and "The ledger is empty" in page and 'class="mark' not in page, out + page[:300])

        rc, out, page = timeline(ledger_file("tl-single.jsonl", [row("only-one", at="2026-09-20T14:00:00Z")]))
        check("timeline: a single event renders, with one tick and no zero-span crash",
              rc == 0 and "The human was needed 1 time" in page
              and "Keep doing the thing for only-one?" in page and page.count('class="tick"') == 1,
              out + page[:300])

        rc, out, page = timeline(ledger_file("tl-malformed.jsonl", [
            row("first-item"),
            "{not json at all",
            "[1, 2]",
            "",
            row("unknown-kind", kind="MAYBE"),
            b"\xff\xfe not utf-8 \xc3",
            "[" * 100000,
            row("last-item", kind="APPROVE"),
        ]))
        check("timeline: malformed lines are skipped and counted, never fatal",
              rc == 0 and "8 lines read: 3 events, 5 skipped" in page, out + page[:500])
        check("timeline: the skipped line numbers are listed",
              "Skipped lines: 2, 3, 4, 6, 7" in page, page[-1500:])
        check("timeline: an unknown kind is shown as other and does not count as the human",
              "The human was needed 2 times" in page and ">other<" in page and "MAYBE" in page, page[:1500])
        check("timeline: the page says the strict reader would refuse that ledger",
              "hsi record would refuse this ledger" in page, page[:1500])
        # A separate ledger for "where": read_ledger decodes in buffered chunks, so a bad byte
        # anywhere in the first chunk fails before line 2 is parsed, and names no line.
        rc, out, page = timeline(ledger_file("tl-strict.jsonl", [row("first-item"), "{not json at all"]))
        check("timeline: and where it would stop, when the strict reader can say",
              rc == 0 and "hsi record would refuse this ledger: ledger line 2" in page, page[:1500])

        rc, out, page = timeline(ledger_file("tl-bom-crlf.jsonl", [
            b"\xef\xbb\xbf" + row("bom-first").encode() + b"\r",
            row("crlf-second").encode() + b"\r",
        ]))
        check("timeline: a byte-order mark and CRLF endings parse",
              rc == 0 and "2 lines read: 2 events, 0 skipped" in page, out + page[:500])

        payload = "<script>alert(1)</script>"
        rc, out, page = timeline(ledger_file("tl-inject.jsonl", [
            row("a\"b'c<i>", question=payload, answer="</style><svg onload=alert(3)>",
                actor="\"><img src=x onerror=alert(2)>", evidence="  JavaScript:alert(4)"),
            json.dumps({"item_id": "x", "kind": "<b>X</b>", "question": "<iframe src=//evil>"}),
            row("linked", evidence="https://example.com/pr/12", question='x" onmouseover="alert(5)'),
        ]))
        found = tags(page)
        names = {name for name, _ in found}
        attrs = [(name, key, value or "") for name, pairs in found for key, value in pairs]
        check("timeline: every tag in the page is one the renderer writes",
              rc == 0 and bool(found) and names <= allowed_tags, str(sorted(names - allowed_tags)))
        check("timeline: no tag carries an event handler or a src",
              rc == 0 and not [a for a in attrs if a[1].startswith("on") or a[1] == "src"], str(attrs[:5]))
        check("timeline: every link is an anchor on the page or an http(s) address",
              bool(found) and all(re.match(r"#|https?://", v) for _, k, v in attrs if k == "href"),
              str([v for _, k, v in attrs if k == "href"][:5]))
        check("timeline: the escaped payload is present, so escaping did not just drop it",
              "&lt;script&gt;alert(1)&lt;/script&gt;" in page and "&lt;img src=x" in page
              and "&lt;b&gt;X&lt;/b&gt;" in page, page[:500])
        check("timeline: a javascript: evidence value is text, never a link",
              "JavaScript:alert(4)" in page
              and not [v for _, k, v in attrs if k == "href" and "javascript" in v.lower()], out)
        check("timeline: an https evidence value is a link",
              'href="https://example.com/pr/12"' in page, out)
        check("timeline: the page makes no request of its own",
              page.startswith("<!doctype html>") and "<script" not in page.lower() and "<link" not in page.lower()
              and "@import" not in page and "url(" not in page
              and not [a for a in attrs if a[1] in ("src", "srcset", "data", "poster")], out)

        tl_ledger = ledger_file("tl-waits.jsonl", [
            row("long-wait", kind="TASTE", actor="builder",
                asked_at="2026-09-20T10:00:00Z", at="2026-09-20T11:30:00Z"),
            row("short-wait", kind="APPROVE", actor="reviewer",
                asked_at="2026-09-20T12:00:00Z", at="2026-09-20T12:20:00Z"),
        ])
        rc, out, page = timeline(tl_ledger)
        check("timeline: recorded waits are totaled and the longest is named",
              rc == 0 and "Waits recorded for 2 of 2: 1h 50m in total, longest 1h 30m" in page,
              out + page[:1500])
        check("timeline: one lane per actor", "builder" in page and "reviewer" in page, page[:1500])
        first = page
        rc, out, page = timeline(tl_ledger)
        check("timeline: the same ledger renders byte-identical pages",
              rc == 0 and first != "" and first == page, out)

        rc, out, page = timeline(ledger_file("tl-zones.jsonl", [
            row("offset-wait", asked_at="2026-09-20T10:00:00-04:00", at="2026-09-20T14:30:00Z"),
            row("naive-wait", asked_at="2026-09-20T14:00:00", at="2026-09-20T14:45:00+00:00"),
        ]))
        check("timeline: offsets convert to UTC and a naive time is read as UTC, without a crash",
              rc == 0 and "Waits recorded for 2 of 2: 1h 15m in total, longest 45m" in page
              and "read as UTC" in page, out + page[:1500])

        rc, out, page = timeline(ledger_file("tl-negative.jsonl", [
            row("backwards", asked_at="2026-09-20T12:00:00Z", at="2026-09-20T11:00:00Z"),
        ]))
        check("timeline: an answer before its question is flagged and left out of the totals",
              rc == 0 and "answered before it was asked" in page and "Waits recorded for 0 of 1" in page,
              out + page[:1500])

        rc, out, page = timeline(ledger_file("tl-untimed.jsonl", [
            row("dated"),
            json.dumps(omit(answer("undated"), "date")),
        ]))
        check("timeline: an event with no time is listed apart, never placed by guess",
              rc == 0 and "1 event has no time recorded" in page and "not recorded" in page,
              out + page[:1500])

        rc, out, page = timeline(ledger_file("tl-dayonly.jsonl", [
            row("clocked", at="2026-09-20T14:00:00Z"),
            json.dumps({"item_id": "clocked", "invalidated": {"date": "2026-09-20", "evidence": "it changed"}}),
        ]))
        check("timeline: a day-only event beside clock times is listed apart, marked day only",
              rc == 0 and "1 event is recorded to the day only" in page and "(day only)" in page,
              out + page[:1500])

        rc, out, page = timeline(EXAMPLE_LEDGER)
        check("timeline: today's ledger shape renders, and claims no wait it cannot see",
              rc == 0 and "The human was needed 1 time" in page and "Waits recorded for 0 of 1" in page
              and "longest" not in page, out + page[:1500])

        same = ledger_file("tl-self.jsonl", [row("keep-me")])
        before = open(same, "rb").read()
        rc, out = run("timeline", same, "-o", os.path.join(tmp, ".", "tl-self.jsonl"))
        check("timeline: writing the page over the ledger itself is refused",
              rc == 2 and "ledger itself" in out and open(same, "rb").read() == before, out)

        rc, out = run("timeline", same, "--bogus")
        check("timeline: an unknown flag is refused", rc == 2 and "hsi timeline" in out
              and "--bogus" in out, out)

        r = subprocess.run([sys.executable, HSI, "timeline", same], capture_output=True, text=True)
        check("timeline: with no -o the page goes to stdout and the summary to stderr",
              r.returncode == 0 and r.stdout.startswith("<!doctype html>")
              and "hsi timeline:" in r.stderr and "hsi timeline:" not in r.stdout, r.stderr)

        big_lines = []
        for n in range(20000):
            minute = n
            big_lines.append(row(f"item-{n}", kind=("DECIDE", "APPROVE", "EXECUTE", "TASTE", "NOTE")[n % 5],
                                 actor=f"agent-{n % 30}",
                                 asked_at=f"2026-09-{1 + minute // 1440:02d}T{minute % 1440 // 60:02d}:{minute % 60:02d}:00Z",
                                 at=f"2026-09-{1 + (minute + 2) // 1440:02d}T{(minute + 2) % 1440 // 60:02d}:{(minute + 2) % 60:02d}:00Z"))
        big = ledger_file("tl-big.jsonl", big_lines)
        started = time.monotonic()
        rc, out, page = timeline(big)
        elapsed = time.monotonic() - started
        check("timeline: a 20,000-event run renders in under a minute",
              rc == 0 and elapsed < 60 and "20,000 lines read: 20,000 events, 0 skipped" in page,
              f"{elapsed:.1f}s " + out)
        marks = page.count('class="mark')
        check("timeline: and the page stays bounded: under 3 MB, marks grouped, lanes merged",
              len(page.encode()) < 3_000_000 and marks < 5000 and "other actors" in page,
              f"{len(page.encode())} bytes, {marks} marks")
        check("timeline: the event table says how much of the run it shows",
              "The table shows the first 2,000 of 20,000 events" in page, page[-2000:])

        rc, out = run("record", "--ledger", TIMELINE_LEDGER, "--lookup", "staging-login")
        check("timeline: the example ledger, optional fields and all, still reads with hsi record",
              rc == 0 and "invalidated: no" in out, out)
        rc, out, page = timeline(TIMELINE_LEDGER)
        check("timeline: the example ledger passes the strict reader, and the page says so",
              rc == 0 and "hsi record reads this ledger without error" in page, out)
        committed = open(TIMELINE_PAGE, encoding="utf-8").read() if os.path.exists(TIMELINE_PAGE) else ""
        check("timeline: the committed example page matches a fresh render of the example ledger",
              page != "" and page == committed,
              "re-render: hsi timeline examples/timeline.example.jsonl -o examples/timeline.example.html")

        # From an independent review of the timeline, each written and watched failing
        # before the fix it names.

        # A lone UTF-16 surrogate is valid JSON and not valid Unicode. JavaScript writes one
        # whenever a string is clipped in the middle of an emoji: "ok 😀".slice(0, 4).
        half = "\ud83d"
        surrogate_ledger = ledger_file("tl-surrogate.jsonl", [
            row(f"item{half}", question=f"q{half}", answer=f"a{half}", actor=f"actor{half}",
                evidence=f"ref{half}", supersedes_reason=f"why{half}", asked_at=f"asked{half}",
                at="2026-09-20T10:00:00Z"),
            row("kind-item", kind=f"K{half}", at=f"at{half}"),
            row("link-item", evidence=f"https://example.com/{half}"),
            row("nested-item", evidence={f"key{half}": [f"value{half}"]}),
            json.dumps({"item_id": f"item{half}",
                        "invalidated": {"date": "2026-09-21", "evidence": f"fired{half}", "at": f"inv{half}"}}),
        ])
        rc, out, page = timeline(surrogate_ledger)
        shown = [f"{text}�" for text in ("item", "q", "a", "actor", "ref", "why", "asked", "K", "at",
                                              "example.com/", "key", "value", "fired", "inv")]
        check("timeline: a lone surrogate in any text field renders as U+FFFD, not a crash",
              rc == 0 and "Traceback" not in out and "5 lines read: 5 events, 0 skipped" in page
              and all(text in page for text in shown),
              out + str([text for text in shown if text not in page]))

        # The file name is text on the page too, and a name that is not UTF-8 reaches Python
        # as a surrogate.
        try:
            odd_name = os.path.join(os.fsencode(tmp), b"tl-latin1-\xe9.jsonl")
            with open(odd_name, "wb") as f:
                f.write(row("plain").encode() + b"\n")
        except (OSError, ValueError):
            odd_name = None
        if odd_name:
            r = subprocess.run([sys.executable, HSI, "timeline", odd_name], capture_output=True)
            check("timeline: a ledger file name that is not UTF-8 renders, not a crash",
                  r.returncode == 0 and b"tl-latin1-\xef\xbf\xbd.jsonl" in r.stdout and b"Traceback" not in r.stderr,
                  r.stderr.decode("utf-8", "replace"))
        else:
            print("SKIP  timeline: a ledger file name that is not UTF-8 (this file system refuses one)")

        kept = os.path.join(tmp, "tl-kept.html")
        previous = b"the previous page\n" * 64
        with open(kept, "wb") as f:
            f.write(previous)
        rc, out = run("timeline", surrogate_ledger, "-o", kept)
        after = open(kept, "rb").read()
        check("timeline: an existing -o file is replaced by the new page, never left truncated",
              rc == 0 and after.startswith(b"<!doctype html>") and after.endswith(b"</html>\n"),
              f"{len(after)} bytes; " + out)

        r = subprocess.run([sys.executable, HSI, "timeline", surrogate_ledger], capture_output=True)
        check("timeline: and to stdout, the same ledger gives a whole page and exit 0",
              r.returncode == 0 and r.stdout.startswith(b"<!doctype html>")
              and r.stdout.endswith(b"</html>\n") and b"Traceback" not in r.stderr,
              r.stderr.decode("utf-8", "replace"))

        try:
            import resource
        except ImportError:
            resource = None
        if resource is not None and hasattr(resource, "RLIMIT_FSIZE"):
            # A write that fails partway, the way a full disk fails it: past 4 KB the
            # process may not grow a file. The old page must survive whole.
            full = os.path.join(tmp, "tl-full")
            os.makedirs(full)
            kept = os.path.join(full, "kept.html")
            with open(kept, "wb") as f:
                f.write(previous)

            def small_files():
                resource.setrlimit(resource.RLIMIT_FSIZE, (4096, 4096))

            r = subprocess.run([sys.executable, HSI, "timeline", TIMELINE_LEDGER, "-o", kept],
                               capture_output=True, text=True, preexec_fn=small_files)
            check("timeline: a write that fails partway leaves the previous page whole, and no temp file",
                  r.returncode == 2 and "cannot write" in r.stderr and open(kept, "rb").read() == previous
                  and os.listdir(full) == ["kept.html"],
                  f"rc {r.returncode}, {os.path.getsize(kept)} bytes, {os.listdir(full)}; {r.stderr}")
        else:
            print("SKIP  timeline: a write that fails partway (no RLIMIT_FSIZE on this platform)")

        # From a second review: a temp file and a rename suit a regular file this user owns
        # and may replace, and nothing else. Every other -o is written where it is, as the
        # first version wrote it, and a file nobody may write is still refused.
        want = subprocess.run([sys.executable, HSI, "timeline", TIMELINE_LEDGER], capture_output=True).stdout

        def write_to(target, **kw):
            return subprocess.run([sys.executable, HSI, "timeline", TIMELINE_LEDGER, "-o", target],
                                  capture_output=True, **kw)

        def binds(path):
            """Whether a chmod that removed write access holds for this user; it does not for root."""
            return not os.access(path, os.W_OK)

        if os.path.exists("/dev/null"):
            r = write_to("/dev/null")
            check("timeline: -o /dev/null exits 0",
                  r.returncode == 0 and b"Traceback" not in r.stderr, r.stderr.decode("utf-8", "replace"))
            r = write_to("/dev/stdout")
            check("timeline: -o /dev/stdout into a pipe exits 0, and the whole page comes through it",
                  r.returncode == 0 and want.startswith(b"<!doctype html>") and r.stdout == want,
                  f"rc {r.returncode}, {len(r.stdout)} of {len(want)} bytes; " + r.stderr.decode("utf-8", "replace"))
        else:
            print("SKIP  timeline: -o /dev/null and /dev/stdout (no /dev on this platform)")

        if hasattr(os, "mkfifo"):
            fifo = os.path.join(tmp, "tl-fifo")
            os.mkfifo(fifo)
            got = []

            def drain():
                with open(fifo, "rb") as f:
                    got.append(f.read())

            reader = threading.Thread(target=drain, daemon=True)
            reader.start()
            r = write_to(fifo, timeout=120)
            reader.join(10)
            check("timeline: -o a FIFO, the shape process substitution gives, streams the page and leaves the FIFO",
                  r.returncode == 0 and got == [want] and stat.S_ISFIFO(os.stat(fifo).st_mode),
                  f"rc {r.returncode}, reader got {[len(g) for g in got]} of {len(want)} bytes, "
                  f"FIFO kept: {stat.S_ISFIFO(os.stat(fifo).st_mode)}; " + r.stderr.decode("utf-8", "replace"))
        else:
            print("SKIP  timeline: -o a FIFO (no mkfifo on this platform)")

        ro_dir = os.path.join(tmp, "tl-readonly")
        os.makedirs(ro_dir)
        ro = os.path.join(ro_dir, "page.html")
        with open(ro, "wb") as f:
            f.write(previous)
        os.chmod(ro, 0o444)
        if binds(ro):
            r = write_to(ro)
            check("timeline: a read-only -o file is refused with exit 2 and left byte for byte",
                  r.returncode == 2 and b"cannot write" in r.stderr and open(ro, "rb").read() == previous
                  and stat.S_IMODE(os.stat(ro).st_mode) == 0o444 and os.listdir(ro_dir) == ["page.html"],
                  f"rc {r.returncode}, {os.path.getsize(ro)} bytes, {os.listdir(ro_dir)}; "
                  + r.stderr.decode("utf-8", "replace"))
        else:
            print("SKIP  timeline: a read-only -o file is refused (permission bits do not bind for this user)")

        hl_dir = os.path.join(tmp, "tl-hardlink")
        os.makedirs(hl_dir)
        first_name, second_name = os.path.join(hl_dir, "a.html"), os.path.join(hl_dir, "b.html")
        with open(first_name, "wb") as f:
            f.write(previous)
        try:
            os.link(first_name, second_name)
        except (OSError, AttributeError):
            second_name = None
        if second_name:
            r = write_to(first_name)
            check("timeline: a hard-linked -o file gets the new page under both names",
                  r.returncode == 0 and open(first_name, "rb").read() == want
                  and open(second_name, "rb").read() == want
                  and os.stat(first_name).st_ino == os.stat(second_name).st_ino
                  and sorted(os.listdir(hl_dir)) == ["a.html", "b.html"],
                  f"rc {r.returncode}, a {os.path.getsize(first_name)} bytes, b {os.path.getsize(second_name)} bytes; "
                  + r.stderr.decode("utf-8", "replace"))
        else:
            print("SKIP  timeline: a hard-linked -o file (this file system refuses a hard link)")

        locked = os.path.join(tmp, "tl-locked")
        os.makedirs(locked)
        in_locked = os.path.join(locked, "page.html")
        with open(in_locked, "wb") as f:
            f.write(previous)
        os.chmod(locked, 0o555)
        try:
            if binds(locked):
                r = write_to(in_locked)
                check("timeline: a writable -o file in a directory this user cannot write is updated in place",
                      r.returncode == 0 and open(in_locked, "rb").read() == want and os.listdir(locked) == ["page.html"],
                      f"rc {r.returncode}, {os.path.getsize(in_locked)} bytes, {os.listdir(locked)}; "
                      + r.stderr.decode("utf-8", "replace"))
            else:
                print("SKIP  timeline: a file in an unwritable directory (permission bits do not bind for this user)")
        finally:
            os.chmod(locked, 0o755)

        long_dir = os.path.join(tmp, "tl-longname")
        os.makedirs(long_dir)
        long_name = os.path.join(long_dir, "p" * 245 + ".html")  # 250 bytes; most file systems allow 255
        try:
            with open(long_name, "wb") as f:
                f.write(previous)
        except OSError:
            long_name = None
        if long_name:
            r = write_to(long_name)
            check("timeline: an -o name of 250 bytes is written, because the temp name no longer grows from it",
                  r.returncode == 0 and open(long_name, "rb").read() == want
                  and os.listdir(long_dir) == [os.path.basename(long_name)],
                  f"rc {r.returncode}, {len(os.listdir(long_dir))} entries; " + r.stderr.decode("utf-8", "replace"))
        else:
            print("SKIP  timeline: a 250-byte -o name (this file system refuses one)")

        # The page must not scroll sideways at phone width. Measured by a browser, because
        # only a browser knows where a line of text breaks.
        browser = next((shutil.which(n) for n in ("google-chrome", "google-chrome-stable", "chromium",
                                                  "chromium-browser") if shutil.which(n)), None)

        def page_width(path, width):
            """The document's scrollWidth with the page laid out `width` px wide. The page
            sits in an iframe of exactly that width, because a window has a minimum size."""
            wrapper = os.path.join(tmp, f"measure-{width}.html")
            with open(wrapper, "w", encoding="utf-8") as f:
                f.write(f'<!doctype html><body style="margin:0"><iframe id="f" src="{Path(path).as_uri()}" '
                        f'style="border:0;width:{width}px;height:2000px"></iframe><pre id="m">none</pre>'
                        '<script>document.getElementById("f").addEventListener("load",function(){'
                        'document.getElementById("m").textContent="scrollWidth="+'
                        'this.contentDocument.documentElement.scrollWidth})</script>')
            try:
                r = subprocess.run([browser, "--headless=new", "--no-sandbox", "--disable-gpu",
                                    "--allow-file-access-from-files", "--virtual-time-budget=5000",
                                    f"--user-data-dir={os.path.join(tmp, 'chrome-profile')}",
                                    "--dump-dom", Path(wrapper).as_uri()],
                                   capture_output=True, text=True, timeout=120)
            except subprocess.TimeoutExpired:
                return None
            found = re.search(r"scrollWidth=(\d+)", r.stdout)
            return int(found.group(1)) if found else None

        if browser:
            token = "export_scope_for_the_quarterly_customer_report_v2_final"
            rc, out, page = timeline(ledger_file("tl-longtoken.jsonl", [
                row(token, actor="planner_agent_with_a_long_name", question="Q " + token * 3,
                    asked_at="2026-09-26T08:00:00Z", at="2026-09-26T10:00:00Z", evidence="ref:" + token * 2),
            ]))
            control = os.path.join(tmp, "tl-control.html")
            with open(control, "w", encoding="utf-8") as f:
                f.write('<!doctype html><meta name="viewport" content="width=device-width">'
                        '<p style="width:900px">wider than a phone</p>')
            seen, wide = page_width(control, 390), page_width(os.path.join(tmp, "tl-longtoken.jsonl.html"), 390)
            check("timeline: at 390 px a long unbroken item id or actor does not scroll the page sideways",
                  rc == 0 and seen is not None and seen > 390 and wide is not None and wide <= 390,
                  f"control page measured {seen} (must be over 390, or the measurement is blind); "
                  f"the timeline measured {wide}")
        elif os.environ.get("CI"):
            check("timeline: the 390 px layout check needs Chrome, and CI has none", False, "install Chrome")
        else:
            print("SKIP  timeline: the 390 px layout check (no Chrome on this machine)")

        def card_tables(path, width):
            """Per `.table-wrap`: its scrollWidth, its clientWidth, and the computed overflow-wrap
            of its Actor cell, with the page laid out `width` px wide. None when nothing ran."""
            wrapper = os.path.join(tmp, f"cards-{width}.html")
            with open(wrapper, "w", encoding="utf-8") as f:
                f.write(f'<!doctype html><body style="margin:0"><iframe id="f" src="{Path(path).as_uri()}" '
                        f'style="border:0;width:{width}px;height:2000px"></iframe><pre id="m">none</pre>'
                        '<script>document.getElementById("f").addEventListener("load",function(){'
                        'var d=this.contentDocument,out=[];'
                        'd.querySelectorAll(".table-wrap").forEach(function(w){'
                        'var c=w.querySelector("td[data-label=Actor]")||w.querySelector("td");'
                        'out.push(w.scrollWidth+","+w.clientWidth+","+(c?getComputedStyle(c).overflowWrap:"none"))});'
                        'document.getElementById("m").textContent="cards="+out.join(";")+"."})</script>')
            try:
                r = subprocess.run([browser, "--headless=new", "--no-sandbox", "--disable-gpu",
                                    "--allow-file-access-from-files", "--virtual-time-budget=5000",
                                    f"--user-data-dir={os.path.join(tmp, 'chrome-profile')}",
                                    "--dump-dom", Path(wrapper).as_uri()],
                                   capture_output=True, text=True, timeout=120)
            except subprocess.TimeoutExpired:
                return None
            found = re.search(r'<pre id="m">cards=([^<]*)\.</pre>', r.stdout)
            if not found:
                return None
            return [(int(a), int(b), c) for a, b, c in (part.split(",") for part in found.group(1).split(";") if part)]

        if browser:
            # The page no longer scrolls at 390 px, but a card table could still scroll
            # sideways inside its own box: a long actor has no break in it.
            control = os.path.join(tmp, "tl-cards-control.html")
            with open(control, "w", encoding="utf-8") as f:
                f.write('<!doctype html><meta name="viewport" content="width=device-width">'
                        '<div class="table-wrap" style="overflow-x:auto;width:200px"><table class="cards">'
                        f'<tr><td>{"x" * 120}</td></tr></table></div>')
            blind = card_tables(control, 390)
            for length in (55, 121):
                actor = ("an_actor_name_with_no_break_" * 5)[:length]
                name = f"tl-cards-{length}.jsonl"
                rc, out, page = timeline(ledger_file(name, [
                    row("first", actor=actor, asked_at="2026-09-26T08:00:00Z", at="2026-09-26T10:00:00Z"),
                    row("second", kind="APPROVE", actor="short", at="2026-09-26T11:00:00Z"),
                ]))
                cards = card_tables(os.path.join(tmp, name + ".html"), 390)
                check(f"timeline: at 390 px no card table scrolls sideways inside its box, with a {length}-character actor",
                      rc == 0 and blind is not None and len(blind) == 1 and blind[0][0] > blind[0][1]
                      and cards is not None and len(cards) == page.count('class="table-wrap"') == 2
                      and all(scroll <= client for scroll, client, _ in cards),
                      f"control {blind} (must overflow, or the measurement is blind); tables {cards} "
                      "as (scrollWidth, clientWidth, overflow-wrap)")
            wide = card_tables(os.path.join(tmp, "tl-cards-55.jsonl.html"), 1280)
            check("timeline: at 1280 px the tables' cells keep their desktop wrapping, so the phone rule stays in its query",
                  wide is not None and len(wide) == 2 and all(wrap == "break-word" for _, _, wrap in wide),
                  f"tables {wide} as (scrollWidth, clientWidth, overflow-wrap)")
        elif os.environ.get("CI"):
            check("timeline: the 390 px card table check needs Chrome, and CI has none", False, "install Chrome")
        else:
            print("SKIP  timeline: the 390 px card table check (no Chrome on this machine)")

        rc, out, page = timeline(ledger_file("tl-unknown-kinds.jsonl", [
            row("lowercase", kind="decide"), row("maybe", kind="MAYBE"), row("null", kind=None),
        ]))
        check("timeline: when no event has a recognized kind, the headline says so, not that the human was not needed",
              rc == 0 and "The human was not needed" not in page
              and "No event had a recognized kind (3 shown as other)" in page, page[:1500])
        rc, out, page = timeline(ledger_file("tl-invalidations-only.jsonl", [
            json.dumps({"item_id": "gone", "invalidated": {"date": "2026-09-21", "evidence": "it changed"}}),
        ]))
        check("timeline: a ledger of invalidations alone still says the human was not needed",
              rc == 0 and "The human was not needed in any event this ledger recorded" in page, page[:1500])
        # From a second review: the headline must not call an invalidation unrecognized, and
        # must not leave the unknown kinds out when some kinds are known.
        rc, out, page = timeline(ledger_file("tl-unknown-and-invalidated.jsonl", [
            row("maybe", kind="MAYBE"),
            json.dumps({"item_id": "gone", "invalidated": {"date": "2026-09-21", "evidence": "it changed"}}),
        ]))
        check("timeline: beside unknown kinds, the headline does not call an invalidation unrecognized",
              rc == 0 and "No event had a recognized kind" not in page
              and "No answer had a recognized kind (1 shown as other); 1 invalidation was recognized." in page,
              page[:1500])
        rc, out, page = timeline(ledger_file("tl-some-unknown.jsonl", [
            row("known-one"), row("known-two", kind="APPROVE"), row("unknown-one", kind="MAYBE"),
            row("unknown-two", kind=None),
        ]))
        check("timeline: when some kinds are known and some are not, the headline gives the unknown count",
              rc == 0 and "The human was needed 2 times: 1 DECIDE, 1 APPROVE. "
              "2 more events had no recognized kind, shown as other." in page, page[:1500])
        rc, out, page = timeline(ledger_file("tl-invisible-kind.jsonl", [
            row("bidi", kind="DE\u202eCIDE"), row("zero-width", kind="APP\u200bROVE"),
        ]))
        check("timeline: an unrecognized kind that only looks like a known one shows its invisible character",
              rc == 0 and "(DE\\u202eCIDE)" in page and "(APP\\u200bROVE)" in page
              and "(DECIDE)" not in page and "\u200b" not in page, page[-3000:])

        rc, out, page = timeline(ledger_file("tl-bidi.jsonl", [
            row("deploy\u202e", actor="builder\u2067", question="\u202dswap\u202c this\u2066",
                asked_at="2026-09-20T10:00:00Z", at="2026-09-20T11:00:00Z", evidence="\u202egnp.exe"),
        ]))
        controls = sorted({f"U+{ord(c):04X}" for c in re.findall("[\u202a-\u202e\u2066-\u2069]", page)})
        check("timeline: bidi controls from the ledger are removed, so the page's own words never reverse",
              rc == 0 and not controls and "(DECIDE, deploy, asked by builder)." in page and "gnp.exe" in page,
              str(controls) + " " + page[:1200])

        long_actor, long_item = "B" * 100_000, "I" * 100_000
        # Invalidations take their item's lane, so 48 short lines once carried 48 copies of
        # the actor into the chart's tooltips.
        amplify = ledger_file("tl-amplify.jsonl", [
            row("x", actor=long_actor, at="2026-09-20T07:00:00Z"),
            row(long_item, actor=long_actor, question="Ship it?",  # the default question holds the item id
                asked_at="2026-09-20T08:00:00Z", at="2026-09-20T10:00:00Z"),
        ] + [json.dumps({"item_id": "x", "invalidated": {"at": f"2026-09-20T{11 + n // 12:02d}:{n % 12 * 5:02d}:00Z"}})
             for n in range(48)])
        rc, out, page = timeline(amplify)
        longest = max((len(m) for m in re.findall(r"B+|I+", page)), default=0)
        check("timeline: a long actor or item id is clipped everywhere, so the page stays smaller than the ledger",
              rc == 0 and longest <= 200 and len(page.encode()) < os.path.getsize(amplify),
              f"longest run {longest:,}, page {len(page.encode()):,} bytes, ledger {os.path.getsize(amplify):,}")

        barecr = os.path.join(tmp, "tl-barecr.jsonl")
        with open(barecr, "wb") as f:
            f.write(row("first-record").encode() + b"\r" + row("second-record").encode() + b"\n")
        rc, out, page = timeline(barecr)
        check("timeline: records split by a bare CR are read the way hsi record reads them",
              rc == 0 and "2 lines read: 2 events, 0 skipped" in page
              and "hsi record reads this ledger without error" in page, page[:1500])

        rc, out, page = timeline(ledger_file("tl-year-one.jsonl", [
            row("ancient", date="0001-01-01", at="0001-01-01T00:00:00Z"),
            row("modern", at="2026-09-20T10:00:00Z"),
        ]))
        check("timeline: a year below 1000 prints with four digits",
              rc == 0 and "0001-01-01 00:00 UTC" in page and not re.search(r"(?<![\d-])1-01-01", page),
              page[:1500])

    print(f"\n{failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
