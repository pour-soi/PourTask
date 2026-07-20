# PourTask

PourTask is a calm, local-first Windows task manager built with Python, PySide6, Qt Quick, and SQLite. Inbox, Today, Month, Completed, search, overdue, and due-soon screens are filtered views of one task database.

## Development

Requires Python 3.12 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\scripts\run_dev.ps1
```

Run tests with `.\scripts\test.ps1` and create the Windows executable with `.\scripts\build_windows.ps1`.

## Local data

PourTask keeps mutable user data outside the installation directory:

- Database: `%LOCALAPPDATA%\PourTask\data\pourtask.db`
- Backups: `%LOCALAPPDATA%\PourTask\backups\`
- Settings: `%LOCALAPPDATA%\PourTask\settings.json`
- Logs: `%LOCALAPPDATA%\PourTask\logs\`

Uninstalling the application does not silently delete this folder. Remove it manually only when you also want to delete tasks, settings, and backups.

## Privacy

PourTask has no account, cloud service, telemetry, or automatic log upload. Logs contain technical events rather than task titles or notes.

The desktop widget currently uses a safe standalone tool window. Windows desktop-layer attachment and Show Desktop behavior require further native validation before release.
