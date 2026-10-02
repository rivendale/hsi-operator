# The system model: the contract

One JSON file, `system-model.json`, is the only thing the skill produces by reading. The
viewer draws it, `bin/sysmap check` refuses it when it lies, and `bin/sysmap items` turns its
drift into questions for the operator. Nothing else reads the code.

The model holds both halves of a loop. Most of it is the **measurement**: what runs, read from
code and live checks. `setpoints` is the **reference**: what done means, in the operator's
words or taken from a document. The difference between them is **drift**.

Every rule below that says **FAIL** is enforced by `sysmap check`. A rule that says **WARN**
is printed and does not fail unless you pass `--strict`. Prose without a check is marked as
such.

## Shape

```
{
  "meta":   {"name": str, "scope": str, "as_of": "YYYY-MM-DD", "sources": [str], "notes": str?,
             "glossary"?: [{"term": str, "means": str}], "mapped_at"?: "YYYY-MM-DDTHH:MMZ",
             "commits"?: [{"repo": "owner/repo", "commit": sha}]},
  "levels": [{"id": 0, "name": "System of systems"}, {"id": 1, "name": "Systems"}, {"id": 2, "name": "Components"}],
  "nodes":  [{"id", "label", "kind", "level", "parent", "does", "human_sees",
              "inputs": [str], "outputs": [str], "status", "evidence": [str]}],
  "edges":  [{"id", "from", "to", "kind", "label", "data", "evidence": [str], "status"?}],
  "triggers": [{"id", "kind", "label",
                "steps": [{"edge", "narration", "evidence"?: [str]}],
                "outcome", "human_feedback", "setpoint"?}],
  "loops":  [{"id", "type", "nodes": [id], "story", "stability", "why", "evidence": [str],
              "label"?: str, "links"?: [{"from", "to", "sign", "delay"?, "label"?}]}],
  "data_uses": [{"data", "produced_by": [id], "used_by": [id], "could_serve": [str]}],
  "gaps":   [{"title", "detail", "evidence": [str], "kind", "setpoint"?, "nodes"?: [id]}],
  "setpoints"?: [{"id", "about", "intent", "measure", "source", "source_ref", "status", "holds", "why"}]
}
```

A `?` marks an optional field. A viewer must ignore any field it does not know, so optional
fields can be added without breaking a drawing.

## Fields

### meta
- `name`: what the map is of, in the words a person would use.
- `scope`: what is in and what is out, in one or two sentences. Say "architecture only".
- `as_of`: the day the measurements were taken. **FAIL** if not `YYYY-MM-DD`.
- `sources`: one line per repo as `owner/repo @ <commit>`, plus one line per kind of live
  check. **FAIL** if empty. `sysmap check --src` compares the commit with the checkout and
  **WARNs** on a mismatch.
- `mapped_at` (optional): when the map was last made, as a UTC time. The viewer shows it in
  the header as "Last mapped"; without it the header can show only the `as_of` date. **FAIL**
  if present and not `YYYY-MM-DDTHH:MM(:SS)Z`.
- `commits` (optional): each repo the map was read from and the full commit, as
  `{"repo", "commit"}`, so the header can name them. **FAIL** if a commit is not 7 to 40 hex
  characters, or contradicts the commit `sources` names for the same repo.
- `notes` (optional): anything a reader needs that fits nowhere else.
- `glossary` (optional): names that mean the same thing, as `{"term", "means"}` (a product
  name, a repo name and an informal name for one system). The viewer lists them under About and
  finds them in search. **FAIL** if an entry has no term or no meaning.

### levels
Three levels, zoomed like a map: **0** the system of systems (products, people, outside
services), **1** systems (deployables, stores, queues, schedulers, outside APIs), **2**
components inside a system (a route, a handler, a job, a table group). **FAIL** if a node
uses a level that is not declared here.

### nodes
| field | meaning |
|---|---|
| `id` | stable and readable (`svc_api`, `job_nightly_digest`), never `n17`: ids survive regeneration only if they mean something, and `sysmap diff` compares by id. **FAIL** on a duplicate, including a node id equal to an edge id (the viewer keeps both in one namespace). |
| `label` | what a person calls it |
| `kind` | `human`, `ui`, `service`, `job`, `store`, `external`, `agent`, `queue`, `channel` (email, chat, push, SMS: anything that carries a message to a person) |
| `level`, `parent` | `parent` nests a level-2 node in its level-1 system and a level-1 node in its level-0 system. **FAIL** if the parent is unknown or not exactly one level up, if a level-0 node has a parent, or if a level-2 node has none. **WARN** for a level-1 node with no parent when level-0 nodes exist. |
| `does` | one plain sentence: what it does. Not what it is built with. |
| `human_sees` | what a person sees or touches here, or `""`. This field is the HSI layer: a node where it stays empty is one no person can observe. |
| `inputs`, `outputs` | plain names of what goes in and out |
| `status` | `live` measured working; `partial` runs but some path is broken, unused or unreachable; `dead` present in code but not deployed or never fires; `unknown` not verified. |
| `evidence` | see **Evidence** below |

### edges
- `from`, `to`: node ids. **FAIL** if either is unknown.
- `kind`: `call` (request and response), `data` (a write or read; the arrow follows the data, so a
  read points from the store to the reader), `event` (published or enqueued, consumed later),
  `webhook` (an outside service calls in), `schedule` (a timer starts it), `human` (a person
  acts, or something reaches a person).
- `label`: a verb phrase. `data`: the payload in architecture terms (`upload id`, `signed payment
  event`), never a value.
- `evidence` is required and `status` is optional (`unknown` excuses missing evidence).
  These two fields go beyond the first draft of the contract because the evidence rule
  needs them.

### triggers
Every way something starts. `kind`: `user_action`, `event`, `webhook`, `schedule`,
`external_update`.
- `steps`: an ordered walk along edges. Each step names an `edge` (**FAIL** if unknown) and
  narrates it in one sentence (**FAIL** if empty). A step inherits its edge's evidence and may
  add its own.
- **WARN** when a step starts at a node no earlier step reached: either time passed (a timer
  fired later, a person came back) or a step is missing. Say which in the narration.
- `outcome`: what is true afterwards. `human_feedback`: what the person sees afterwards, or
  the word `none` with the reason. **FAIL** if empty: "none" is a finding, a blank is an
  omission.
- `setpoint` (optional): the id of the stated intent this trigger is measured against,
  usually a hsi-operator setpoint. This is how the map joins the controller.

### loops
- `type`: `balancing` (corrects toward a target: stability) or `reinforcing` (more of X
  produces more of X: runaway risk, or growth).
- `nodes`: the loop's members in order, at least two, all known (**FAIL** otherwise).
- `links` (optional, recommended): the causal chain, one entry per hop, each with `sign` `+`
  (more of `from` gives more of `to`) or `-` (more gives less), and `delay: true` where the
  effect lags. When present: the links must close one cycle through exactly the listed nodes,
  and **the type is computed, not asserted**: an odd number of `-` is balancing, an even number
  is reinforcing. **FAIL** if the stated type disagrees with the signs. Without links, **WARN**
  that the type is asserted, and **WARN** for each hop that is not an edge on the map (the
  viewer cannot draw a loop it cannot trace).
- `stability`: `stable`, `watch` or `unstable`; `why` says what was measured. **WARN** when a
  loop is called `stable` or `unstable` with no `live` evidence line: a stability verdict
  without a measurement is a guess, and `watch` with "unmeasured" is the honest label.
- `story`: one or two sentences a person can follow without the diagram.
- `label` (optional): a short name of a few words ("Producer brake"). The viewer puts it on the
  loop's badge and in the loop list; without it, the viewer uses the story's opening words.

### data_uses
What each important piece of data is, who makes it, who reads it, and which workflows it
could serve that it does not today. **FAIL** on an unknown id. **WARN** when `used_by` is
empty: data nobody reads is an output without a reader.

### gaps
Anything the map found that someone should know. **FAIL** without evidence; for an absence,
the evidence is the search that came back empty (`live 2026-10-01: grep -rn receipt api/: 0 hits`).

- `kind` (required) names the drift class, so the correction step can route it. **FAIL** when
  it is missing or not one of these four:
  - `unintended`: built and running, and no stated intent asks for it, or it works against
    one (a scheduled job whose output nobody reads, machine text shown as a person's own)
  - `missing`: intended, and absent or broken on the map
  - `runaway`: a loop moving away from its target
  - `unknown`: worth knowing, but nobody can say yet whether it was meant. Not drift.
- `setpoint` (optional): the id of the setpoint the gap was compared against. **FAIL** when the
  model has a `setpoints` section and no setpoint has that id; **WARN** when there is no section,
  because the reference cannot be checked or drawn.
- `nodes` (optional): the parts the gap is about. The viewer highlights them when the gap is
  picked and marks them in the drift overlay. **FAIL** on an unknown id.

These kind names replaced `drift_unintended`, `drift_missing`, `drift_runaway` and `gap` on
2026-10-01, before any map shipped. The checker refuses the old names, so a map written
against them fails loudly instead of drawing wrong.

### setpoints (the controller half)
What done means, one entry per intent, written down before it is compared with the map. The
section is optional so that a measurement-only map still draws, but a map without it **WARNs**:
it has nothing to compare against, so it cannot show drift. The viewer hides its Done vs actual
lens when there are no setpoints.

| field | meaning |
|---|---|
| `id` | short and stable (`S4`, `paid-sees-receipt`). **FAIL** on a duplicate. |
| `about` | the trigger id or node id this intent governs. **FAIL** if it names neither. A trigger may also name its setpoint (`triggers[].setpoint`). |
| `intent` | what SHOULD happen, in plain words: what done means. One or two sentences the operator would recognize as theirs. |
| `measure` | what on the map, or which read-only live probe, shows whether it holds |
| `source` | `operator` (their own words), `doc` (a README, design note or code comment) or `decision` (a dated decision record) |
| `source_ref` | where it came from: `owner/repo/path:LINE`, or a quote with its date. Not resolved against a checkout. |
| `status` | `confirmed` or `proposed`. The operator's own words are `confirmed`. A setpoint taken from a document or decision stays `proposed` until the operator confirms it; then its source becomes `operator` and `source_ref` quotes the confirmation. **FAIL** on either mismatch. |
| `holds` | `yes`, `no` or `unknown`, judged against this map and its live checks |
| `why` | what was measured to reach that verdict, in a sentence or three |

Every field is required: **FAIL** when one is empty or outside its values. Do not invent intent
from the code; that grades the system against itself.

### drift, and where it goes
**Drift** is every setpoint whose `holds` is `no` or `unknown`, plus every gap of kind
`unintended`, `missing` or `runaway`. The viewer's **Done vs actual** lens lists the setpoints
grouped by `holds`, and its drift overlay marks every part and connection involved: for a
setpoint about a trigger, the parts and connections on its steps; for one about a part, that
part; for a drift gap, its `nodes` and the connections between them. A part touched only by
setpoints that hold `unknown` is marked as unmeasured, not as off target.
`sysmap items` routes drift to hsi-operator as DECIDE items, with empty options for an agent or
the operator to frame:

- each drift gap becomes one item, carrying the setpoint it names, so that setpoint is not
  asked twice;
- each setpoint that does not hold or is unmeasured, and that no drift gap carries, becomes one
  item;
- each `unstable` loop becomes one item.

`signal` is `error` only when a **confirmed** setpoint fails: it holds `no`, or a `missing` or
`runaway` gap names it. Everything else is `proposal`, because a document's intent is a claim
until the operator says that is what done means. `sysmap diff` reports a setpoint whose `holds`
changed, which is how a re-run after a fix shows the loop closing.

## Evidence

Every node, edge, loop and gap carries a non-empty `evidence` list, or the node or edge says
`status: "unknown"` and is drawn dashed. Each entry is one of three forms, and anything else
**FAILs**:

| form | example | proves |
|---|---|---|
| `owner/repo/path:LINE` or `:LINE-LINE` | `acme/uploads/api/src/routes/uploads.ts:12` | the code says so, at the commit in `meta.sources` |
| a URL | `https://status.example.com/` | a page says so (a claim, unless it is the live thing itself) |
| `live YYYY-MM-DD: what was run: what it showed` | `live 2026-10-01: GET /healthz: 200, version 3f2c9e1` | it was measured working that day |

- **In code is not live.** **WARN** with a count of `live` nodes whose evidence, and whose
  ancestors' evidence, holds no `live` line. A component inside a deployable measured live at
  the cited commit inherits that measurement; a component in a box nobody measured does not.
  People (`human`) are exempt.
  The viewer draws the same warning where it applies: such a part gets a hollow status dot
  and a "Live, unmeasured" chip, and a loop rated `stable` or `unstable` with no `live` line
  says "unmeasured" on its badge (a stable one turns grey, not green). The About tab counts
  both, so the warning reaches the reader and not only the terminal.
- **FAIL** when a citation points at a secret file (`.env` and its variants other than
  `.env.example`, key and certificate files, credential and secret stores). A map cites the
  code that reads a variable, never the file that holds it.
- **FAIL** when any string in the model looks like a live credential (private key block, cloud
  access key, common API token prefixes, a JWT). The checker prints where, never what.
- With `--src owner/repo=DIR`, each citation under that prefix must name a file that exists in
  `DIR`, inside `DIR`, with at least that many lines. **FAIL** otherwise, and **FAIL** if no
  citation matched any prefix, because a check that resolved nothing did not run.
- Not checked, by anything: that the cited line supports the claim. A second reader does that.

## Tiny example

A hypothetical photo-upload app: a web page, one API, a queue, a worker, a store, a database,
and a payment provider that calls back. It has two triggers, one balancing loop, one
reinforcing loop on watch, three gaps (two of them drift), and four setpoints: one holds, two
do not, and one nobody has measured. `sysmap selftest` reads this block, requires it to pass
with no warnings, then breaks it on purpose. It is also the model built into
`assets/viewer.html`, so the viewer opened on its own shows every lens.

<!-- sysmap:example -->
```json
{
  "meta": {
    "name": "Tiny Uploads (example)",
    "scope": "A hypothetical photo-upload web app: the web page, the API, the thumbnail worker, storage and the payment callback. Architecture only.",
    "as_of": "2026-10-01",
    "sources": [
      "acme/uploads @ 3f2c9e1 (matches the deployed image, measured 2026-10-01)",
      "live read-only checks 2026-10-01: GET /healthz, the queue_depth metric, the bucket size"
    ]
  },
  "levels": [{"id": 0, "name": "System of systems"}, {"id": 1, "name": "Systems"}, {"id": 2, "name": "Components"}],
  "nodes": [
    {"id": "product", "label": "Tiny Uploads", "kind": "service", "level": 0, "parent": null,
     "does": "Lets a customer upload photos and get thumbnails back, on a free or paid plan.",
     "human_sees": "the web app", "inputs": ["photos", "payments"], "outputs": ["thumbnails"],
     "status": "live", "evidence": ["live 2026-10-01: GET https://uploads.example.com/healthz: 200, version 3f2c9e1"]},
    {"id": "customer", "label": "Customer", "kind": "human", "level": 0, "parent": null,
     "does": "Uploads photos and pays for a plan.", "human_sees": "the upload page and the plan badge",
     "inputs": ["tile states", "plan badge"], "outputs": ["photos", "payments"],
     "status": "live", "evidence": ["acme/uploads/web/src/pages/Upload.tsx:14"]},
    {"id": "payments", "label": "Payment provider", "kind": "external", "level": 0, "parent": null,
     "does": "Takes card payments on its hosted page and calls back when one succeeds.",
     "human_sees": "the provider's hosted checkout page", "inputs": ["card details"], "outputs": ["signed payment events"],
     "status": "live", "evidence": ["acme/uploads/api/src/billing/checkout.ts:8", "live 2026-10-01: provider dashboard, webhook endpoints: 1 endpoint, last delivery 200"]},
    {"id": "web", "label": "Web app", "kind": "ui", "level": 1, "parent": "product",
     "does": "The page where a customer uploads photos and watches them finish.",
     "human_sees": "an Upload button, a grid of tiles marked Processing or Ready, a plan badge",
     "inputs": ["upload state"], "outputs": ["uploads", "status polls"],
     "status": "live", "evidence": ["acme/uploads/web/src/pages/Upload.tsx:14"]},
    {"id": "api", "label": "API", "kind": "service", "level": 1, "parent": "product",
     "does": "Accepts uploads and payment callbacks and answers status polls.",
     "human_sees": "", "inputs": ["uploads", "payment events", "polls"], "outputs": ["jobs", "upload state"],
     "status": "live", "evidence": ["acme/uploads/api/src/server.ts:22", "acme/uploads/fly.toml:1"]},
    {"id": "r_upload", "label": "POST /uploads", "kind": "service", "level": 2, "parent": "api",
     "does": "Checks the plan limit, stores the original and queues a thumbnail job.",
     "human_sees": "", "inputs": ["photo", "plan"], "outputs": ["original", "upload row", "job"],
     "status": "live", "evidence": ["acme/uploads/api/src/routes/uploads.ts:12"]},
    {"id": "r_status", "label": "GET /uploads/:id", "kind": "service", "level": 2, "parent": "api",
     "does": "Says whether an upload's thumbnail is ready.",
     "human_sees": "", "inputs": ["upload id"], "outputs": ["upload state"],
     "status": "live", "evidence": ["acme/uploads/api/src/routes/uploads.ts:48"]},
    {"id": "r_hook", "label": "POST /webhooks/payments", "kind": "service", "level": 2, "parent": "api",
     "does": "Verifies the provider's signature and marks the account paid.",
     "human_sees": "", "inputs": ["signed payment event"], "outputs": ["plan change"],
     "status": "live", "evidence": ["acme/uploads/api/src/routes/payments.ts:9"]},
    {"id": "q_thumbs", "label": "Thumbnail queue", "kind": "queue", "level": 1, "parent": "product",
     "does": "Holds thumbnail jobs until the worker takes them.",
     "human_sees": "", "inputs": ["jobs", "retried jobs"], "outputs": ["jobs"],
     "status": "live", "evidence": ["acme/uploads/api/src/queue.ts:5", "live 2026-10-01: queue_depth metric, 7 days: daily max 41, daily min 0"]},
    {"id": "worker", "label": "Thumbnail worker", "kind": "job", "level": 1, "parent": "product",
     "does": "Takes up to four jobs at once, writes thumbnails, and re-queues a job that times out.",
     "human_sees": "", "inputs": ["jobs", "originals"], "outputs": ["thumbnails", "ready flags", "retried jobs"],
     "status": "live", "evidence": ["acme/uploads/worker/src/index.ts:30"]},
    {"id": "files", "label": "Object storage", "kind": "store", "level": 1, "parent": "product",
     "does": "Keeps originals and thumbnails.",
     "human_sees": "", "inputs": ["originals", "thumbnails"], "outputs": ["thumbnails"],
     "status": "live", "evidence": ["acme/uploads/api/src/storage.ts:3", "live 2026-10-01: bucket size 182 GB, up 9 GB in 30 days"]},
    {"id": "db", "label": "Database", "kind": "store", "level": 1, "parent": "product",
     "does": "Keeps accounts, plans and upload records.",
     "human_sees": "", "inputs": ["upload rows", "plan changes"], "outputs": ["upload state", "plan"],
     "status": "live", "evidence": ["acme/uploads/api/migrations/001_init.sql:1"]}
  ],
  "edges": [
    {"id": "e1", "from": "customer", "to": "web", "kind": "human", "label": "picks a photo and presses Upload", "data": "photo file", "evidence": ["acme/uploads/web/src/pages/Upload.tsx:31"]},
    {"id": "e2", "from": "web", "to": "r_upload", "kind": "call", "label": "POST /uploads", "data": "multipart photo", "evidence": ["acme/uploads/web/src/api.ts:12"]},
    {"id": "e3", "from": "r_upload", "to": "files", "kind": "data", "label": "writes the original", "data": "original image", "evidence": ["acme/uploads/api/src/routes/uploads.ts:20"]},
    {"id": "e4", "from": "r_upload", "to": "db", "kind": "data", "label": "inserts an upload row as processing", "data": "upload row", "evidence": ["acme/uploads/api/src/routes/uploads.ts:24"]},
    {"id": "e5", "from": "r_upload", "to": "q_thumbs", "kind": "event", "label": "enqueues a thumbnail job", "data": "upload id", "evidence": ["acme/uploads/api/src/routes/uploads.ts:27"]},
    {"id": "e6", "from": "q_thumbs", "to": "worker", "kind": "event", "label": "delivers the next job", "data": "upload id", "evidence": ["acme/uploads/worker/src/index.ts:30"]},
    {"id": "e7", "from": "worker", "to": "files", "kind": "data", "label": "writes the thumbnail", "data": "thumbnail image", "evidence": ["acme/uploads/worker/src/index.ts:41"]},
    {"id": "e8", "from": "worker", "to": "db", "kind": "data", "label": "marks the upload ready", "data": "upload state", "evidence": ["acme/uploads/worker/src/index.ts:44"]},
    {"id": "e9", "from": "worker", "to": "q_thumbs", "kind": "event", "label": "re-enqueues a job that timed out, with no cap", "data": "upload id", "evidence": ["acme/uploads/worker/src/index.ts:52"]},
    {"id": "e10", "from": "web", "to": "r_status", "kind": "call", "label": "polls every 3 seconds", "data": "upload id", "evidence": ["acme/uploads/web/src/api.ts:20"]},
    {"id": "e11", "from": "db", "to": "r_status", "kind": "data", "label": "reads the upload state", "data": "upload state", "evidence": ["acme/uploads/api/src/routes/uploads.ts:50"]},
    {"id": "e12", "from": "web", "to": "customer", "kind": "human", "label": "shows the tile as Ready", "data": "tile state", "evidence": ["acme/uploads/web/src/pages/Upload.tsx:52"]},
    {"id": "e13", "from": "payments", "to": "r_hook", "kind": "webhook", "label": "payment succeeded", "data": "signed payment event", "evidence": ["acme/uploads/api/src/routes/payments.ts:9"]},
    {"id": "e14", "from": "r_hook", "to": "db", "kind": "data", "label": "sets the plan to paid", "data": "plan change", "evidence": ["acme/uploads/api/src/routes/payments.ts:21"]},
    {"id": "e15", "from": "db", "to": "r_upload", "kind": "data", "label": "reads the plan to enforce the free limit of 20 uploads", "data": "plan", "evidence": ["acme/uploads/api/src/routes/uploads.ts:15"]}
  ],
  "triggers": [
    {"id": "t_upload", "kind": "user_action", "label": "A customer uploads a photo", "setpoint": "upload-feedback",
     "steps": [
       {"edge": "e1", "narration": "The customer picks a photo and presses Upload."},
       {"edge": "e2", "narration": "The page posts the file to the API."},
       {"edge": "e3", "narration": "The API writes the original to object storage."},
       {"edge": "e4", "narration": "It records the upload as processing."},
       {"edge": "e5", "narration": "It queues a thumbnail job and returns at once."},
       {"edge": "e6", "narration": "When a slot is free, the worker takes the job."},
       {"edge": "e7", "narration": "The worker writes the thumbnail."},
       {"edge": "e8", "narration": "It marks the upload ready."},
       {"edge": "e10", "narration": "Meanwhile the page has been polling every three seconds."},
       {"edge": "e11", "narration": "The next poll reads ready."},
       {"edge": "e12", "narration": "The tile turns from Processing to Ready."}
     ],
     "outcome": "The thumbnail is stored and the upload reads ready.",
     "human_feedback": "The tile turns from Processing to Ready within one poll of the thumbnail being written."},
    {"id": "t_paid", "kind": "webhook", "label": "The payment provider reports a successful payment", "setpoint": "paid-sees-receipt",
     "steps": [
       {"edge": "e13", "narration": "The provider posts a signed payment event to the webhook."},
       {"edge": "e14", "narration": "The webhook verifies the signature and sets the plan to paid."}
     ],
     "outcome": "The account's plan reads paid and the free limit no longer applies.",
     "human_feedback": "none: no receipt and no confirmation screen; the plan badge changes only on the next page load."}
  ],
  "loops": [
    {"id": "L_drain", "type": "balancing", "nodes": ["q_thumbs", "worker"],
     "links": [
       {"from": "q_thumbs", "to": "worker", "sign": "+", "label": "more jobs waiting, more jobs taken, up to four at once"},
       {"from": "worker", "to": "q_thumbs", "sign": "-", "label": "more jobs taken, fewer waiting"}
     ],
     "story": "The worker drains the queue: the more jobs wait, the more it takes, up to four at once, so the queue shrinks back toward empty.",
     "stability": "stable",
     "why": "Measured over seven days: the depth peaks near 40 in the evening and is back to 0 by 02:00 every day, so arrivals stay below capacity.",
     "evidence": ["acme/uploads/worker/src/index.ts:12", "live 2026-10-01: queue_depth metric, 7 days: daily max 41, daily min 0"]},
    {"id": "L_retry", "type": "reinforcing", "nodes": ["q_thumbs", "worker"],
     "links": [
       {"from": "q_thumbs", "to": "worker", "sign": "+", "delay": true, "label": "more jobs waiting, more jobs that time out before they finish"},
       {"from": "worker", "to": "q_thumbs", "sign": "+", "label": "more timeouts, more jobs put back in the queue"}
     ],
     "story": "A retry storm in waiting: a slow day makes jobs time out, every timeout goes back in the queue, and a longer queue makes more jobs time out.",
     "stability": "watch",
     "why": "Unmeasured under load. The worker re-queues on timeout with no cap and no backoff; it has not run away only because the daily peak stays under capacity.",
     "evidence": ["acme/uploads/worker/src/index.ts:52"]}
  ],
  "data_uses": [
    {"data": "upload state (processing or ready)", "produced_by": ["r_upload", "worker"], "used_by": ["r_status"],
     "could_serve": ["an email when a large batch finishes", "a support view of uploads stuck in processing"]},
    {"data": "plan (free or paid)", "produced_by": ["r_hook"], "used_by": ["r_upload"],
     "could_serve": ["a receipt screen right after payment"]}
  ],
  "gaps": [
    {"kind": "missing", "setpoint": "paid-sees-receipt", "title": "A paying customer sees no confirmation",
     "detail": "The intent says a customer sees a receipt within a minute of paying. The webhook changes the plan and nothing tells the customer; the badge changes on their next page load.",
     "nodes": ["r_hook", "db", "customer"],
     "evidence": ["acme/uploads/api/src/routes/payments.ts:21", "live 2026-10-01: grep -rn receipt across acme/uploads: 0 hits outside tests"]},
    {"kind": "unintended", "title": "Originals are kept forever",
     "detail": "Nothing deletes an original after its thumbnail exists, and no stated intent asks to keep them, so storage grows with every upload.",
     "nodes": ["r_upload", "files"],
     "evidence": ["acme/uploads/api/src/storage.ts:3", "live 2026-10-01: bucket size 182 GB, up 9 GB in 30 days"]},
    {"kind": "unknown", "title": "A rejected webhook signature is silent",
     "detail": "A bad signature returns 400 and logs nothing, so a rotated signing secret would stop every plan upgrade with no alert. A control action with no feedback path; nobody has said whether an alert was meant.",
     "nodes": ["payments", "r_hook"],
     "evidence": ["acme/uploads/api/src/routes/payments.ts:12"]}
  ],
  "setpoints": [
    {"id": "upload-feedback", "about": "t_upload",
     "intent": "A customer who uploads a photo sees it marked Ready within ten seconds, without reloading the page.",
     "measure": "Trigger t_upload ends at e12, where the tile turns Ready. Live: the p95 time from upload to ready in the request log.",
     "source": "operator", "source_ref": "operator, 2026-09-28: \"people should see their photo is done before they wonder\"",
     "status": "confirmed", "holds": "yes",
     "why": "The path is complete on the map, and the request log on 2026-10-01 put the p95 from upload to ready at 6 seconds with the 3-second poll."},
    {"id": "paid-sees-receipt", "about": "t_paid",
     "intent": "When a customer pays, they see a receipt within a minute.",
     "measure": "Trigger t_paid ends at something the customer sees, so its human_feedback is not none.",
     "source": "operator", "source_ref": "operator, 2026-09-28: \"when a customer pays, they see a receipt within a minute\"",
     "status": "confirmed", "holds": "no",
     "why": "t_paid ends at the database: the plan changes and nothing tells the customer (gap: A paying customer sees no confirmation)."},
    {"id": "retry-capped", "about": "worker",
     "intent": "A thumbnail job that keeps timing out stops after three tries and is marked failed.",
     "measure": "The worker's re-enqueue (e9) carries a try count and a limit, so loop L_retry has a brake.",
     "source": "doc", "source_ref": "acme/uploads/docs/operations.md:14",
     "status": "proposed", "holds": "no",
     "why": "e9 puts a timed-out job back in the queue with no cap and no backoff (worker/src/index.ts:52), which is why L_retry is on watch."},
    {"id": "mobile-upload", "about": "web",
     "intent": "A customer can upload a photo from a phone browser.",
     "measure": "A person check: upload one photo from a phone. Or the share of uploads from mobile browsers in the request log.",
     "source": "operator", "source_ref": "operator, 2026-09-28: \"most people will do this from their phone\"",
     "status": "confirmed", "holds": "unknown",
     "why": "Nothing on the map shows a phone layout or a mobile upload, and nobody has tried one."}
  ]
}
```

## Changing the contract

The viewer, the checker and the skill read this one page. Add a field as optional, teach
the checker about it, and note it in `CHANGELOG.md` with the failure that needed it. Never
rename or repurpose a field: old maps stop drawing silently.
