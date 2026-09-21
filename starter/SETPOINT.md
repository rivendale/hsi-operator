# Setpoint — what done means for the work in flight

Fill this in **before** building, not at the end. If it is hard to state, the answer is
usually a **smaller** done rather than more planning.

**Classify first, and say so out loud:** a spike (the output is an answer, not something
you keep), something bounded (a change to what already exists and can be read), or
something architectural (new, or it changes an interface others depend on). Ties take the
heavier path, and complexity found mid-task upgrades it.

| | |
|---|---|
| **id** | `short-slug`, cited by the work that follows. No id, no start. |
| **1. Who uses this, and when?** | One person and one moment beats "the team". If the honest answer is "nobody yet", say so now. |
| **2. What does it let them do** that they cannot do today? | |
| **3. What would make them say "that is not what I wanted"?** | People describe wrongness far more precisely than rightness. |
| **4. Done when** | ONE checkable sentence, external to the model: a command that exits, a number that moves, a person who does something you can watch. "It looks good" is not checkable. |
| **5. Explicitly out of scope** | This is what stops the work growing quietly. |
| **Re-ask if** | The condition that would change this answer. A condition, never a timer. |
| **Asked as** | The request in their own words, before anyone tidied it. |

**An approval covers the stage you actually showed.** Approving the idea is not approving
an artifact that does not exist yet.

`hsi done setpoint.json` in this repo does the same thing as a file a machine can check.
