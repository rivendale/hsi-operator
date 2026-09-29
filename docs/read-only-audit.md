# An overnight read-only audit that someone reads

Written 2026-09-29 from one run, 2026-09-27 into 2026-09-28.

1. **Lanes.** Split by area (hosts, repositories, security, web, records). Every lane is read-only
   and has a written list of what it may not touch.
2. **A verify pass before anyone sees a finding.** A separate agent re-measures every serious
   finding from a different angle and checks it against the written record (decisions, known
   issues, open work). In one run of seven lanes over about 80 minutes, the verify pass tested the
   59 serious findings: 40 confirmed, 15 downgraded and 4 refuted. A worker's verdict is an
   assumption until it is re-derived
   ([honesty protocol](../skills/hsi-operator/references/honesty-protocol.md)).
3. **Severity comes from what the person has to choose**, not from how alarming a finding sounds.
   Red is a decision only they can make; amber is work the owner will do; grey is anything nobody
   can or would act on.
4. **Say what was not checked, grouped by why:** needs admin rights, would have been a write or
   spent money, out of bounds by rule, no instrument, depth limit.
5. **Disclose your own slips** in the report: an instrument that read something it should not
   have, a command that broke a house rule.
6. **Deliver it.** In that run, the main finding was that the existing nightly reports had no
   reader. What was missing was delivery, not more checks
   ([`every-output-needs-a-reader.md`](every-output-needs-a-reader.md)).
