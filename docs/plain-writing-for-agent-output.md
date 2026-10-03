# Write agent output in controlled English, but only the parts that help

An agent's reply is read by a person who is busy, often on a phone, and often about to act on it.
ASD-STE100 (Simplified Technical English) is a controlled language written for aircraft
maintenance manuals, where a misread instruction has a cost. Asking a model to write "80% of the way
to STE" makes replies easier to act on. The whole specification is too strict for this use,
though, so pick the rules that the evidence supports.

In a prompt or instruction file, that looks like this:

> Write about 80% of the way to ASD-STE100. Code, paths, identifiers and section numbers are
> exempt. Follow these six rules: (the list below).

**How the subset was chosen.** One operator, October 2026. A model reviewer scored 40 randomly
sampled assistant replies from a week of interactive work against 11 STE rules. The reviewer had
no part in writing the replies. For each rule it marked the replies where a break plausibly hurt
clarity, and the replies that broke the rule without harm. Six rules earned a place:

| rule | scored as hurting | scored as harmless |
|---|---|---|
| One name for one thing | 6 | 3 |
| Sentences over the limit | 7 | 22 |
| Noun stacks of more than three | 5 | 4 |
| One action per step | 2 | 2 |
| Command before the risk | 2 | 0 |
| Vertical list for parallel items | 2 | 0 |
| Active voice | 0 | about 25 |
| Simple verb forms only | 0 | about 20 |
| Plain-word list ("use", not "utilize") | 0 | judged, not counted |
| Controlled dictionary | not scored | not scored |
| Economy (say each thing once) | not scored | not scored |

**What the evidence can and cannot carry.** This is one person's replies, scored once by one
model pass, with no second reader checking the scores. Counts of 2 against 0 are a lean, not a
result. Treat the six rules as a reasonable starting set, and rerun the sample before you trust
the ranking.

**The six rules.**

- Use one name for one thing. Copy a UI label exactly, every time. In one reply a device setting
  had three names while the reader was hunting for it on a screen.
- Write the command first, then the risk. An action item starts with a verb.
- Give each step one action, and number the steps.
- Split a sentence over 30 words. Keep the verdict and each step under 20. STE's limits are 20
  words for procedures and 25 for description. In this sample they flagged 22 sentences that read
  fine. A limit of 30 still caught every sentence that caused trouble, and those ran 38 to 54 words.
- Stack no more than three nouns. Explain a coined term the first time, or do not use it.
- Use a vertical list for three or more parallel items, and give each paragraph one topic.

**What was rejected, and why.** Active voice and simple verb forms did no measured harm. The
passives had obvious actors, and "is running" is the honest tense for a job still running. The
plain-word list found nothing to fix. The last two rules were judged without counts. STE's
controlled dictionary fights file paths, identifiers and legal section numbers. Its economy rule
fights a reader who asks for important things to be said more than once, and that preference wins.

**Ship a check with it.** A rule that matters is enforced by a check. Three of these rules are
mechanical enough to check:

1. Flag sentences over 30 words, after removing code, URLs and paths.
2. Flag an action item whose first word is a pronoun, article or preposition instead of a verb.
3. Flag em dashes, if the reader has banned them.

Make the check warn, never block. A flag from a prose checker is a judgment, not a proof, so it
must not fail a build. The same sample showed why the em dash check matters. 11 of 40 replies used
em dashes that the operator's own instructions forbade, because nothing checked.

Rerun the sample after a few weeks. A rule that stops catching anything has done its job or never
mattered, and the counts tell you which.
