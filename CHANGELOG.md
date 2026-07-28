# Changelog

## v1.2.0 - 2026-07-28

PourTask 1.2.0 is the stable culmination of the 1.2 validation cycle, focused on responsive desktop layouts, a practical Today widget, stronger Windows integration, and a cohesive commercial-quality interface.

### Desktop

- Added a responsive three-column layout with user-adjustable, persisted splitters and a smaller 720 x 520 minimum window size.
- Reworked Task Details into a genuinely responsive editor that reflows fields and actions as its panel narrows while preserving drafts and vertical access.
- Improved Settings organization, information density, typography, spacing, interaction feedback, and animation consistency through unified design tokens.
- Added a distinctive PourTask application icon across the runtime, taskbar, Alt+Tab, tray, executable, installer, shortcuts, and installed-app listing.

### Desktop Widget

- Redesigned the widget as a compact desktop card with real-time Today task rows, Compact and Expanded modes, optional delayed hover expansion, and inline Quick Add.
- Added Show Widget and Reset Widget Position controls while retaining native movement, resizing, task completion, and synchronized task updates.
- Refined widget spacing, hierarchy, empty states, controls, and transitions for a denser, more glanceable experience.

### Windows

- Added an opt-in per-user startup setting with tray-minimized launch, single-instance protection, and uninstall cleanup.
- Improved tray behavior, geometry persistence, multi-monitor recovery, and high-DPI resilience for the main window and desktop widget.

### Product Polish

- Completed a broad responsive-layout, consistency, accessibility, and Windows desktop UX pass without changing task storage, task semantics, or user-data locations.

## v1.2.0-beta.3 - 2026-07-28

Third external validation build focused on reliable desktop-widget rendering, optional hover expansion, denser interface details, and complete PourTask icon integration.

- Fixed the desktop widget blank-body rendering issue so actual Today task rows display at the default installed widget size.
- Anchored the widget header, task list, and Quick Add regions with a 26-pixel header, 30-pixel task rows, and a 30-pixel Quick Add area.
- Added optional compact-widget hover expansion with a 375 ms expand delay and a 650 ms collapse delay.
- Prevented hover collapse during Quick Add focus, context-menu use, control interaction, task completion, native movement, and resizing.
- Kept temporary hover expansion from overwriting the saved Compact state.
- Replaced wordy widget header actions with compact, accessible icon-only controls.
- Increased the Notes editor height and refined Save and Delete onto a clearer shared action row.
- Shortened the Search field, compacted main-window task rows, enlarged sidebar icons, and strengthened the Task Details hierarchy.
- Added a new branded PourTask application icon with consistent runtime, taskbar, Alt+Tab, tray, PyInstaller, installer, shortcut, and Add/Remove Programs integration.
- Preserved the Beta 2 Windows startup feature, including HKCU registration, tray-minimized startup, single-instance handling, portable-build restrictions, and uninstall cleanup.

## v1.2.0-beta.2 - 2026-07-27

External validation build focused on responsive window layout, practical Today-widget use, and user-controlled Windows startup.

- Rebalanced the default three-column layout to favor the task editor while preserving draggable, saved splitters.
- Reduced the main-window minimum size to 720 x 520 and automatically collapse the editor when space is insufficient without discarding unfinished edits.
- Made narrow editor fields and actions remain reachable through responsive layout and vertical scrolling.
- Made the desktop widget render actual Today task titles with compact 30-pixel rows, immediate completion, and shared-model synchronization.
- Reduced the widget's default and minimum expanded heights while retaining compact mode, native movement and resizing, geometry persistence, and multi-monitor recovery.
- Added an installed-build-only, per-user Windows startup option backed by the HKCU Run registry key.
- Made startup launches remain minimized to the system tray and added single-instance coordination for normal and startup invocations.
- Added installer cleanup for PourTask's own startup registration.

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
