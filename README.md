# PourTask

**Current validation version: v1.2.0-beta.3**

PourTask is a polished, local-first desktop task manager for Windows. It uses a calm Pour-family interface and keeps Inbox, Today, Month, Completed, Search, and Settings as filtered views of one local task database.

## What PourTask supports

- Task creation, editing, completion, restoration, deletion, and short-session undo
- A complete New Task editor with Notes, scheduled dates, due dates, and assigned months before saving
- US date display, flexible US date input, date calendars, and an assigned-month picker
- Case-insensitive search across task titles and notes
- Local backup export and validated replacement import
- Optional Windows system tray, launch at startup, desktop widget, and saved window position
- Keyboard shortcuts for navigation, search, task creation, saving, canceling, and undo

PourTask does not require an account and does not provide cloud synchronization, collaboration, reminders, recurring tasks, attachments, priorities, tags, or AI planning.

## Run the Windows release

1. Download `PourTask-v1.2.0-beta.3-Windows-Setup.exe` or `PourTask-v1.2.0-beta.3-Windows.zip` from the validation pre-release.
2. Run the installer, or extract the complete portable ZIP to a writable folder.
3. For the portable build, run `PourTask.exe` from the extracted folder.

Keep the complete extracted directory together. Do not move only the executable away from its `_internal` runtime directory.

Windows may show an unknown-publisher warning because the first release is not code-signed.

## Local data

PourTask stores mutable data outside the application directory:

- Database: `%LOCALAPPDATA%\PourTask\data\pourtask.db`
- Backups: `%LOCALAPPDATA%\PourTask\backups\`
- Settings: `%LOCALAPPDATA%\PourTask\settings.json`
- Logs: `%LOCALAPPDATA%\PourTask\logs\`

Updating, moving, or deleting the portable application directory does not silently remove this data. Remove the local data folder manually only when you also want to delete tasks, settings, and backups.

## Run from source

Python 3.12 or newer is required.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\scripts\run_dev.ps1
```

## Run tests

```powershell
.\scripts\test.ps1
```

The complete release verification also runs Python compilation, QML loading, QML lint, a PyInstaller Windows build, and an isolated portable launch check.

## Build the Windows portable package

```powershell
.\scripts\build_windows.ps1
```

The current development build creates:

- `release\PourTask-v1.2.0-beta.3-Windows\`
- `release\PourTask-v1.2.0-beta.3-Windows.zip`
- `release\PourTask-v1.2.0-beta.3-Windows.zip.sha256`
- `release\PourTask-v1.2.0-beta.3-Windows-Setup.exe`
- `release\PourTask-v1.2.0-beta.3-Windows-Setup.exe.sha256`

## Privacy

PourTask has no telemetry or automatic log upload. Logs contain technical diagnostic information rather than complete task titles or Notes.
