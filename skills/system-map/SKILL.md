---
name: system-map
description: "Use when someone has lost track of how a system actually works and wants to see it, or asks to review an app as a whole: an architecture map, diagram, overview or zoomable canvas of one app, several repos or the infrastructure under them; what happens, step by step, when a user acts or a webhook, event, schedule or outside update fires; where data flows; what a person sees at each point; and which feedback loops hold steady or run away. Builds an evidence-backed model from the code and read-only live checks, draws it as an interactive map to zoom and trace, and compares it with what was intended, so drift becomes a question for the operator. Fits any project: a web app, a game, an operating system, a fleet of services."
license: MIT
---

# system-map

**A map is a measurement. It is half of a loop.**

Agents build faster than anyone can keep the architecture in their head, so people lose
track of what is live, what runs on its own, and how the parts affect each other. A canvas
closes that observation gap. It does not say whether what it shows is what anyone meant.
That is the other half, and this repo already has it: hsi-operator's Door 2 writes down what
done means as a **setpoint**. This skill is the **measurement**. Comparing the two gives
**drift**, and drift goes to the operator through Door 1 as a **correction**. Re-running
the map after a change is the feedback.

| loop part | here |
|---|---|
| setpoint | what the system is supposed to do: Door 2 setpoints, or the operator's own words for the few triggers that matter |
| measurement | `system-model.json`, extracted from code and read-only live checks, every claim cited |
| comparison | drift: setpoints that do not hold or are unmeasured, things built but never intended, intended but missing, loops running away; the map's Done vs actual lens draws it |
| correction | `sysmap items` turns drift into DECIDE items that `hsi` ranks with everything else |

**The failure this prevents has two faces:** an operator who cannot say what their own
system does, and a confident diagram that invents boundaries. Diagrams drawn by a model
from a vague prompt look right and are wrong in exactly the places nobody checks. So every
box, arrow, step and loop here cites a file and line or a dated live measurement, or it is
drawn dashed as unknown.

---

## Running `sysmap`

`sysmap` is a single Python 3 script in this skill's `bin/` folder; it is not on your PATH. Call it by path:

- installed as a plugin: `python3 "${CLAUDE_PLUGIN_ROOT}/skills/system-map/bin/sysmap" check system-model.json`
- from a clone of this repo: `python3 skills/system-map/bin/sysmap check system-model.json`

Or add an alias for the session: `alias sysmap='python3 /path/to/skills/system-map/bin/sysmap'`. `sysmap selftest` proves the install works.

## When to use it, and when not

**Use it** when someone asks how a system works or what happens when something occurs;
says they have lost track; is about to change something that crosses several parts; is
taking over a codebase; or after a burst of agent work, when drift is likeliest. It works
the same for a web app, a game (input, tick, network messages, economy), an operating
system or platform (boot, services, device events, updates), a CLI, or a fleet of
services across many repos and hosts.

**Do not use it** for one function's call path (read it), a question one small diagram
answers (draw that one), deciding whether to adopt a tool (`repo-triage`), or deciding what
done means (Door 2, which this skill asks for but does not replace).

## First, say the scope out loud

Classify before reading anything, and say it so the operator can overrule it in one word:

- **Trace:** one question ("what happens when a customer pays?"). Map the one trigger and
  the nodes it touches, at whatever level it needs. Minutes, not hours.
- **System:** one deployable product. Levels 1 and 2.
- **System of systems:** several repos, hosts or products. Level 0 and 1 everywhere, level
  2 only where a question or a drift item points.

Then write down, before the first read: which repos at which commits, which hosts or
services you may probe read-only and how, what is out of scope, and **who will read the
map and when**. A map with no named reader is a picture nobody opens.

## The method, in order

Detail and stack-by-stack search patterns are in `references/method.md`.

1. **Sources and deploy truth.** List each repo `@ commit`. Read what actually runs first:
   compose files, manifests, platform configs, unit files and timers, CI schedules, ingress.
   When deploy and code disagree, the deploy wins and the disagreement is a gap.
2. **Entry points and triggers, before components.** Every way something starts: user
   actions (pages, forms, commands), webhooks, schedules, queue consumers, inbound email,
   agent and MCP tool entry points, outside updates (pollers, watchers, sync). A component
   list without triggers is a parts catalog; triggers are what people actually ask about.
   Count what you found, and account for every one: mapped, or out of scope with a reason.
3. **Components and stores.** Deployables first, then the parts inside them that own a
   trigger or touch a store. Stores from schemas and migrations, buckets, caches, queues.
4. **Flows.** Walk each trigger edge by edge to its outcome. Each edge is a call, a data
   write or read, an event, a webhook, a schedule or a human action.
5. **Human touchpoints.** For every node, what a person sees or touches there. For every
   trigger, what the person sees afterwards, and how soon. **"None" is a finding, never a
   blank.** This is the HSI layer: control actions go down, feedback comes up, and an action
   with no feedback path is where systems drift unnoticed.
6. **Loops.** Find where an output comes back as an input. Write each link with its sign,
   compute balancing or reinforcing from the signs, and judge stability from a measurement,
   not from the fact that nothing has broken yet.
7. **Data uses.** What each important piece of data is, who makes it, who reads it, and what
   workflow it could serve that it does not. Data with no reader is a gap.
8. **Drift.** Compare against the setpoints. Classify each difference (see below).
9. **Check, render, second reader.** `sysmap check` until it passes; render; then a second
   agent that did not build the model re-measures every unstable loop, dead node and drift
   item before the operator sees them. A builder's verdict is a candidate, not a finding.

## Evidence rules

The contract and every rule's enforcement are in `references/model-schema.md`. The rules
that matter most:

- **Cite or mark unknown.** Evidence is `owner/repo/path:LINE`, a URL, or
  `live YYYY-MM-DD: what was run: what it showed`. Nothing else counts, including "see the
  README".
- **In code is not live.** `live` means measured working: the endpoint answered, the metric
  moved, the job's last run is known. Code that exists but never runs is `dead`; code nobody
  measured is `unknown`. Statuses are where operators get misled, so they get the strictest
  reading.
- **Docs last, as claims to check.** A README describes intent. Read the file that does the
  thing.
- **Compute the loop type; never assert it.** With signed links, `sysmap check` refuses a
  type that contradicts its own signs.
- **Reconcile counts.** Triggers found, triggers mapped, triggers excluded: the three numbers
  add up, or the map is quietly partial.
- **Verify citations against the checkout:** `sysmap check --src owner/repo=DIR` refuses a
  missing file or a line past the end, and warns when the checkout is not the mapped commit.
  It cannot tell whether the line supports the claim; the second reader does that.

## Many repos and infrastructure

- **One model.** One `meta.sources` line per repo with its commit; every citation starts with
  `owner/repo/`. Ids stay unique across repos (prefix them when lanes work in parallel).
- **Level 0** is products, people and outside services; **level 1** is deployables, stores,
  queues and schedulers; **level 2** is components. Hosts, proxies, DNS and monitors appear
  as nodes only where they change what a flow does; a monitor and its alert route are
  usually a balancing loop with a person in it.
- **A cross-repo edge cites both ends:** the producer's call and the consumer's handler. An
  edge you can cite at one end only is a gap ("sends to a route nobody serves", or the
  reverse).
- **Fan out by repo, merge in one place.** Each lane returns a model fragment as a file path,
  not a payload in its reply; the parent merges, runs `sysmap check`, and resolves id
  collisions. Lanes stay read-only and get a written list of what they may not touch.
- **What you cannot read is one node.** A private repo or a vendor's internals becomes a
  single `external` node with status `unknown` and the reason, not a guess at its insides.

## What you hand over

1. **`system-model.json`**, passing `sysmap check`.
2. **The map:** `sysmap render system-model.json -o system-map.html --title "Two To Four Words"`
   embeds the model in the viewer (`assets/viewer.html`), one HTML file: zoom from level 0 to
   level 2, play a trigger step by step, switch on the loop overlay, compare done with actual
   in the drift lens. It must work on a phone. The file is an artifact body; add `--standalone`
   for a copy that opens from disk. For a hosted page that must make no third-party request,
   add `--vendor-dir DIR`: each CDN script is pointed at the file in DIR whose hash matches its
   pinned integrity, the Google Fonts links become `DIR/fonts/fonts.css` (or system fonts), and
   render refuses rather than write a page that still reaches another host. Set
   `meta.mapped_at` and `meta.commits` so the header says when the map was made and from what.
3. **A short reading note**, written for the person, before the map: what the system does
   in one sentence, its main parts in plain words, and **the five things worth knowing**
   (drift, unstable loops, triggers that end in "none"). The map is for exploring; the note
   is what gets read.
4. **Drift items:** `sysmap items system-model.json > drift-items.json`, then
   `hsi drift-items.json`. The items arrive with empty options on purpose: frame them (2 to 4
   options, each with its consequence) before they reach the operator, and drop any whose
   answer does not depend on the operator's preference, intent, risk appetite, money,
   relationships, legal exposure or taste.

## Close the loop: intent against the map

The model carries both halves. Everything else in it is the measurement; `setpoints` is the
reference. The contract for both is `references/model-schema.md`.

- **Setpoint first.** One entry per intent: `about` (the trigger or part it governs), `intent`
  (what should happen, in plain words: what done means), `measure` (what on the map or which
  read-only probe shows it), `source` and `source_ref`, `status`, `holds` (`yes`, `no` or
  `unknown`) and `why`. If Door 2 setpoints exist, carry them over and cite their ids on the
  triggers they govern (`triggers[].setpoint`). If none exist for a running system, ask the
  operator for the three to five triggers they care about, in their words ("when a customer
  pays, they see a receipt within a minute"). Those are `confirmed`. A setpoint you take from
  a README, a design note or a decision record is `proposed` until the operator confirms it;
  `sysmap check` refuses either mismatch. Do not invent intent from the code: that grades the
  system against itself.
- **Classify every gap**, so the correction step can route it (`gaps[].kind`, required):
  - `unintended`: running, and no stated intent asks for it, or it works against one (a
    scheduled job whose output nobody reads, machine text shown as a person's own)
  - `missing`: intended, and absent or broken (a promised confirmation that never reaches
    the person)
  - `runaway`: a loop moving away from its target (a retry storm, output outpacing its
    readers, spend climbing)
  - `unknown`: worth knowing, and nobody can say yet whether it was meant. Not drift.

  Name the setpoint a gap breaks (`gaps[].setpoint`) and the parts it is about (`gaps[].nodes`).
- **Drift** is every setpoint that does not hold or that nobody has measured, plus every gap
  that is unintended, missing or running away.
- **The drift lens shows it.** The map's **Done vs actual** tab lists the setpoints grouped
  by does not hold, not known and holds, each with its intent, how it is measured, its source,
  and whether it is confirmed or only proposed. Picking one highlights the path of the event
  it is about, or the part, plus the parts its gaps name. The **Drift** overlay rings every
  part involved: dashed where what runs is not what was meant, dotted where nobody has
  measured, with a count on each part; it is drawn differently from the loop overlay so both
  can be on. A map with no setpoints hides the lens.
- **Route the drift into the hsi-operator queue:**

  ```
  sysmap items system-model.json > drift-items.json
  hsi drift-items.json
  ```

  `sysmap items` makes one DECIDE item per drift gap (carrying the setpoint it names, so that
  setpoint is not asked twice), one per setpoint that does not hold or is unmeasured and that
  no drift gap carries, and one per `unstable` loop. An item is `signal: error` only when a
  confirmed setpoint fails; a failure against a merely proposed one is a proposal, and its
  question asks the operator to confirm or correct the intent first. Frame 2 to 4 options for
  each before it reaches Door 1, and drop any whose answer does not depend on the operator.
- **Re-map after a change; that is the feedback.** `sysmap diff old.json new.json` reports a
  setpoint whose `holds` moved, so a fix shows up as `holds 'no' -> 'yes'`.
- **Not every gap is drift, and not every drift needs the operator.** A broken citation is
  your work; "keep or remove this job" is theirs.

## Keeping a map current

- A map is true at `meta.as_of` and the commits in `meta.sources`. It goes stale on a
  condition, not a date: a new entry point, a new deployable, a migration, a new outside
  service, or a `watch` loop whose measurement moved. `sysmap check --src` warns when a
  checkout has moved past the mapped commit.
- **Keep the old model and diff it:** `sysmap diff old.json new.json` lists what disappeared
  first, because a deletion is the change nobody sees in the new picture.
- Keep ids stable and meaningful so a diff compares like with like.
- **If nobody has opened the map in two weeks, that is the finding.** Ask whether it answers
  a question anyone has, before adding detail to it.

## What not to do

- **Never read secrets.** No `.env` files (`.env.example` is fine), key files, token stores
  or credential directories. Take variable **names** from the code that reads them, never
  values. Report where a credential lives, never what it is. `sysmap check` refuses a
  citation of a secret file and any credential-shaped string in the model.
- **Never write to what you map.** No deploys, restarts, migrations, test payments, or posts
  to a webhook "to see what happens." Live checks are reads: health endpoints, status and
  list commands, metric queries, log line counts.
- **Never copy user data into the model.** Architecture only. A measurement may use counts
  and aggregates; it never names a person, quotes a message or shows a record.
- **Never draw a box you cannot cite**, and never let a layout invent a boundary: grouping
  comes from `parent`, and `parent` comes from deploy truth.
- **Do not map everything at level 2.** A canvas of five hundred boxes is a list of zero.
  Go deep only where a question or a drift item points.
- **Do not call a loop stable because it has not failed yet.** Unmeasured is `watch`.
- **Do not hand over a map when a sentence answers the question.**

## Honest limitations

- `sysmap check` verifies shape, references, citation form, and with `--src` that cited
  lines exist. It cannot tell whether a citation supports its claim, and it cannot see what
  static reading misses: routes built from config, feature flags, dynamic dispatch,
  reflection. Say what was not traced.
- Whether a loop is stable is a judgment backed by a measurement, not a computation. The
  checker computes the type from signs; it does not compute stability.
- The map is only as current as its last run. Nothing here re-runs it on its own.
- The viewer is one HTML file; what it loads at view time is stated at the top of
  `assets/viewer.html`.
