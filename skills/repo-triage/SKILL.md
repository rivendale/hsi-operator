---
name: repo-triage
description: Use when someone shares an open-source repo, library, model or tool and asks whether it is useful, whether to adopt or install it, or whether it is worth taking on as a dependency — evaluates it against MEASURED gaps rather than against its own pitch, and gives a verdict. Most verdicts should be no.
license: MIT
---

# repo-triage

**The failure mode this exists to prevent: adopting on enthusiasm rather than against a
measured gap.**

A shared link arrives with momentum behind it — stars, a launch post, a benchmark table.
The pitch describes what the thing *does*. The only question that matters is whether it
fixes something you have **measured**, and the honest answer is usually no.

**Most verdicts should be no.** A triage skill that finds everything useful is the same
defect as an assistant that approves everything. See `../hsi-operator/references/honesty-protocol.md`.

---

## The order matters. Cheapest kill first.

### 1. LICENCE — before anything else

The cheapest possible kill and the one most often skipped, because it takes ten seconds
and feels like paperwork.

- **No licence at all** is not permissive. It is all-rights-reserved. You may read it; you
  may not copy from it. Say that explicitly when recommending something as "a reference".
- **Non-commercial** (CC-BY-NC and friends) rules out anything touching a business.
- Check the **actual repo and the model card separately** — they disagree more often than
  you would expect, and a model card's claim is not a LICENSE file.

### 2. MATURITY — is there a thing here yet

`created`, `pushed`, stars **against** forks and commits, downloads for a model.

- A repo created **today** with two thousand stars is a launch, not a track record.
- **Two commits and five months untouched** is a satellite, not a project.
- Stars measure attention. Forks and downloads measure use. Prefer the second.
- **Staleness is fatal for some things and irrelevant for others.** A reference
  implementation can be three years old. Anything claiming to be more current than a
  training cutoff cannot be three months stale.

### 3. THE RUNTIME — does it run on the hardware you actually have

**The check most often skipped, and the one that kills most confidently.**

CUDA kernels on an AMD box. MLX on Linux. A GGUF that no installed runtime loads. A
browser-only WebGPU build proposed as a server lane. A benchmark measured on hardware
nobody here owns.

Ask what it needs, then check what is present. **Do not reason from the architecture
diagram.** A recommendation is also a claim about the world.

### 4. READ THE SOURCE, NOT THE README

The README says what the author wants it to do. Read the file that does the thing.

The gap is routinely load-bearing: a document library pitched for offline use whose
fallback path hands the document to a third-party API; a "memory" system whose annotations
are off by default; telemetry enabled unless disabled.

### 5. DOES IT FIX SOMETHING YOU MEASURED

Not something you might have. Name the measurement, with its number.

*"We have 4 unreadable documents out of 6,384"* is a measured gap, and it tells you a
better OCR model fixes almost nothing. *"Our OCR could be better"* is a feeling and it
will approve anything.

**If you cannot name the measurement, the honest verdict is "no gap identified", not
"looks useful".**

### 6. WHAT WOULD IT MAKE WORSE

The question nobody asks, and the one that produces the sharpest no.

- Does it dissolve a control you rely on? An abstraction that makes two providers
  interchangeable strings can erase a rule enforced by *which* provider you call.
- Does it add a processor to a data path? An intermediary makes a payload question
  strictly worse, never better.
- Does it default something on that you would not switch on deliberately?
- Does it create a second place for a fact that already lives somewhere?

---

## The verdict

State one. Not a list of considerations.

- **ADOPT** — name the measured gap it closes and what you will remove if it works.
- **STEAL A PATTERN** — the common useful outcome. Take the idea, credit it, write none of
  its code. Check the licence permits even this.
- **NO** — and say which step killed it. *"Non-commercial licence."* *"Needs CUDA, we are
  AMD."* *"Fixes nothing we measured."* A no with a reason is reusable; a no without one
  gets re-litigated when the link is shared again.
- **NOT YET** — with the trigger that would reopen it, and the date.

**Separate the artifact from the product.** *"Do not install it, read three files and take
two ideas"* is a legitimate and common verdict.

## Say what you did not check

A triage with no stated blind spot was not a triage. Name what you could not run, could not
see, or took from the README rather than the source — and label a relayed claim as relayed.
