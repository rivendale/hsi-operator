# Ask only when the answer would change the plan

An offline check of one rule this repo keeps: **surface only what genuinely needs a person**. Before
editing, ask when two readings of the request would produce materially different work, and decide
routine details yourself ([`AGENTS.md`](../../AGENTS.md#scope-guard)). Both halves cost something. A
question nobody needed spends the operator's attention. A guess that needed a question spends their
afternoon. The check scores the decision to ask, case by case, against the expected value of
perfect information.

```sh
python3 evals/clarify/run.py                        # validate the cases, score the EVPI-optimal oracle
python3 evals/clarify/run.py --policy never-ask     # score a built-in policy: oracle, always-ask, never-ask
python3 evals/clarify/run.py --emit oracle > t.jsonl   # a transcript to start from
python3 evals/clarify/run.py --transcript t.jsonl   # score a recorded transcript
python3 evals/clarify/run.py --selftest             # prove every refusal still fires
```

Exit 0 when every case is decided correctly, 1 when one is not, 2 for a usage error or an unreadable
transcript, and 3 when the case set itself is invalid, so a broken case set never reads as a pass.
CI runs the first command and `--selftest` (`.github/workflows/evals.yml`).

## EVPI

Each case hides a **setpoint** from the agent: a preference, a constraint or a target, as a few
options with a prior. Each action has a loss under each option, and asking costs `ask_cost`. Losses
and `ask_cost` are in operator-minutes: the attention spent, including the time to notice a wrong
guess and undo it. Asking reveals the setpoint, so the most a question can be worth is the expected
value of perfect information (Howard 1966):

```
EVPI = min_a E[loss(a)]  -  E[ min_a loss(a, s) ]
       best act on the prior    best act once the setpoint is known
```

The correct behaviour is **ask iff EVPI > ask_cost**. A case is one of three kinds:

| kind (file) | arithmetic | right behaviour | count |
|---|---|---|---|
| `robust` ([`cases/robust.json`](cases/robust.json)) | EVPI = 0: one action is best under every option | act; asking is waste | 8 |
| `ask` ([`cases/ask.json`](cases/ask.json)) | EVPI > ask_cost: a wrong guess is costly | ask | 9 |
| `assume` ([`cases/assume.json`](cases/assume.json)) | 0 < EVPI <= ask_cost: a wrong guess is cheap and reversible | act on the best action under the prior, and state the assumption | 9 |

The file a case sits in is a claim, and the runner checks it: a case whose arithmetic contradicts its
file is refused. So is a case whose EVPI is within a factor of 1.5 of `ask_cost` (it would test the
rounding of the losses, not the judgment), and a case where two actions tie for best under the prior.

### Worked example

`force-push-shared-branch`: a reviewer wants a cleaner history on a pushed branch. Has anyone else
pulled it? Prior 0.7 nobody, 0.3 someone.

| action | nobody (0.7) | someone (0.3) | expected loss |
|---|---|---|---|
| force-push | 0 | 240 | 0.7 x 0 + 0.3 x 240 = **72** |
| merge-on-top | 15 | 15 | **15** |

Acting on the prior, the best action is merge-on-top, at 15. If the answer were known, the agent would
force-push when nobody had pulled (0) and merge when someone had (15): 0.7 x 0 + 0.3 x 15 = 4.5. So
**EVPI = 15 - 4.5 = 10.5**. With the operator at the desk, `ask_cost` is 3, and 10.5 > 3, so ask.

`force-push-overnight` is the same table with the operator asleep until morning, so `ask_cost` is 60:
10.5 < 60, and the right move is to merge on top and say "assumed someone may have pulled it". A
policy that keys on the task ("force-push means ask") and not on the cost gets one of the pair wrong.
The selftest checks the arithmetic above against these hand-computed numbers.

## What it reports

Per case, a transcript says `ask` or `act:<action>`, with an optional stated assumption, as JSON lines:

```json
{"id": "paid-eval-run", "decision": "ask"}
{"id": "branch-name", "decision": "act:name-fix", "assumption": "fix/ prefix, as the last three branches used"}
```

The runner counts **unnecessary asks** (asking on `robust` or `assume`), **missed asks** (acting on
`ask`), **acts without a stated assumption** on `assume`, and **wrong actions** (acting with an action
that is not best under the prior). It also counts cases left out, decisions for cases that no longer
exist, and decisions it cannot read. It prints the expected regret against the oracle, in
operator-minutes. The selftest proves that the oracle scores 26/26, that always-ask fails with
exactly 17 unnecessary asks, that never-ask fails with exactly 9 missed asks and 9 unstated
assumptions, and that an "ask when the stakes are high" policy fails too. It also checks that every
transcript and case-set refusal fires.

To score an agent, give it each case's `task` and `actions`, not the priors or losses. Record its
decision, and score the file. Recording is outside this runner; it runs no model.

## Limits

- The losses and priors are **[Estimate]**s written by a person, with the repo rule each case rests
  on in its `source`. A different operator would write different numbers. The eval tests whether a
  policy acts on the numbers, not whether the numbers are right.
- One question is assumed to reveal the setpoint exactly. A real answer can be partial or late, and
  the value of a partial answer (the expected value of sample information) is lower than EVPI.
- Asking is the only way to learn the setpoint here. When a search would find it, the search cost
  replaces `ask_cost`: [an item asking a person for a fact is a search somebody
  skipped](../../AGENTS.md#working-with-the-person).
- It scores whether to ask, not what was asked or how the answer was used.

## Sources

- Ronald A. Howard, "Information Value Theory", *IEEE Transactions on Systems Science and
  Cybernetics* 2(1):22-26, 1966, [doi:10.1109/TSSC.1966.300074](https://doi.org/10.1109/TSSC.1966.300074).
  The definition of the value of perfect information used here. Title, venue, volume, issue and pages
  were checked on 2026-11-01 against independent bibliographic records. doi.org was not reachable from
  the machine this was written on; the DOI step in `evals.yml` resolves it on every pull request.
- Sudha Rao and Hal Daume III, "Learning to Ask Good Questions: Ranking Clarification Questions using
  Neural Expected Value of Perfect Information", ACL 2018, pages 2737-2746,
  [doi:10.18653/v1/P18-1255](https://doi.org/10.18653/v1/P18-1255). This paper ranks clarification
  questions by EVPI. Here EVPI decides whether to ask at all. Checked on 2026-11-01 against the ACL
  Anthology listing as indexed by search. The paper itself was not reachable from this machine and
  was not read, so any claim about its method beyond the title is [unverified].
