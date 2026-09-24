# Ledger adapter

Run `python3 adapters/ledger/collect.py .hsi/ledger.jsonl > items.json`, then give
`items.json` to `hsi`. The ledger path is explicit. The adapter emits one `stale` item
for each invalidated standing answer, with the ledger line and recorded evidence.

It drops answers that are still standing and older answers superseded by a newer row.
It leaves `options` empty and gives only a generic `why_you`. It cannot know the
operator's choices, the cost of delay, reversibility, who is blocked, or a real
deadline. An agent or person must frame those fields before relying on the board.

The adapter checked only the ledger's recorded events. The ledger records judgments;
it does not detect when an `invalidated_by` condition fires. A person or agent must
run `hsi record --invalidate` with evidence. This adapter does not watch calendars,
git, or any system outside the ledger, and it did not check whether the evidence is
true or whether the answer's original reasoning still holds.
