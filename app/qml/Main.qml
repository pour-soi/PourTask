import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "theme"
import "components"

ApplicationWindow {
    id: root
    visible: !launchHidden
    width: 1300; height: 780
    minimumWidth: 1060; minimumHeight: 620
    title: "PourTask"
    color: Theme.bg
    property bool adding: false

    function openView(name) {
        appViewModel.setView(name)
        searchField.text = ""
    }
    function selectedMonthDate() {
        var parts = appViewModel.selectedMonth.split("-")
        return new Date(Number(parts[0]), Number(parts[1]) - 1, 1)
    }
    function pageTitle() {
        if (appViewModel.currentView === "month") return Qt.formatDate(selectedMonthDate(), "MMMM yyyy")
        if (appViewModel.currentView === "search") return "Search"
        return appViewModel.currentView.charAt(0).toUpperCase() + appViewModel.currentView.slice(1)
    }
    function pageSubtitle() {
        if (appViewModel.currentView === "inbox") return "Capture ideas before scheduling them."
        if (appViewModel.currentView === "today") return Qt.formatDate(new Date(), "dddd, MMMM d")
        if (appViewModel.currentView === "completed") return "Finished tasks remain available here."
        if (appViewModel.currentView === "search") return "Results from task titles and notes."
        if (appViewModel.currentView === "settings") return "Manage local application behavior and backups."
        return ""
    }
    function emptyTitle() {
        if (appViewModel.currentView === "inbox") return "Inbox is clear."
        if (appViewModel.currentView === "today") return "Nothing scheduled for today."
        if (appViewModel.currentView === "month") return "Nothing planned for this month."
        if (appViewModel.currentView === "completed") return "No completed tasks yet."
        return "No matching tasks."
    }
    function emptySubtitle() {
        return appViewModel.currentView === "inbox" ? "Capture a new task when something comes to mind." : ""
    }
    function submitQuickTask() {
        if (!quickTitle.text.trim()) return
        appViewModel.addTask(quickTitle.text)
        quickTitle.text = ""
        root.adding = false
    }

    onClosing: function(close) {
        if (settingsViewModel.minimizeToTray && trayAvailable) {
            close.accepted = false
            root.hide()
        }
    }

    Shortcut { sequence: "Ctrl+N"; onActivated: { root.adding = true; quickTitle.forceActiveFocus() } }
    Shortcut { sequence: "Ctrl+F"; onActivated: searchField.forceActiveFocus() }
    Shortcut { sequence: "Ctrl+Z"; onActivated: appViewModel.undo() }
    Shortcut { sequence: "Ctrl+1"; onActivated: root.openView("inbox") }
    Shortcut { sequence: "Ctrl+2"; onActivated: root.openView("today") }
    Shortcut { sequence: "Ctrl+3"; onActivated: root.openView("month") }
    Shortcut { sequence: "Ctrl+4"; onActivated: root.openView("completed") }
    Shortcut { sequence: "Escape"; onActivated: { if (appViewModel.detailOpen) appViewModel.closeDetail(); else root.adding = false } }

    RowLayout {
        anchors.fill: parent; spacing: 0

        Rectangle {
            Layout.preferredWidth: Theme.sidebarWidth; Layout.fillHeight: true
            color: Theme.sidebar
            ColumnLayout {
                anchors.fill: parent; anchors.leftMargin: Theme.s16; anchors.rightMargin: Theme.s16
                anchors.topMargin: Theme.s20; anchors.bottomMargin: Theme.s16; spacing: Theme.s8
                RowLayout {
                    Layout.fillWidth: true; Layout.bottomMargin: Theme.s24; spacing: Theme.s12
                    Rectangle {
                        Layout.preferredWidth: 36; Layout.preferredHeight: 36; radius: Theme.rControl
                        color: Theme.accentDim; border.color: Theme.border
                        PourIcon { anchors.centerIn: parent; width: 20; height: 20; name: "completed"; iconColor: Theme.accent }
                    }
                    ColumnLayout {
                        spacing: 0; Layout.fillWidth: true
                        Text { text: "PourTask"; color: Theme.text; font.pixelSize: 18; font.weight: Font.DemiBold }
                        Text { text: "LOCAL TASKS"; color: Theme.dim; font.pixelSize: 9; font.letterSpacing: 0.8 }
                    }
                }
                Repeater {
                    model: [
                        { key: "inbox", label: strings.inbox, icon: "inbox", tip: "Inbox · Ctrl+1" },
                        { key: "today", label: strings.today, icon: "today", tip: "Today · Ctrl+2" },
                        { key: "month", label: strings.month, icon: "month", tip: "Month · Ctrl+3" },
                        { key: "completed", label: strings.completed, icon: "completed", tip: "Completed · Ctrl+4" }
                    ]
                    delegate: NavItem {
                        required property var modelData
                        Layout.fillWidth: true; text: modelData.label; iconName: modelData.icon
                        selected: appViewModel.currentView === modelData.key
                        ToolTip.text: modelData.tip
                        onClicked: root.openView(modelData.key)
                    }
                }
                Item { Layout.fillHeight: true }
                Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: Theme.border; Layout.bottomMargin: Theme.s8 }
                NavItem {
                    Layout.fillWidth: true; text: strings.settings; iconName: "settings"
                    selected: appViewModel.currentView === "settings"
                    ToolTip.text: "Settings"
                    onClicked: root.openView("settings")
                }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true; Layout.fillHeight: true; spacing: 0
            Rectangle {
                Layout.fillWidth: true; Layout.preferredHeight: 96; color: Theme.bg
                RowLayout {
                    anchors.fill: parent; anchors.leftMargin: Theme.s24; anchors.rightMargin: Theme.s24; spacing: Theme.s16
                    ColumnLayout {
                        Layout.fillWidth: true; spacing: Theme.s4
                        Text { text: root.pageTitle(); color: Theme.text; font.pixelSize: Theme.pageTitle; font.weight: Font.DemiBold; elide: Text.ElideRight; Layout.fillWidth: true }
                        Text { text: root.pageSubtitle(); visible: text.length > 0; color: Theme.secondary; font.pixelSize: Theme.pageSubtitle; elide: Text.ElideRight; Layout.fillWidth: true }
                    }
                    SearchField {
                        id: searchField
                        Layout.preferredWidth: Math.min(360, Math.max(260, root.width * 0.24))
                        selectByMouse: true
                        onTextEdited: text.trim() ? appViewModel.setSearch(text) : appViewModel.clearSearch()
                    }
                    PrimaryButton { text: "New Task"; ToolTip.text: "New Task · Ctrl+N"; onClicked: { root.adding = true; quickTitle.forceActiveFocus() } }
                }
            }

            Rectangle {
                visible: root.adding; Layout.fillWidth: true; Layout.preferredHeight: 64
                color: Theme.accentDim; border.color: Theme.border
                RowLayout {
                    anchors.fill: parent; anchors.leftMargin: Theme.s24; anchors.rightMargin: Theme.s24; spacing: Theme.s8
                    PourTextField { id: quickTitle; Layout.fillWidth: true; placeholderText: "What needs to be done?"; onAccepted: root.submitQuickTask() }
                    PrimaryButton { text: "Add Task"; onClicked: root.submitQuickTask() }
                    PourButton { text: "Cancel"; onClicked: root.adding = false }
                }
            }

            RowLayout {
                Layout.fillWidth: true; Layout.fillHeight: true; spacing: 1
                Rectangle {
                    Layout.fillWidth: true; Layout.fillHeight: true; color: Theme.surface
                    ColumnLayout {
                        anchors.fill: parent; anchors.leftMargin: Theme.s24; anchors.rightMargin: Theme.s24
                        anchors.topMargin: Theme.s16; anchors.bottomMargin: Theme.s20; spacing: Theme.s12

                        RowLayout {
                            visible: appViewModel.currentView === "month"; Layout.fillWidth: true; spacing: Theme.s8
                            PourButton { text: "Previous"; onClicked: appViewModel.changeMonth(-1) }
                            Item { Layout.fillWidth: true }
                            PourButton { text: "Current Month"; onClicked: appViewModel.currentMonth() }
                            PourButton { text: "Next"; onClicked: appViewModel.changeMonth(1) }
                        }

                        ColumnLayout {
                            visible: appViewModel.currentView === "settings"; Layout.fillWidth: true; Layout.fillHeight: true; spacing: Theme.s16
                            Text { text: "APPLICATION"; color: Theme.dim; font.pixelSize: Theme.groupHeading; font.weight: Font.DemiBold }
                            CheckBox { text: "Launch at Startup"; checked: settingsViewModel.launchAtStartup; onToggled: settingsViewModel.setLaunchAtStartup(checked) }
                            CheckBox { text: "Close button minimizes to tray"; checked: settingsViewModel.minimizeToTray; onToggled: settingsViewModel.setMinimizeToTray(checked) }
                            CheckBox { text: "Enable Desktop Widget (safe window mode)"; checked: settingsViewModel.widgetEnabled; onToggled: settingsViewModel.setWidgetEnabled(checked) }
                            Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: Theme.border }
                            Text { text: "LOCAL BACKUPS"; color: Theme.dim; font.pixelSize: Theme.groupHeading; font.weight: Font.DemiBold }
                            RowLayout { spacing: Theme.s8
                                PrimaryButton { text: "Export Backup"; iconName: "completed"; onClicked: appViewModel.exportBackup() }
                                PourButton { text: "Replace Current Data..."; onClicked: appViewModel.importBackup() }
                            }
                            Text { text: "Replacement validates the imported database and creates a safety backup first."; color: Theme.secondary; font.pixelSize: Theme.bodyText; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                            Item { Layout.fillHeight: true }
                        }

                        ListView {
                            id: taskList
                            visible: appViewModel.currentView !== "settings"
                            Layout.fillWidth: true; Layout.fillHeight: true
                            model: appViewModel.tasks; spacing: Theme.s8; clip: true
                            delegate: TaskRow {
                                selected: appViewModel.selectedTask.id === taskId
                                onToggled: value => appViewModel.setCompleted(taskId, value)
                                onOpened: appViewModel.openDetail(taskId)
                            }
                            EmptyState {
                                anchors.centerIn: parent; visible: taskList.count === 0
                                title: root.emptyTitle(); subtitle: root.emptySubtitle()
                            }
                        }
                    }
                }

                Rectangle { Layout.preferredWidth: 1; Layout.fillHeight: true; color: Theme.border }
                DetailsPanel {
                    Layout.preferredWidth: root.width >= 1500 ? 390 : (root.width >= 1250 ? 360 : 320)
                    Layout.fillHeight: true
                    task: appViewModel.selectedTask
                }
            }
        }
    }

    Rectangle {
        visible: appViewModel.message !== ""
        anchors.horizontalCenter: parent.horizontalCenter; anchors.bottom: parent.bottom; anchors.bottomMargin: Theme.s20
        width: toastRow.implicitWidth + Theme.s24; height: 44; radius: Theme.rControl
        color: Theme.accentDim; border.color: Theme.borderStrong; z: 20
        RowLayout {
            id: toastRow; anchors.centerIn: parent; spacing: Theme.s8
            Text { text: appViewModel.message.replace(" — Undo", ""); color: Theme.text; font.pixelSize: Theme.bodyText }
            Button {
                id: undoButton
                visible: appViewModel.message.indexOf("Undo") >= 0; text: strings.undo
                onClicked: appViewModel.undo()
                contentItem: Text { text: undoButton.text; color: Theme.accentHover; font.pixelSize: Theme.bodyText; font.weight: Font.DemiBold }
                background: Item {}
            }
        }
    }
}
