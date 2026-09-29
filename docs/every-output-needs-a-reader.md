# Name the reader before you build the producer

Agents make reports, feeds, alerts, dashboards and nightly checks cheap to produce. The expensive
failure is the one nobody notices: the output is produced, it is correct, and nobody reads it. From
one operator's records, September 2026:

- A status feed meant to give a single view of all agents went unpublished for about 163 hours.
  Nobody noticed, because nothing read it.
- Twenty-six nightly reports sat in a folder with no reader. A failing daily job appeared in three
  of them, counted but never named.
- A nightly check's own docstring said its state file existed "so a digest can read the nightly
  result." No digest did.
- About 677 KB of research reports arrived in five days, and nothing recorded which of them
  changed a decision.
- A public catalog and a public guide had 0 and 3 viewers in 14 days, and most of the 3 were the
  author. The guide also showed 130 unique cloners: automation (CI, installs, mirrors), not
  readers.

**The rule.** Before building a producer, name its reader and give it three things: a
**trigger**, so nobody has to remember to run it; a **consuming-end check**, a command that proves
the last run reached the reader, not just that it ran; and a **use record**.

- Every report ends with one action and an owner. At 14 days, mark it used or unused.
- Every recurring workflow gets one row: trigger, inputs, reader, cadence, the measure, the
  command that proves the last run reached its reader, and what happens if it is forgotten. List
  the rows whose last evidence is older than twice their cadence.
- A count is not a finding. "Failed units: 2" without the names hands the reader a search.
- When a producer has no reader, the fix is a reader or a deletion, not a better producer. Reuse a
  view the person already opens before adding a new channel.
- For a public repository, count unique viewers from GitHub's traffic API, not clones, and read
  the referrers beside them. An AI assistant's site can be one of them, so a README that says
  plainly what the repository is and who it is for is part of how people find it.

This is the README's fourteen-day rule applied to everything an agent produces, not only to this
skill. [`read-only-audit.md`](read-only-audit.md) is one case where it decided the outcome.
