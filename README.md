# codesys-unittest

xunit-style CODESYS unit tests for AI agents. One command, one short report.

Tests are ST function blocks using xunit vocabulary (suite / test / assert / fixture).
A host runner starts SoftMotion / Control Win, logs in via
[codesys-connect](https://github.com/zhouyongh/codesys-connect), polls results, and
emits text + JUnit XML.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ut.ps1 run -Project D:\repo\projects\App.project -UserFile user.txt
powershell -NoProfile -ExecutionPolicy Bypass -File ut.ps1 run -Mock    # wire-check without a PLC
```

| Command | What it does |
|---|---|
| `run` | ensure runtime -> connect -> run suites -> report |
| `run -Mock` | same pipeline, synthetic results |
| `ensure-runtime` / `stop-runtime` | SoftMotion / Control Win lifecycle |
| `report` | format last `results.json` |

Real PLC: pass `-Address <ip> -Port <port>` and skip the local runtime.

## Authoring

Copy `lib/GVL_Test.st`, `lib/FB_Assert.st`, `lib/PRG_Tests.st`, `lib/FB_Sample_Test.st`
into the PLC project. Each suite FB = one `Test_*` method per case; asserts write into
`GVL_Test`; the runner polls `GVL_Test.g_xDone`.

Full workflow (feature / regression / report shape): see `SKILL.md`.

## Requirements

- Windows, PowerShell 5.1+
- CODESYS 3.5.x with Scripting Engine
- [codesys-connect](https://github.com/zhouyongh/codesys-connect) (sibling folder, or `CODESYS_CONNECT_HOME`)
- Python 3 for `report.py` (`MIMO_PYTHON` or `python` on PATH)

Credentials live in codesys-connect's session file. Prefer `-UserFile`; this skill
never writes passwords into work files. `test_ops.py` reads login from env
(`CODESYS_UNITTEST_USER`/`CODESYS_UNITTEST_PASSWORD`) or the codesys-connect session.

Full interface: [SKILL.md](SKILL.md).
