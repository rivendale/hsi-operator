---
name: context-steward
description: Use when a long session approaches its context limit, or at any natural checkpoint in long-running work. Decides what must survive compaction, writes it somewhere durable BEFORE the window closes, and keeps working memory small by moving detail out rather than summarizing it away.
license: MIT
---

# context-steward

**A summary is a pointer, not a substitute.** Compaction that summarizes loses the file path,
the exact error, the number, the constraint — and loses them silently, at the moment they stop
being visible and before anyone notices they mattered.

Three separate projects arrived at the same fix independently in 2026: never rewrite the record,
only change what is *sent*; delete rather than summarize; keep notes and a searchable history
instead of a prose digest. **This skill is that principle, without depending on any of them.**

---

## 1. Know where you are, and do not trust the wrong gauge

**Check the actual context gauge, not a token budget, not a request count, not elapsed time.**
This skill exists because its author confidently reported "plenty of context left" from a *budget*
counter while the window sat at **94%** — an instrument that measures something else, read as if
it measured this. If the runtime shows a percentage, that is the number. If it does not, say you
cannot see it rather than estimating from feel.

**Act at 80%, not at 95%.** The write you need is the one you make while you still have room to
make it well.

## 2. When: at a boundary, with a bar that falls as the window fills

80% is the latest point, not the only one. The best moment is a **boundary**: one unit of work
has just finished, and the next has not loaded its detail yet. Compacting mid-unit throws away
exactly the live detail the next step needs.

Two questions decide whether you are at one:
- **Is the current unit finished** (merged, recorded, handed off) rather than paused mid-edit?
- **Is this hands-on work or coordination?** Hands-on work (a diff in progress, a failing test,
  an exact error) loses far more to compaction than coordination (status, routing, waiting on
  someone).

**The certainty you need should fall as the window fills.** Early, a wrong "compact now" is
expensive and nothing forces it, so require a clear boundary. Near full, the cost of *not*
compacting dominates, so any plausible boundary will do. One published adviser encodes this as a
threshold sliding from 0.90 when the window is under 10% full to 0.50 above 90%, reasoning that
"a wrong hint costs most when there is still room"
([compact-adviser](https://github.com/kunchenguid/compact-adviser), MIT). The shape matters more
than the numbers; calibrate your own.

**Run the cheap gates first:** enough context to be worth compacting at all, the session idle
rather than mid-tool-call, and a cooldown since the last suggestion so the advice does not nag.
Only then spend a judgment on it. If that judgment is a hosted model, the third caution in §5
applies in full, and **declare the bound**: how much leaves (a reply count and a byte cap) and
what never does (system prompt, images, keys).

## 3. What must survive, in priority order

1. **Decisions and who made them**, in the decider's own words, with the reasoning. A verdict
   without its reasoning cannot be applied to the next case.
2. **Measurements** — the number, the command that produced it, the date. Never the prose about
   the number.
3. **Corrections.** What was believed, what turned out to be true, and how it was caught. These
   are the highest-value and the first thing a summary drops.
4. **What is RUNNING** — background jobs, how to check them, how to restart them.
5. **What is blocked, and on whom.**
6. **What must not be re-litigated**, with the date it was settled.

**A secret's location survives; its value never does.** A long session can hold a live credential,
pasted into chat, printed by a command or read from a file, and it will score as important. Write
where it is and what it unlocks, never the string itself, in notes and in the handoff alike.

**What does NOT need to survive:** your reasoning chain, intermediate attempts that went nowhere,
tool output you already acted on, anything reconstructible from a file you can name.

## 4. Move it out, do not compress it in

The instinct is to summarize so it fits. That is the failure. **Write it to a file and keep the
path.** A path costs a line and returns everything; a summary costs a paragraph and returns a
lossy shadow of it.

Prefer, in order: **a private repo** (durable, diffable, survives the machine), **never a public
one**, where a handoff publishes names, locations and the status of other work · a local
scratch file the runtime can re-read · the context itself, last.

## 5. Classification decides what stays — and it is a GROUP-level use

If you have a classifier — a small local model, a typed-output API, even a set of heuristics —
score each block of working memory on *"would losing this change a future decision?"* and drop
what scores low. **Deleting beats summarizing**: the failure mode of deletion is a gap someone
notices, and the failure mode of summarizing is a confident sentence that is subtly wrong.

**Three cautions, each measured rather than assumed:**
- **Typed output does not guarantee correct judgments.** Vendors state this themselves.
  Calibration generally holds across groups of predictions, not on any single answer — so use a
  classifier to decide *what to spend more attention on*, never as the sole authority for
  discarding something irreplaceable.
- **Such models are usually not deterministic.** The same input can land either side of a
  threshold between runs. Widen the band by the observed jitter, and cache the decision against a
  hash of the input so a re-run cannot silently flip it.
- **Sending working memory to a third party is a data decision, not a performance one.** A long
  session's context contains whatever it has touched — names, credentials' locations, financial
  detail. If that payload cannot go to a vendor, the classifier must be local, and a local model
  is usually fast enough once you turn off anything that makes it think before answering.

## 6. Never let a reconstruction pass as the original

When work resumes from a compacted state, anything rebuilt from a summary is **[RECONSTRUCTED]**
and must say so. A rebuilt artifact compared against a real one produces a *smaller* difference
than the truth, because the reconstruction inherits the reconstructor's assumptions — which reads
as agreement and is not.

**If a decision depends on it, re-read or re-measure. Do not rebuild from prose.**

## 7. The handoff, written before you need it

One file, at the top of a **private** working tree (a local scratch path if the tree is public),
containing: what is running and how to restart it ·
the highest-leverage unstarted thing · who is blocked on what · what is open on the human · what
is live and unfixed · what must not be re-litigated · the lesson worth carrying.

**Write it at 80%.** A handoff written at 97% is written by someone who is already out of room to
think about it.
