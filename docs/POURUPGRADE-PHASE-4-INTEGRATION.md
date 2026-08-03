# PourUpgrade Phase 4 integration

This feature branch is a test-only PourUpgrade integration. It does not enable update checks for stable PourTask users.

## Verified architecture and storage

PourTask is a Python/PySide6 Qt Quick application packaged by PyInstaller. SQLite writes are transactional and occur through the repository layer. Settings are atomically replaced JSON. Stable data remains under `%LOCALAPPDATA%\PourTask`: schema location `database` protects `data\`, `local-data` protects `backups\`, and `settings` protects `settings.json`. `logs\` is diagnostic and disposable. There is no separate helper process.

The stable Inno Setup installer is per-user (`PrivilegesRequired=lowest`) at `%LOCALAPPDATA%\Programs\PourTask`. It has stable AppId `{B9ED315F-7DE7-43FA-8B85-7B1FF1ED64A5}` and must not be used for Phase 4. `PourTask.Phase4.iss` provides a separate test AppId, install root, display name, marker, shortcut, and uninstall identity. It does not write stable startup settings.

## Test identity and protocol

The test app ID is `com.pour.pourtask.phase4`; protocol identity is `pourtask-phase4-v1`; repository/channel are pinned to private `pour-soi/PourUpgrade-TestRelease` and `phase4-test`. The fixed `--pourupgrade-phase4-test` launch mode selects `%LOCALAPPDATA%\PourTask-Phase4` and `%LOCALAPPDATA%\PourUpgrade\registrations-test`; automated harnesses may override both with explicit temporary roots. Development/portable runs without the Phase 4 installed marker do not register.

The Settings action launches only the fixed local PourUpgrade executable with `--focus-app com.pour.pourtask.phase4`. It never accepts a URL, repository, executable path, or installer command from the user or manifest.

The same-user local pipe uses a 16 KiB length-prefixed JSON message, exact fields, exact app/protocol identity, bounded lifetime, nonce validation, and single-use request IDs. Open edits return `requires-user-action`; persistence failure returns `failed`; only successful persistence returns `ready`, followed by graceful Qt exit. Foreground uses normal launch, tray uses fixed `--pourupgrade-tray`, and none does not launch. Health reports only app/version/mode/restoration/process/attempt/request identity.

## Boundary and limitations

PourUpgrade owns GitHub, selection, verification, cache, planning, installation, restart, health validation, history, logs, and recovery. Stage 4.1 is limited to isolated test roots and packaged/local harness validation. Stage 4.2 requires a separately built prerelease executable with independently verifiable version metadata before running the isolated test installer. Stage 4.3 and any existing stable installation remain forbidden without a separate decision.
