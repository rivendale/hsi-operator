# Fixtures for the `update` skill

Independent test fixtures for `skills/update/bin/update-report`. They were written from the skill's spec and its
failure list alone, by someone other than the person who built the script, before the script existed, so the
builder never grades its own work.

```sh
python3 evals/update/run.py                 # every fixture
python3 evals/update/run.py --only 07,12    # fixtures whose id starts with 07 or 12
python3 evals/update/run.py --tags spec     # only the fixtures the spec states literally
python3 evals/update/run.py --list          # id, failure-list item, tag, what it checks
python3 evals/update/run.py --bin PATH      # test another copy of the script
```

Exit 0 when every selected fixture passes, 1 when one fails, 3 when the script is missing or not executable (so
"no script yet" is never read as "all passed").

## What a fixture is

A directory under `fixtures/` with one `case.json`: the **input** (files, a git history, a fake `gh` or none, the
command-line arguments) and what the report must do (**exit code**, lines it must and must not print, section
contents, order). The runner builds a fresh directory per fixture, runs the script there with a clean environment
and checks:

- `HOME` is empty and git reads no user or system config; git may not look above the directory; `TZ=UTC`.
- `PATH` holds only a directory of symlinks to common tools, never `gh`, plus a fake `gh` when the fixture asks
  for one (`ok-empty`, `unauth`, `error`) that logs every call. A fixture cannot reach the real network or the real `gh`.
- Dates are written as `{{today-4}}`, `{{now-72h}}` and `{{NOW}}` and filled in at run time, and the script is given
  `--now {{NOW}}`, so a fixture never goes stale.

## Tags

| tag | meaning | if it fails |
|---|---|---|
| `spec` | the spec states the literal line or the exit code | a bug in the script |
| `principle` | the spec states a rule (a failure to read is never "nothing"; never crash; never write) and this checks it | a bug in the script |
| `assumption` | the spec is silent on a format and the fixture assumed one | settle the spec, then change the fixture or the script |
| `extra` | a case the failure list missed (a stale input, an omission, a corrupt file) | a bug in the script |

## Coverage

Every item on the spec's failure list (1 to 15) has at least one fixture, and most have a control that must NOT
trigger the flag (for example, `04c` checks that a recent objective is not `STALLED`). Cases the list missed:
Windows line endings, an empty `done-when:`, an unknown or missing `status:`, a dropped objective, an unreadable
file, a directory in place of the file, bytes that are not UTF-8, bidi and zero-width characters, hostile text in a
commit subject, a 3000-objective file with a 300 KB line, a run that must write nothing and call `gh` with read
verbs only, two runs that must print the same page, and a future-dated `updated:`.

## Proving the fixtures can fail

A fixture that cannot fail proves nothing. The script was copied and broken one behaviour at a time, 73 ways (a flag
renamed, a threshold ignored, a failure swallowed or reported as "none", the exit code dropped or reordered, escapes
left in, a window or a cap removed, a write added, a gh write verb added, and so on); the full set of fixtures was run
against each copy. 67 of the 73 breaks are caught. The 6 that survive are listed here with the reason, so none is silent:

| break | why no fixture catches it |
|---|---|
| invalid UTF-8 no longer caught | equivalent: `UnicodeError` is a subclass of `ValueError`, behaviour unchanged |
| `gh auth status` not checked | equivalent against real gh: an unauthenticated `gh pr list` fails by itself; the fake gh models that |
| unknown-status objectives hide their needs | equivalent: the script already shows needs only for active and blocked objectives |
| CRLF not handled by the splitter | equivalent: control characters are stripped afterwards |
| input-size cap removed | the spec sets no input bound; unspecified, so no fixture asserts one |
| stall boundary `>=` against `>` | the spec says "older than the stall threshold" without fixing whether day N counts; unspecified |
