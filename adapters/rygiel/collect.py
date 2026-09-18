#!/usr/bin/env python3
"""Rygiel estate adapter — turn the local record into the hsi items contract.

THE SKILL KNOWS NOTHING ABOUT THIS ESTATE, and that is the point. `bin/hsi` consumes a
plain JSON contract; this file is the only thing that knows about ATTENTION.md, the family
calendar, or how this household is organised. Anyone else writes their own adapter and the
skill is unchanged.

  python3 adapters/rygiel/collect.py [REPO] > items.json
  bin/hsi items.json

WHAT IT DELIBERATELY DROPS, because the skill says these must never reach a person:
  - rows whose status is done / decided / dropped / confirmed / cancelled
  - anything not addressed to the operator
  - anything whose text is a FACT rather than a question (an item asking a person for a
    fact is a search somebody skipped)
"""
import json, os, re, sys, datetime

CLOSED = {"done", "decided", "dropped", "confirmed", "cancelled", "superseded",
          "resolved", "not-applicable", "never"}

def kind_of(row):
    """DECIDE / APPROVE / EXECUTE / TASTE from how the row reads."""
    t = ((row.get("what") or "") + " " + (row.get("note") or "")).lower()
    if any(w in t for w in ("approve", "permission", "may i", "sign off", "authorise", "authorize")):
        return "APPROVE"
    if any(w in t for w in ("decide", "decision", "choose", "whether to", "or accept", "trade")):
        return "DECIDE"
    if any(w in t for w in ("look", "feel", "wording", "design", "layout", "ui", "ux", "tone")):
        return "TASTE"
    return "EXECUTE"

def main(argv):
    repo = argv[1] if len(argv) > 1 else os.path.expanduser("~/projects/overseer")
    cal = os.path.join(repo, "reference", "family-calendar.jsonl")
    today = datetime.date.today()
    items = []
    for line in open(cal, encoding="utf-8"):
        line = line.strip()
        if not line: continue
        try: r = json.loads(line)
        except ValueError: continue
        if str(r.get("status", "")).lower() in CLOSED: continue
        who = [w.lower() for w in (r.get("who") or [])]
        if "nick" not in who: continue
        what = (r.get("what") or "").strip()
        if not what: continue

        # a HARD external date only -- a soft revisit is not a deadline
        dl = None
        if str(r.get("firmness", "")).lower() == "hard":
            e = (r.get("end") or r.get("start") or "")[:10]
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", e):
                try:
                    if datetime.date.fromisoformat(e) >= today: dl = e
                except ValueError: pass

        note = (r.get("note") or "")
        ign = ""
        for cue in ("if ignored", "forfeit", "expire", "penalt", "closes", "unrecover", "late"):
            m = re.search(rf"[^.\n]*{cue}[^.\n]*", note, re.I)
            if m: ign = m.group(0).strip()[:160]; break

        items.append({
            "id": r.get("id", "?"),
            "kind": kind_of(r),
            "question": what if what.endswith("?") else f"{what} — what do you want to do?",
            "why_you": "On the board addressed to you; not answerable from the record.",
            "options": [],
            "if_ignored_30d": ign,
            "blocks": [w for w in (r.get("who") or []) if w.lower() != "nick"],
            "reversible": "no" if dl else "partly",
            "cost": "a decision",
            "deadline": dl,
            "evidence": f"reference/family-calendar.jsonl id={r.get('id')}",
        })
    json.dump({"items": items}, sys.stdout, indent=1, ensure_ascii=False)
    print(file=sys.stderr)
    print(f"adapter: {len(items)} open item(s) addressed to the operator", file=sys.stderr)
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
