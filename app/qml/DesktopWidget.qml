import QtQuick
import QtQuick.Controls
import "theme"
import "components"

ApplicationWindow {
    id: widget
    objectName: "desktopWidget"
    width: settingsViewModel.widgetExpandedWidth
    height: settingsViewModel.widgetCompact
            ? 70 : settingsViewModel.widgetExpandedHeight
    minimumWidth: 220
    minimumHeight: compact ? 60 : 115
    visible: false
    title: "PourTask Today"
    flags: Qt.Tool | Qt.FramelessWindowHint
           | (settingsViewModel.widgetAlwaysOnTop ? Qt.WindowStaysOnTopHint : 0)
    color: "transparent"

    readonly property bool persistentCompact: settingsViewModel.widgetCompact
    readonly property bool compact: persistentCompact && !hoverExpanded
    property bool hoverExpanded: false
    property bool pointerInside: false
    property bool controlPressed: false
    property bool nativeInteraction: false
    property bool quickAddActive: false
    property bool sizeTransitionActive: false
    property string quickAddError: ""
    readonly property bool hoverCollapseBlocked:
        quickAddActive || quickAdd.activeFocus || widgetMenu.visible || controlPressed || nativeInteraction

    function openMain() {
        mainWindow.show()
        mainWindow.raise()
        mainWindow.requestActivate()
    }
    function setCompact(value) {
        hoverExpandTimer.stop()
        hoverCollapseTimer.stop()
        hoverExpanded = false
        quickAddActive = false
        if (value === persistentCompact) {
            height = value ? 70 : settingsViewModel.widgetExpandedHeight
            return
        }
        if (value) {
            settingsViewModel.setWidgetExpandedSize(width, height)
            settingsViewModel.setWidgetCompact(true)
            height = 70
        } else {
            settingsViewModel.setWidgetCompact(false)
            width = settingsViewModel.widgetExpandedWidth
            height = settingsViewModel.widgetExpandedHeight
        }
    }
    function beginQuickAdd() {
        quickAddActive = true
        quickAddError = ""
        Qt.callLater(quickAdd.forceActiveFocus)
    }
    function cancelQuickAdd() {
        quickAdd.text = ""
        quickAddError = ""
        quickAddActive = false
        scheduleHoverCollapse()
    }
    function setHoverExpanded(value) {
        if (value === hoverExpanded)
            return
        hoverExpanded = value
        if (value) {
            width = settingsViewModel.widgetExpandedWidth
            height = settingsViewModel.widgetExpandedHeight
        } else {
            height = 70
        }
    }
    function scheduleHoverCollapse() {
        if (hoverExpanded && !pointerInside && !hoverCollapseBlocked)
            hoverCollapseTimer.restart()
    }
    function hoverEntered() {
        pointerInside = true
        hoverCollapseTimer.stop()
        if (settingsViewModel.widgetExpandOnHover
                && persistentCompact && !hoverExpanded)
            hoverExpandTimer.restart()
    }
    function hoverLeft() {
        pointerInside = false
        hoverExpandTimer.stop()
        scheduleHoverCollapse()
    }
    function openTask(taskId) {
        appViewModel.openDetail(taskId)
        mainWindow.setEditorCollapsed(false)
        openMain()
    }

    onClosing: function(close) {
        close.accepted = false
        widget.hide()
    }
    onXChanged: geometrySaveTimer.restart()
    onYChanged: geometrySaveTimer.restart()
    onWidthChanged: {
        if (!persistentCompact) {
            geometrySaveTimer.restart()
            expandedSizeTimer.restart()
        }
    }
    onHeightChanged: {
        if (!persistentCompact) {
            geometrySaveTimer.restart()
            expandedSizeTimer.restart()
        }
    }
    onHoverCollapseBlockedChanged: if (!hoverCollapseBlocked) scheduleHoverCollapse()

    Behavior on height {
        enabled: !widget.nativeInteraction
        NumberAnimation {
            duration: Theme.normal
            easing.type: Easing.OutCubic
            onRunningChanged: widget.sizeTransitionActive = running
        }
    }

    Timer {
        id: geometrySaveTimer
        interval: 400
        onTriggered: settingsViewModel.setWidgetGeometry(
                         Math.round(widget.x), Math.round(widget.y),
                         Math.round(widget.width), Math.round(widget.height))
    }
    Timer {
        id: expandedSizeTimer
        interval: 400
        onTriggered: if (!widget.persistentCompact)
                         settingsViewModel.setWidgetExpandedSize(
                             Math.round(widget.width), Math.round(widget.height))
    }
    Timer {
        id: hoverExpandTimer
        objectName: "widgetHoverExpandTimer"
        interval: 375
        onTriggered: {
            if (settingsViewModel.widgetExpandOnHover
                    && widget.persistentCompact && widget.pointerInside)
                widget.setHoverExpanded(true)
        }
    }
    Timer {
        id: hoverCollapseTimer
        objectName: "widgetHoverCollapseTimer"
        interval: 650
        onTriggered: {
            if (widget.hoverExpanded && !widget.pointerInside
                    && !widget.hoverCollapseBlocked)
                widget.setHoverExpanded(false)
        }
    }

    Rectangle {
        id: widgetSurface
        objectName: "widgetSurface"
        anchors.fill: parent
        radius: Theme.radius
        color: Theme.elevated
        border.color: Theme.borderStrong
        z: 0

        HoverHandler {
            id: widgetHover
            onHoveredChanged: {
                if (hovered) widget.hoverEntered()
                else widget.hoverLeft()
            }
        }

        Item {
            id: header
            objectName: "widgetHeader"
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.leftMargin: Theme.s8
            anchors.rightMargin: Theme.s8
            anchors.topMargin: widget.compact
                               ? Math.max(5, (widget.height - height) / 2)
                               : 5
            height: Theme.widgetHeaderHeight
            z: 3

            Item {
                id: dragArea
                objectName: "widgetDragArea"
                anchors.left: parent.left
                anchors.right: headerButtons.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom

                Text {
                    id: todayLabel
                    anchors.left: brandIcon.right
                    anchors.leftMargin: Theme.s8
                    anchors.verticalCenter: parent.verticalCenter
                    text: "Today"
                    color: Theme.text
                    font.pixelSize: 14
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
                }
                Image {
                    id: brandIcon
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    width: Theme.iconMedium
                    height: Theme.iconMedium
                    source: appIconUrl
                    fillMode: Image.PreserveAspectFit
                }
                Text {
                    anchors.left: todayLabel.right
                    anchors.leftMargin: Theme.s8
                    anchors.verticalCenter: parent.verticalCenter
                    text: taskList.count
                    color: Theme.accent
                    font.pixelSize: 12
                    font.weight: Font.DemiBold
                }
                DragHandler {
                    target: null
                    enabled: !settingsViewModel.widgetLockPosition
                    onActiveChanged: {
                        widget.nativeInteraction = active
                        if (active)
                            widget.startSystemMove()
                    }
                }
                TapHandler {
                    acceptedButtons: Qt.LeftButton
                    onDoubleTapped: widget.openMain()
                }
            }

            Row {
                id: headerButtons
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                spacing: 0
                WidgetIconButton {
                    objectName: "widgetOpenButton"
                    iconName: "open"
                    ToolTip.text: "Open PourTask"
                    onPressedChanged: widget.controlPressed = pressed
                    onClicked: widget.openMain()
                }
                WidgetIconButton {
                    objectName: "widgetCompactButton"
                    iconName: widget.compact ? "down" : "up"
                    ToolTip.text: widget.compact ? "Expand widget" : "Collapse widget"
                    onPressedChanged: widget.controlPressed = pressed
                    onClicked: widget.setCompact(!widget.persistentCompact)
                }
            }
        }

        Rectangle {
            anchors.left: parent.left; anchors.right: parent.right
            anchors.top: header.bottom
            anchors.leftMargin: Theme.s8
            anchors.rightMargin: Theme.s8
            height: 1; color: Theme.border; visible: !widget.compact
        }

        Rectangle {
            id: footer
            objectName: "widgetFooter"
            visible: !widget.compact
            anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom
            anchors.leftMargin: Theme.s8
            anchors.rightMargin: Theme.s8
            anchors.bottomMargin: Theme.s4
            height: Theme.compactControlHeight
            z: 3
            radius: Theme.rSmall
            color: Theme.subtle

            Button {
                id: addTaskButton
                objectName: "widgetAddTaskButton"
                anchors.fill: parent
                visible: !widget.quickAddActive
                text: "+  Add task"
                Accessible.name: "Add a task for today"
                contentItem: Text {
                    text: addTaskButton.text
                    color: addTaskButton.hovered ? Theme.accentHover : Theme.accent
                    font.pixelSize: Theme.bodyText
                    font.weight: Font.DemiBold
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    radius: Theme.rSmall
                    color: addTaskButton.hovered ? Theme.hover : "transparent"
                }
                onClicked: widget.beginQuickAdd()
            }

            PourTextField {
                id: quickAdd
                objectName: "widgetQuickAdd"
                visible: widget.quickAddActive
                anchors.fill: parent
                placeholderText: "Task for today"
                Accessible.name: "Add a task for today"
                onActiveFocusChanged: if (!activeFocus) widget.scheduleHoverCollapse()
                onTextEdited: widget.quickAddError = ""
                onAccepted: {
                    if (text.trim() === "")
                        return
                    if (appViewModel.addTodayTask(text)) {
                        text = ""
                        widget.quickAddError = ""
                        widget.quickAddActive = false
                    } else {
                        widget.quickAddError = "Enter a task title."
                    }
                }
                Keys.onEscapePressed: widget.cancelQuickAdd()
            }
        }

        Text {
            id: quickAddErrorText
            visible: !widget.compact && widget.quickAddError !== ""
            anchors.left: footer.left
            anchors.right: footer.right
            anchors.bottom: footer.top
            anchors.bottomMargin: 1
            text: widget.quickAddError
            color: Theme.danger
            font.pixelSize: Theme.metadata
            elide: Text.ElideRight
            z: 4
        }

        ListView {
            id: taskList
            objectName: "widgetTaskList"
            visible: !widget.compact
            opacity: 1
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: header.bottom
            anchors.bottom: quickAddErrorText.visible
                            ? quickAddErrorText.top : footer.top
            anchors.leftMargin: Theme.s8
            anchors.rightMargin: Theme.s8
            anchors.topMargin: Theme.s4
            anchors.bottomMargin: Theme.s4
            model: appViewModel.todayTasks
            spacing: 1
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            z: 2
            delegate: WidgetTaskRow {
                onInteractionChanged: active => widget.controlPressed = active
                onToggled: value => appViewModel.setCompleted(taskId, value)
                onOpened: widget.openTask(taskId)
            }
            Text {
                objectName: "widgetEmptyState"
                anchors.top: parent.top
                anchors.topMargin: 6
                anchors.horizontalCenter: parent.horizontalCenter
                visible: taskList.count === 0
                text: "No tasks for today"
                color: Theme.secondary
                font.pixelSize: Theme.bodyText
            }
        }
    }

    TapHandler {
        acceptedButtons: Qt.RightButton
        onTapped: widgetMenu.popup()
    }
    Menu {
        id: widgetMenu
        objectName: "widgetContextMenu"
        onAboutToShow: hoverCollapseTimer.stop()
        onClosed: widget.scheduleHoverCollapse()
        MenuItem {
            objectName: "widgetOpenAction"
            text: "Open PourTask"
            onTriggered: widget.openMain()
        }
        MenuItem {
            objectName: "widgetCompactAction"
            text: widget.persistentCompact ? "Expand" : "Compact"
            onTriggered: widget.setCompact(!widget.persistentCompact)
        }
        MenuItem {
            objectName: "widgetHoverExpandAction"
            text: "Expand widget on hover"
            checkable: true
            checked: settingsViewModel.widgetExpandOnHover
            onTriggered: settingsViewModel.setWidgetExpandOnHover(checked)
        }
        MenuItem {
            objectName: "widgetAlwaysOnTopAction"
            text: "Always on Top"
            checkable: true
            checked: settingsViewModel.widgetAlwaysOnTop
            onTriggered: {
                settingsViewModel.setWidgetAlwaysOnTop(checked)
                Qt.callLater(widget.show)
            }
        }
        MenuItem {
            objectName: "widgetLockPositionAction"
            text: "Lock Position"
            checkable: true
            checked: settingsViewModel.widgetLockPosition
            onTriggered: settingsViewModel.setWidgetLockPosition(checked)
        }
        MenuSeparator {}
        MenuItem {
            objectName: "widgetHideAction"
            text: "Hide Widget"
            onTriggered: widget.hide()
        }
    }

    WidgetResizeHandle {
        objectName: "widgetLeftResizeHandle"
        targetWindow: widget; edges: Qt.LeftEdge
        anchors.left: parent.left; anchors.top: parent.top; anchors.bottom: parent.bottom
        width: 6; cursorShape: Qt.SizeHorCursor
        onInteractionChanged: active => widget.nativeInteraction = active
    }
    WidgetResizeHandle {
        objectName: "widgetRightResizeHandle"
        targetWindow: widget; edges: Qt.RightEdge
        anchors.right: parent.right; anchors.top: parent.top; anchors.bottom: parent.bottom
        width: 6; cursorShape: Qt.SizeHorCursor
        onInteractionChanged: active => widget.nativeInteraction = active
    }
    WidgetResizeHandle {
        objectName: "widgetTopResizeHandle"
        targetWindow: widget; edges: Qt.TopEdge
        anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top
        height: 6; cursorShape: Qt.SizeVerCursor
        onInteractionChanged: active => widget.nativeInteraction = active
    }
    WidgetResizeHandle {
        objectName: "widgetBottomResizeHandle"
        targetWindow: widget; edges: Qt.BottomEdge
        anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom
        height: 6; cursorShape: Qt.SizeVerCursor
        onInteractionChanged: active => widget.nativeInteraction = active
    }
    WidgetResizeHandle {
        targetWindow: widget; edges: Qt.LeftEdge | Qt.TopEdge
        anchors.left: parent.left; anchors.top: parent.top
        width: 10; height: 10; cursorShape: Qt.SizeFDiagCursor
        onInteractionChanged: active => widget.nativeInteraction = active
    }
    WidgetResizeHandle {
        targetWindow: widget; edges: Qt.RightEdge | Qt.TopEdge
        anchors.right: parent.right; anchors.top: parent.top
        width: 10; height: 10; cursorShape: Qt.SizeBDiagCursor
        onInteractionChanged: active => widget.nativeInteraction = active
    }
    WidgetResizeHandle {
        targetWindow: widget; edges: Qt.LeftEdge | Qt.BottomEdge
        anchors.left: parent.left; anchors.bottom: parent.bottom
        width: 10; height: 10; cursorShape: Qt.SizeBDiagCursor
        onInteractionChanged: active => widget.nativeInteraction = active
    }
    WidgetResizeHandle {
        targetWindow: widget; edges: Qt.RightEdge | Qt.BottomEdge
        anchors.right: parent.right; anchors.bottom: parent.bottom
        width: 10; height: 10; cursorShape: Qt.SizeFDiagCursor
        onInteractionChanged: active => widget.nativeInteraction = active
    }
}
