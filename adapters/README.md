# Adapters

An adapter turns a system you already have (a tracker, a task file, a calendar) into the
`items` contract that `bin/hsi` reads (`hsi --schema`). `jsonl-tasks/` is the worked example.
The standard below is what any adapter must meet. Written 2026-09-24 for
[#7](https://github.com/rivendale/hsi-operator/issues/7); `ledger/` is the real adapter.

## What an adapter must never write

- **A `why_you` beyond one generic line.** Why this needs a person is a judgment about
  preference, risk or taste; structured data does not contain it.
- **`options`.** Options are framing. An adapter that invents them makes the board look
  finished when it is not.
- **A `deadline` from a soft date.** A due date, a start date or a calendar entry is not a
  consequence. Emit a deadline only where something actually happens on that date.

## What an adapter must drop

- **Closed items,** including anything done, canceled or declined.
- **Facts.** An item that asks a person for something a search would find is a search
  somebody skipped.
- **Housekeeping:** labels, reminders and recurring chores that need no decision.

## Who frames

Framing (the `why_you`, the options, a recommendation) belongs to an agent or a person working
from what the adapter found. The adapter finds candidates; it does not decide what they mean.

## Each adapter's README

It must name what it did not check: fields it ignored, systems it could not reach, and any
date it treated as soft. A README that claims full coverage is the finding.

## The measured objection

Issue #7 records that dated items sort ahead of every undated one. A calendar adapter can
therefore fill a three-item board with dated entries and push every real decision off it. A
calendar adapter must pass a date only under the deadline rule above, and its README must say
what share of the board it took in a real run.
