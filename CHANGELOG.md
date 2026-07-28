# Changelog

## v1.2.0-beta.1 - 2026-07-27

Validation build for external testing of the new window layout and desktop widget behavior before the next stable release.

- Added a responsive three-column layout with draggable, persisted splitters.
- Made the main window freely resizable while retaining normal maximize, restore, minimize, and close behavior.
- Added a collapsible task editor that automatically reopens for New Task and task editing.
- Redesigned the desktop widget for a much smaller default footprint.
- Added native widget movement and edge/corner resizing.
- Improved compact mode and restoration of the previous expanded size.
- Added main-window, splitter, editor, and widget geometry/state persistence.
- Added multi-monitor work-area recovery for saved window positions.
- Synchronized Today tasks between the widget and main window without new polling.
- Made headers, date controls, and editor layouts responsive at narrower widths.

## v1.1.0 - 2026-07-26

- Replaced quick-add with a complete New Task editor that does not create a database record before Save Task.
- Added US `MM/DD/YYYY` date display, flexible US date input, and field-level validation.
- Added reusable Schedule Date and Due Date calendar pickers.
- Added `MM/YYYY` Assigned Month input and a reusable month picker.
- Added automatic task selection and view following after task creation or date changes.
- Preserved the existing database schema, ISO storage, user data location, and v1.0.0 database compatibility.

## v1.0.0 - 2026-07-25

- First public release of PourTask.
- Added a responsive three-column Pour-family interface with a permanent task details panel.
- Added Inbox, Today, Month, Completed, Search, and Settings views over one task database.
- Added local SQLite storage for tasks, notes, dates, completion state, and application settings.
- Added task creation, editing, completion, restoration, search, undo, and validated local backups.
- Added Windows system tray, optional launch at startup, desktop widget support, and saved window geometry.
