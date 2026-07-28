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
    property string quickAddError: ""
    readonly property bool hoverCollapseBlocked:
        quickAdd.activeFocus || widgetMenu.visible || controlPressed || nativeInteraction

    function openMain() {
        mainWindow.show()
        mainWindow.raise()
        mainWindow.requestActivate()
    }
    function setCompact(value) {
        hoverExpandTimer.stop()
        hoverCollapseTimer.stop()
        hoverExpanded = false
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
        radius: Theme.rLarge
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
            anchors.leftMargin: 6
            anchors.rightMargin: 5
            anchors.topMargin: 4
            height: 26
            z: 3

            Item {
                id: dragArea
                objectName: "widgetDragArea"
                anchors.left: parent.left
                anchors.right: headerButtons.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom

                Text {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    text: "Today · " + taskList.count
                    color: Theme.text
                    font.pixelSize: 14
                    font.weight: Font.DemiBold
                    elide: Text.ElideRight
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

        PourTextField {
            id: quickAdd
            objectName: "widgetQuickAdd"
            visible: !widget.compact
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.leftMargin: 5
            anchors.rightMargin: 5
            anchors.bottomMargin: 5
            height: 30
            placeholderText: strings.quick_add
            Accessible.name: "Add a task for today"
            z: 3
            onActiveFocusChanged: if (!activeFocus) widget.scheduleHoverCollapse()
            onTextEdited: widget.quickAddError = ""
            onAccepted: {
                if (appViewModel.addTodayTask(text)) {
                    text = ""
                    widget.quickAddError = ""
                } else {
                    widget.quickAddError = "Enter a task title."
                }
            }
        }

        Text {
            id: quickAddErrorText
            visible: !widget.compact && widget.quickAddError !== ""
            anchors.left: quickAdd.left
            anchors.right: quickAdd.right
            anchors.bottom: quickAdd.top
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
                            ? quickAddErrorText.top : quickAdd.top
            anchors.leftMargin: 5
            anchors.rightMargin: 5
            anchors.topMargin: 2
            anchors.bottomMargin: 3
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
