# Live smoke test (L5)

The default suite (`python -m unittest discover -s tests`) runs on a machine
without CODESYS: it covers parsing, reporting, the reset sequence, the real
`ut.ps1` launch path with a fake runner, and `run_tests()` with a fake online
application. It cannot prove that the Scripting Engine calls work against a
real runtime.

This live test is the missing half. It is **skipped by default** and runs only
when the environment says a prepared project exists.

## Prerequisites

- Windows, CODESYS 3.5.x, SoftMotion Win / Control Win (or a real PLC).
- A project that already contains the protocol POUs and the suites, already
  imported and downloaded. The conveyor-loop or sample-app sample works.
- Credentials (a local `user.txt`, not committed).
- Local: the runtime is up (`ut.ps1 ensure-runtime`). Remote: the application
  is RUN; the test does not start a remote PLC.

## Run

```powershell
$env:CODESYS_UNITTEST_LIVE = "1"
$env:CODESYS_UNITTEST_PROJECT = "D:\repo\projects\App.project"
$env:CODESYS_UNITTEST_USERFILE = "D:\repo\user.txt"
# optional:
$env:CODESYS_UNITTEST_ADDRESS = "192.168.1.10"
$env:CODESYS_UNITTEST_PORT = "11740"
$env:CODESYS_UNITTEST_EXPECT_CASES = "19"

python -m unittest discover -s tests -p "test_live_smoke.py" -v
```

It runs `ut.ps1 run` **twice**, without downloading in between, and asserts:

- exit code 0 both times;
- `report.txt` has `N cases, 0 failed`;
- `N` is greater than 0 and identical between the two runs;
- optionally, `N` equals `CODESYS_UNITTEST_EXPECT_CASES`.

The two-run check is the point: it exercises the reset hold, the case-count
guard and the idempotent suites together.

## Rounds the script cannot do

These need a human at the keyboard (or a later automation layer):

1. **Red** – break one rule in the project, import + download, run:
   exit 1, exactly the expected case fails, `junit.xml` carries a `<failure>`.
2. **Restore** – put the rule back, import + download, run: exit 0.
3. **Structural failure** – set `g_uiSuitesTotal` one too high, import +
   download, run: the runner reports a `g_xDone` timeout with
   `suitesDone=4/5`, not a green run.
4. **Real PLC** – run with `-Address` / `-Port`; confirm the runner only probes
   the port and does not start the application. Add `-StartIfStopped` only when
   that is intended.

The conveyor-loop walk-through has the exact commands and expected outputs:
[`examples/conveyor-loop/docs/CLOSED_LOOP.md`](../examples/conveyor-loop/docs/CLOSED_LOOP.md).

## CI

The GitHub workflow in `.github/workflows/self-tests.yml` runs the default
suite on `windows-latest` (L0-L4). L5 needs a self-hosted Windows runner with
CODESYS installed and a prepared project:

- set `CODESYS_UNITTEST_LIVE=1`, `CODESYS_UNITTEST_PROJECT`,
  `CODESYS_UNITTEST_USERFILE` as runner environment/secrets;
- run `python -m unittest discover -s tests -p "test_live_smoke.py" -v` as a separate job;
- never commit `user.txt` or a `.project` with credentials.

## Test hooks used by L3/L4

`ut.ps1` accepts a few environment overrides that exist only for the test
suite. They are not part of the user-facing interface:

| Variable | Purpose |
|---|---|
| `CODESYS_UNITTEST_EXE` / `_PROFILE` | skip install resolution, point at a fake runner |
| `CODESYS_UNITTEST_OPS` | override the ops script passed to the runner |
| `CODESYS_UNITTEST_WATCHDOG_SEC` | shorten the process-tree watchdog |

These variables change which program runs. Treat them like
`CODESYS_CONNECT_EXE`: only set them in a local, trusted test session, never
in a shared or untrusted environment.

`test_ops.py` can be imported by the host tests; it only runs when
`CODESYS_UNITTEST_TARGET` is set (the CLI always sets it). A leftover
`target.txt` next to the script does not trigger a run.
