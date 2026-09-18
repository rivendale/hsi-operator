#!/usr/bin/env python3
"""Example adapter — turn a JSONL task file into the hsi items contract.

THE SKILL KNOWS NOTHING ABOUT YOUR SYSTEMS, and that is the point. `bin/hsi` consumes a
plain JSON contract; an adapter is the only thing that knows where your work lives. This
one reads a line-delimited JSON file, which is the smallest useful shape. Copy it and
change the reader for a tracker, an issue API, a database, or a spreadsheet.

  python3 collect.py TASKS.jsonl --operator alice > items.json
  hsi items.json

INPUT: one JSON object per line. Only `what` is required.
  {"id":"...", "what":"the thing", "who":["alice"], "status":"open",
   "firmness":"hard", "due":"2026-10-14", "note":"free text"}

WHAT IT DROPS, because the SKILL says these must never reach a person:
  - anything whose status reads as closed
  - anything not addressed to the operator, when `who` is present
  - anything with no text
"""
import argparse, datetime, json, re, sys

CLOSED = {"done", "closed", "complete", "completed", "decided", "dropped", "cancelled",
          "confirmed", "superseded", "resolved", "wontfix", "abandoned"}

APPROVE = ("approve", "permission", "sign off", "authorise", "authorize", "may i", "ok to")
DECIDE  = ("decide", "decision", "choose", "whether to", "which ", " or ", "trade-off", "tradeoff")
TASTE   = ("look", "feel", "wording", "copy", "design", "layout", "ui", "ux", "tone", "naming")

def kind_of(text):
    t = text.lower()
    if any(w in t for w in APPROVE): return "APPROVE"
    if any(w in t for w in DECIDE):  return "DECIDE"
    if any(w in t for w in TASTE):   return "TASTE"
    return "EXECUTE"

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="JSONL file, one task per line")
    ap.add_argument("--operator", default=None,
                    help="only items addressed to this name; omit to take all")
    ap.add_argument("--today", default=None, help="YYYY-MM-DD, for reproducible output")
    a = ap.parse_args(argv)
    today = datetime.date.fromisoformat(a.today) if a.today else datetime.date.today()

    items, skipped = [], 0
    for line in open(a.path, encoding="utf-8"):
        line = line.strip()
        if not line: continue
        try: r = json.loads(line)
        except ValueError: skipped += 1; continue
        if str(r.get("status", "")).lower() in CLOSED: continue
        who = [str(w).lower() for w in (r.get("who") or [])]
        if a.operator and who and a.operator.lower() not in who: continue
        what = str(r.get("what") or "").strip()
        if not what: continue

        # A deadline is a HARD EXTERNAL date. A soft revisit is not a deadline, and
        # treating it as one is how everything becomes urgent and nothing is.
        due = None
        if str(r.get("firmness", "")).lower() in ("", "hard"):
            d = str(r.get("due") or r.get("end") or r.get("start") or "")[:10]
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
                try:
                    if datetime.date.fromisoformat(d) >= today: due = d
                except ValueError: pass

        note = str(r.get("note") or "")
        ign = ""
        for cue in ("if ignored", "forfeit", "expire", "penalt", "closes", "unrecover", "late"):
            m = re.search(rf"[^.\n]*{cue}[^.\n]*", note, re.I)
            if m: ign = m.group(0).strip()[:160]; break

        items.append({
            "id": r.get("id") or what[:40],
            "kind": kind_of(what + " " + note),
            "question": what if what.endswith("?") else f"{what} — what do you want to do?",
            # An adapter over structured data CANNOT know why this needs a human. Saying so
            # is better than inventing a reason; an agent or a person fills this in.
            "why_you": "On your list and not answerable from the record. Reason not inferable by the adapter.",
            "options": [],
            "if_ignored_30d": ign,
            "blocks": [w for w in (r.get("who") or [])
                       if not a.operator or str(w).lower() != a.operator.lower()],
            "reversible": "no" if due else "partly",
            "cost": "a decision",
            "deadline": due,
            "evidence": f"{a.path} id={r.get('id')}" if r.get("id") else a.path,
        })

    json.dump({"items": items}, sys.stdout, indent=1, ensure_ascii=False)
    print(f"\nadapter: {len(items)} open item(s)"
          + (f", {skipped} unparseable line(s) skipped" if skipped else ""), file=sys.stderr)
    return 0

if __name__ == "__main__":
    sys.exit(main())
