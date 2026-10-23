# Tier every pull request, and let the tier decide who must review it

Credit: the tiers, "an agent's approval never counts as a person's", "an approval covers one specific
commit" and "start strict and loosen with evidence" are adapted from Addy Osmani, Morgan Westlee Lunt and
Qing Wang's "How the Claude Code team does code review" (Anthropic, 15 October 2026,
[post](https://claude.dev/blog/solving-code-review-at-anthropic/)). The five-point checklist is adapted
from Matt Pocock's `pr` skill ([@mattpocockuk](https://x.com/mattpocockuk),
[skills/engineering/pr/SKILL.md](https://github.com/mattpocock/skills/blob/5beb35b040e3/skills/engineering/pr/SKILL.md)),
as reused in Warp's `merge-risk` skill
([.agents/skills/merge-risk/SKILL.md](https://github.com/warpdotdev/common-skills/blob/8792394ff1b6/.agents/skills/merge-risk/SKILL.md)).

When agents write most of the code, a person cannot read every pull request, and should not have to.
The useful question is not "did a human look?" but "did the right number of independent readers look,
given what this change could break?" Answer it per pull request, with a written rule.

## The three tiers

| Tier | What puts a pull request here | Required before merge |
|---|---|---|
| **Low** | Docs, tests, internal tooling, small fixes; all checks green | Checks green and **one** independent review at the exact head |
| **Medium** | Behavior changes, dependency bumps, schedulers, anything that calls a paid API or outside service | Checks green and **two** independent reviews, ideally from **different model vendors** |
| **High** | Credentials, secrets or auth; money movement; personal, health or client data; anything irreversible (deletes, data migrations); public publishing; CI or deploy config of anything public-facing; the review and safety rules themselves | Two independent reviews **and the operator's approval** |

The highest matching item wins: a one-line change to a high-tier path is high.

Anthropic's version counts people (zero, one, two). In a setup where agents review agents and one
person operates, count **independent reviewers** instead, and reserve the person for the high tier.
"Independent" means a different session from the author, and for the medium tier a different vendor,
so the two reviewers do not share a blind spot.

## Rules that make the tiers hold

1. **An author never reviews its own work.** A session that wrote any commit on the branch cannot review it.
2. **An agent's approval is never recorded as the person's.** A relay of the person's words carries a
   pointer to where they said it.
3. **A review binds to the exact head commit.** A new push needs a new review.
4. **The pull request states its tier and why, in one line.** Whoever merges checks the tier against
   the diff, and moves it up if a higher-tier path is touched. Never down.
5. **Start strict, loosen with evidence.** Count merges and reverts per tier each month. Move a kind of
   change down a tier only after a month of evidence, and only with the operator's yes.

## The checklist every review answers

1. **Alignment.** Does the code do what the pull request and its task say, and nothing else?
   Are drive-by changes named?
2. **Sensitive surface.** Does it touch auth, permissions, payments, personal data, secrets,
   migrations, dependency bumps or infrastructure config, however small the diff?
3. **Verification.** Is there proof from the consuming end: a test seen to fail before the fix, a run,
   a screenshot for a UI change? Unit tests passing is not enough on its own.
4. **Rollback cost.** How hard is this to undo after merge? Name anything irreversible.
5. **Error detection.** Will a failure be noticed before a user reports it? Are errors swallowed, or does
   a fallback hide the problem?

## What it costs, and when it is wrong

- A tier is a judgment. Put the path rules (which directories are high) in a file the merger reads,
  so the judgment is checkable and does not drift between sessions.
- Two reviews from different vendors cost twice one review. Spend it where a miss is expensive, which
  is what the medium tier is for.
- Revert rate is a lagging measure, and a quiet month on a small repo proves little. Prefer a longer
  window over loosening early.

See also: [a written review standard](a-written-review-standard.md), which is what each reviewer is
asked; this page decides how many reviewers are needed.
