#!/usr/bin/env python3
"""Turn invalidated standing ledger answers into HSI stale items."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "hsi-operator" / "bin"))
from ledger import LedgerError, read_ledger


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", help="append-only HSI ledger JSONL file")
    args = parser.parse_args()
    try:
        standing = read_ledger(args.ledger)
    except (LedgerError, OSError) as error:
        print(f"ledger adapter: {error}", file=sys.stderr)
        return 2
    items = []
    for item_id, entry in standing.items():
        event = entry["invalidated"]
        if not event:
            continue
        answer = entry["answer"]
        items.append({
            "id": item_id,
            "kind": answer["kind"],
            "question": "Re-decide: " + answer["question"],
            "signal": "stale",
            "evidence": (f"{args.ledger}:{entry['invalidation_line']} invalidated "
                         f"{event['date']}: {event['evidence']}"),
            "why_you": "A standing answer was invalidated; a person or agent must frame the decision.",
            "options": [],
            "deadline": None,
        })
    json.dump({"items": items}, sys.stdout, indent=2, ensure_ascii=False)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
