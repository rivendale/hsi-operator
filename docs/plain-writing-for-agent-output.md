# Write agent output in controlled English, but only the parts that help

An agent's reply is read by a person who is busy, often on a phone, and often about to act on it.
ASD-STE100 (Simplified Technical English) is a controlled language written for aircraft
maintenance manuals, where a misread instruction has a cost. Asking a model to write "80% of the way
to STE" makes replies easier to act on. The whole specification is too strict for this use,
though, so pick the rules that the evidence supports.

**How the subset was chosen.** One operator, October 2026. A reviewer with no part in writing the
replies scored 40 randomly sampled assistant replies from a week of interactive work against 11 STE
rules. For each rule it counted the replies where breaking the rule plausibly hurt clarity, and the
replies that broke it without harm. Six rules earned a place:

| rule | hurt clarity | broke it, no harm |
|---|---|---|
| One name for one thing | 6 | 3 |
| Sentences over the limit | 7 | 22 |
| Noun stacks of more than three | 5 | 4 |
| One action per step | 2 | 2 |
| Command before the risk | 2 | 0 |
| Vertical list for parallel items | 2 | 0 |
| Active voice | 0 | about 25 |
| Simple verb forms only | 0 | about 20 |

**The six rules.**

- Use one name for one thing. Copy a UI label exactly, every time. In one reply a device setting
  had three names while the reader was hunting for it on a screen.
- Write the command first, then the risk. An action item starts with a verb.
- Give each step one action, and number the steps.
- Split a sentence over 30 words. Keep the verdict and each step under 20. STE's limits (20 words
  for procedures, 25 for description) flagged 22 sentences that read fine; 30 caught every sentence
  that caused trouble, which ran 38 to 54 words.
- Stack no more than three nouns. Explain a coined term the first time, or do not use it.
- Use a vertical list for three or more parallel items, and give each paragraph one topic.

**What was rejected, and why.** Active voice and simple verb forms did no measured harm: the
passives had obvious actors, and "is running" is the honest tense for a job still running. A
plain-word list ("use", not "utilize") found nothing to fix. STE's controlled dictionary fights
file paths, identifiers and legal section numbers. Its economy also fights a reader who asks for
important things to be said more than once; that preference wins.

**Ship a check with it.** A rule that matters is enforced by a check, and a detector over prose
scores the warning as the offense, so this one warns and never blocks. Three of the rules are
mechanical: flag sentences over 30 words (after removing code, URLs and paths), flag an action item
whose first word is a pronoun, article or preposition rather than a verb, and flag em dashes if the
reader has banned them. The same sample showed why the last one matters: 11 of 40 replies used em
dashes that the operator's own instructions forbade, because nothing checked.

Rerun the sample after a few weeks. A rule that stops catching anything has done its job or never
mattered, and the counts tell you which.
