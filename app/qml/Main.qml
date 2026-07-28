import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "theme"
import "components"

ApplicationWindow {
    id: root
    objectName: "mainWindow"
    visible: !launchHidden
    width: 960
    height: 700
    minimumWidth: 720
    minimumHeight: 520
    title: "PourTask"
    color: Theme.bg

    property bool editorCollapsed: settingsViewModel.editorCollapsed
    property real lastSidebarWidth: settingsViewModel.mainSidebarWidth > 0
                                    ? settingsViewModel.mainSidebarWidth : width * 0.16
    property real lastTaskWidth: settingsViewModel.mainTaskWidth > 0
                                 ? settingsViewModel.mainTaskWidth
                                 : (settingsViewModel.mainEditorWidth > 0
                                    ? Math.max(180, width - lastSidebarWidth
                                               - settingsViewModel.mainEditorWidth - 12)
                                    : width * 0.34)
    property real lastEditorWidth: settingsViewModel.mainEditorWidth > 0
                                   ? settingsViewModel.mainEditorWidth : width * 0.50
    property bool layoutReady: false
    readonly property bool editorHasRoom: contentSplitView.width >= 520
    readonly property bool searchRelevant: appViewModel.currentView !== "settings"

    Component.onCompleted: {
        layoutReady = true
        automaticCollapseTimer.restart()
    }

    function setEditorCollapsed(collapsed) {
        if (collapsed === editorCollapsed)
            return
        if (collapsed && detailsPanel.visible) {
            lastEditorWidth = detailsPanel.width
            persistSplitters()
        }
        if (!collapsed && !editorHasRoom)
            return
        if (!collapsed && lastEditorWidth < 260)
            lastEditorWidth = Math.max(260, width * 0.50)
        settingsViewModel.setEditorCollapsed(collapsed)
    }
    function persistSplitters() {
        lastSidebarWidth = sidebarPanel.width
        lastTaskWidth = taskListPanel.width
        if (detailsPanel.visible)
            lastEditorWidth = detailsPanel.width
        settingsViewModel.setMainSplitters(
                    sidebarPanel.width, taskListPanel.width, lastEditorWidth)
    }
    function openView(name) {
        appViewModel.clearMessage()
        appViewModel.setView(name)
        searchField.text = ""
    }
    function startNewTask() {
        if (appViewModel.currentView === "settings")
            appViewModel.setView("inbox")
        if (editorCollapsed && editorHasRoom)
            setEditorCollapsed(false)
        appViewModel.beginNewTask()
    }
    function collapseEditorIfNeeded(availableWidth) {
        if (layoutReady && availableWidth < 520 && !editorCollapsed)
            setEditorCollapsed(true)
    }
    function selectedMonthDate() {
        var parts = appViewModel.selectedMonth.split("-")
        return new Date(Number(parts[0]), Number(parts[1]) - 1, 1)
    }
    function pageTitle() {
        if (appViewModel.currentView === "month")
            return Qt.formatDate(selectedMonthDate(), "MMMM yyyy")
        if (appViewModel.currentView === "search")
            return "Search"
        return appViewModel.currentView.charAt(0).toUpperCase()
                + appViewModel.currentView.slice(1)
    }
    function pageSubtitle() {
        if (appViewModel.currentView === "inbox")
            return "Capture ideas before scheduling them."
        if (appViewModel.currentView === "today")
            return Qt.formatDate(new Date(), "dddd, MMMM d")
        if (appViewModel.currentView === "completed")
            return "Finished tasks remain available here."
        if (appViewModel.currentView === "search")
            return "Results from task titles and notes."
        if (appViewModel.currentView === "settings")
            return "Manage local application behavior and backups."
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
        return appViewModel.currentView === "inbox"
                ? "Capture a new task when something comes to mind." : ""
    }
    function toastText() {
        return appViewModel.message.replace("鈥?", "").replace("Undo", "").trim()
    }

    onClosing: function(close) {
        if (settingsViewModel.minimizeToTray && trayAvailable) {
            close.accepted = false
            root.hide()
        }
    }

    Connections {
        target: appViewModel
        function onDetailChanged() {
            if ((appViewModel.isCreating || appViewModel.detailOpen)
                    && root.editorCollapsed)
                root.setEditorCollapsed(false)
        }
        function onMessageChanged() {
            if (appViewModel.message === "") {
                toastTimer.stop()
                return
            }
            toastTimer.interval = appViewModel.message.indexOf("Undo") >= 0 ? 6500 : 3000
            toastTimer.restart()
        }
    }

    Timer {
        id: splitterSaveTimer
        interval: 300
        onTriggered: root.persistSplitters()
    }
    Timer {
        id: automaticCollapseTimer
        interval: 50
        onTriggered: root.collapseEditorIfNeeded(contentSplitView.width)
    }
    Timer {
        id: toastTimer
        interval: 3000
        onTriggered: appViewModel.clearMessage()
    }

    Shortcut { sequence: "Ctrl+N"; onActivated: root.startNewTask() }
    Shortcut {
        sequence: "Ctrl+F"
        enabled: root.searchRelevant
        onActivated: searchField.forceActiveFocus()
    }
    Shortcut { sequence: "Ctrl+Z"; onActivated: appViewModel.undo() }
    Shortcut { sequence: "Ctrl+1"; onActivated: root.openView("inbox") }
    Shortcut { sequence: "Ctrl+2"; onActivated: root.openView("today") }
    Shortcut { sequence: "Ctrl+3"; onActivated: root.openView("month") }
    Shortcut { sequence: "Ctrl+4"; onActivated: root.openView("completed") }
    Shortcut {
        sequence: "Escape"
        enabled: !detailsPanel.popupOpen
        onActivated: {
            if (appViewModel.isCreating) appViewModel.cancelNewTask()
            else if (appViewModel.detailOpen) appViewModel.closeDetail()
        }
    }

    SplitView {
        id: mainSplitView
        objectName: "mainSplitView"
        anchors.fill: parent
        orientation: Qt.Horizontal
        onResizingChanged: if (!resizing) splitterSaveTimer.restart()
        handle: Rectangle {
            implicitWidth: 6
            color: SplitHandle.pressed || SplitHandle.hovered
                   ? Theme.borderStrong : Theme.border
        }

        Rectangle {
            id: sidebarPanel
            objectName: "sidebarPanel"
            SplitView.minimumWidth: 130
            SplitView.preferredWidth: root.lastSidebarWidth
            SplitView.maximumWidth: 320
            color: Theme.sidebar

            ColumnLayout {
                anchors.fill: parent
                anchors.leftMargin: Theme.s16
                anchors.rightMargin: Theme.s16
                anchors.topMargin: Theme.s20
                anchors.bottomMargin: Theme.s16
                spacing: Theme.s8

                RowLayout {
                    Layout.fillWidth: true
                    Layout.bottomMargin: Theme.s24
                    spacing: Theme.s12
                    Rectangle {
                        Layout.preferredWidth: 36
                        Layout.preferredHeight: 36
                        radius: Theme.rControl
                        color: Theme.accentDim
                        border.color: Theme.border
                        PourIcon {
                            anchors.centerIn: parent
                            width: 20
                            height: 20
                            name: "completed"
                            iconColor: Theme.accent
                        }
                    }
                    ColumnLayout {
                        spacing: 0
                        Layout.fillWidth: true
                        Text {
                            text: "PourTask"
                            color: Theme.text
                            font.pixelSize: 18
                            font.weight: Font.DemiBold
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                        Text {
                            text: "LOCAL TASKS"
                            color: Theme.dim
                            font.pixelSize: 9
                            font.letterSpacing: 0.8
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
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
                        Layout.fillWidth: true
                        text: modelData.label
                        iconName: modelData.icon
                        selected: appViewModel.currentView === modelData.key
                        ToolTip.text: modelData.tip
                        onClicked: root.openView(modelData.key)
                    }
                }
                Item { Layout.fillHeight: true }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    color: Theme.border
                    Layout.bottomMargin: Theme.s8
                }
                NavItem {
                    Layout.fillWidth: true
                    text: strings.settings
                    iconName: "settings"
                    selected: appViewModel.currentView === "settings"
                    ToolTip.text: "Settings"
                    onClicked: root.openView("settings")
                }
            }
        }

        ColumnLayout {
            id: mainContent
            SplitView.fillWidth: true
            SplitView.minimumWidth: 360
            spacing: 0

            Rectangle {
                id: header
                Layout.fillWidth: true
                Layout.preferredHeight: narrow ? 126 : 96
                color: Theme.bg
                readonly property bool narrow: width < 640

                GridLayout {
                    anchors.fill: parent
                    anchors.leftMargin: header.narrow ? Theme.s16 : Theme.s24
                    anchors.rightMargin: header.narrow ? Theme.s16 : Theme.s24
                    anchors.topMargin: Theme.s12
                    anchors.bottomMargin: Theme.s12
                    columns: header.narrow ? 2 : 3
                    columnSpacing: Theme.s16
                    rowSpacing: Theme.s8

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.columnSpan: header.narrow ? 2 : 1
                        spacing: Theme.s4
                        Text {
                            text: root.pageTitle()
                            color: Theme.text
                            font.pixelSize: Theme.pageTitle
                            font.weight: Font.DemiBold
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                        Text {
                            text: root.pageSubtitle()
                            visible: text.length > 0
                            color: Theme.secondary
                            font.pixelSize: Theme.pageSubtitle
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                    }
                    SearchField {
                        id: searchField
                        objectName: "taskSearchField"
                        visible: root.searchRelevant
                        Layout.fillWidth: true
                        Layout.minimumWidth: header.narrow ? 120 : 180
                        Layout.preferredWidth: 300
                        Layout.maximumWidth: 360
                        selectByMouse: true
                        onTextEdited: text.trim()
                                      ? appViewModel.setSearch(text)
                                      : appViewModel.clearSearch()
                    }
                    PrimaryButton {
                        objectName: "newTaskButton"
                        text: "New Task"
                        ToolTip.text: "New Task · Ctrl+N"
                        Layout.alignment: Qt.AlignRight
                        onClicked: root.startNewTask()
                    }
                }
            }

            SplitView {
                id: contentSplitView
                objectName: "contentSplitView"
                Layout.fillWidth: true
                Layout.fillHeight: true
                orientation: Qt.Horizontal
                onWidthChanged: automaticCollapseTimer.restart()
                onResizingChanged: if (!resizing) splitterSaveTimer.restart()
                handle: Rectangle {
                    implicitWidth: 6
                    color: SplitHandle.pressed || SplitHandle.hovered
                           ? Theme.borderStrong : Theme.border
                }

                Rectangle {
                    id: taskListPanel
                    objectName: "taskListPanel"
                    SplitView.fillWidth: root.editorCollapsed
                                         || appViewModel.currentView === "settings"
                    SplitView.minimumWidth: 180
                    SplitView.preferredWidth: root.lastTaskWidth
                    color: Theme.surface

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.leftMargin: Theme.s24
                        anchors.rightMargin: Theme.s24
                        anchors.topMargin: Theme.s16
                        anchors.bottomMargin: Theme.s20
                        spacing: Theme.s12

                        RowLayout {
                            visible: appViewModel.currentView === "month"
                            Layout.fillWidth: true
                            spacing: Theme.s8
                            PourButton { text: "Previous"; onClicked: appViewModel.changeMonth(-1) }
                            Item { Layout.fillWidth: true }
                            PourButton { text: "Current Month"; onClicked: appViewModel.currentMonth() }
                            PourButton { text: "Next"; onClicked: appViewModel.changeMonth(1) }
                        }

                        ColumnLayout {
                            visible: appViewModel.currentView === "settings"
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            spacing: Theme.s16
                            Text {
                                text: "APPLICATION"
                                color: Theme.dim
                                font.pixelSize: Theme.groupHeading
                                font.weight: Font.DemiBold
                            }
                            CheckBox {
                                objectName: "startupToggle"
                                text: "Run PourTask at Windows startup"
                                checked: settingsViewModel.launchAtStartup
                                enabled: settingsViewModel.startupSupported
                                onClicked: settingsViewModel.setLaunchAtStartup(checked)
                                ToolTip.visible: hovered && !enabled
                                ToolTip.text: settingsViewModel.startupUnavailableReason
                            }
                            Text {
                                visible: settingsViewModel.startupError !== ""
                                         || !settingsViewModel.startupSupported
                                text: settingsViewModel.startupError !== ""
                                      ? settingsViewModel.startupError
                                      : settingsViewModel.startupUnavailableReason
                                color: settingsViewModel.startupError !== ""
                                       ? Theme.danger : Theme.secondary
                                font.pixelSize: Theme.metadata
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                            CheckBox {
                                text: "Close button minimizes to tray"
                                checked: settingsViewModel.minimizeToTray
                                onToggled: settingsViewModel.setMinimizeToTray(checked)
                            }
                            CheckBox {
                                text: "Enable Desktop Widget (safe window mode)"
                                checked: settingsViewModel.widgetEnabled
                                onToggled: settingsViewModel.setWidgetEnabled(checked)
                            }
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 1
                                color: Theme.border
                            }
                            Text {
                                text: "LOCAL BACKUPS"
                                color: Theme.dim
                                font.pixelSize: Theme.groupHeading
                                font.weight: Font.DemiBold
                            }
                            RowLayout {
                                spacing: Theme.s8
                                PrimaryButton {
                                    text: "Export Backup"
                                    iconName: "completed"
                                    onClicked: appViewModel.exportBackup()
                                }
                                PourButton {
                                    text: "Replace Current Data..."
                                    onClicked: appViewModel.importBackup()
                                }
                            }
                            Text {
                                text: "Replacement validates the imported database and creates a safety backup first."
                                color: Theme.secondary
                                font.pixelSize: Theme.bodyText
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                            }
                            Item { Layout.fillHeight: true }
                            Text {
                                objectName: "aboutVersionText"
                                text: "PourTask " + appVersion
                                color: Theme.dim
                                font.pixelSize: Theme.bodyText
                                Accessible.name: "PourTask version " + appVersion
                            }
                        }

                        ListView {
                            id: taskList
                            visible: appViewModel.currentView !== "settings"
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            model: appViewModel.tasks
                            spacing: Theme.s8
                            clip: true
                            delegate: TaskRow {
                                selected: appViewModel.selectedTask.id === taskId
                                onToggled: value => appViewModel.setCompleted(taskId, value)
                                onOpened: {
                                    root.setEditorCollapsed(false)
                                    appViewModel.openDetail(taskId)
                                }
                            }
                            EmptyState {
                                anchors.centerIn: parent
                                visible: taskList.count === 0
                                title: root.emptyTitle()
                                subtitle: root.emptySubtitle()
                            }
                        }
                    }

                    Button {
                        id: expandEditorButton
                        objectName: "expandEditorButton"
                        visible: root.editorCollapsed
                                 && appViewModel.currentView !== "settings"
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.topMargin: Theme.s16
                        width: 30
                        height: 36
                        text: "‹"
                        ToolTip.visible: hovered
                        ToolTip.text: "Expand task details"
                        onClicked: root.setEditorCollapsed(false)
                        contentItem: Text {
                            text: expandEditorButton.text
                            color: Theme.secondary
                            font.pixelSize: 20
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        background: Rectangle {
                            radius: Theme.rSmall
                            color: expandEditorButton.hovered ? Theme.hover : Theme.subtle
                            border.color: Theme.border
                        }
                    }
                }

                DetailsPanel {
                    id: detailsPanel
                    objectName: "detailsPanel"
                    visible: !root.editorCollapsed
                             && appViewModel.currentView !== "settings"
                    SplitView.fillWidth: visible
                    SplitView.minimumWidth: 260
                    SplitView.preferredWidth: root.lastEditorWidth
                    SplitView.maximumWidth: Math.max(260, contentSplitView.width - 180)
                    task: appViewModel.selectedTask
                    viewModel: appViewModel
                    onCollapseRequested: root.setEditorCollapsed(true)
                    onWidthChanged: {
                        if (visible && contentSplitView.resizing && width >= 260)
                            root.lastEditorWidth = width
                    }
                }
            }
        }
    }

    Rectangle {
        visible: appViewModel.message !== ""
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.rightMargin: Theme.s20
        anchors.bottomMargin: Theme.s20
        width: Math.min(root.width - Theme.s32, toastRow.implicitWidth + Theme.s24)
        height: 44
        radius: Theme.rControl
        color: Theme.accentDim
        border.color: Theme.borderStrong
        z: 20

        RowLayout {
            id: toastRow
            anchors.fill: parent
            anchors.leftMargin: Theme.s12
            anchors.rightMargin: Theme.s12
            spacing: Theme.s8
            Text {
                text: root.toastText()
                color: Theme.text
                font.pixelSize: Theme.bodyText
                elide: Text.ElideRight
                Layout.fillWidth: true
            }
            Button {
                id: undoButton
                visible: appViewModel.message.indexOf("Undo") >= 0
                text: strings.undo
                onClicked: appViewModel.undo()
                contentItem: Text {
                    text: undoButton.text
                    color: Theme.accentHover
                    font.pixelSize: Theme.bodyText
                    font.weight: Font.DemiBold
                }
                background: Item {}
            }
        }
    }
}
