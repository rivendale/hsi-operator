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

    print(f"\n{failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
