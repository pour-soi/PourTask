import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "theme"
import "components"

ApplicationWindow {
    id: widget
    objectName: "desktopWidget"
    width: settingsViewModel.widgetExpandedWidth
    height: settingsViewModel.widgetCompact
            ? 70 : settingsViewModel.widgetExpandedHeight
    minimumWidth: 220
    minimumHeight: settingsViewModel.widgetCompact ? 60 : 115
    visible: false
    title: "PourTask Today"
    flags: Qt.Tool | Qt.FramelessWindowHint
           | (settingsViewModel.widgetAlwaysOnTop ? Qt.WindowStaysOnTopHint : 0)
    color: "transparent"

    readonly property bool compact: settingsViewModel.widgetCompact
    property string quickAddError: ""

    function openMain() {
        mainWindow.show()
        mainWindow.raise()
        mainWindow.requestActivate()
    }
    function setCompact(value) {
        if (value === compact)
            return
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
        geometrySaveTimer.restart()
        if (!compact) expandedSizeTimer.restart()
    }
    onHeightChanged: {
        geometrySaveTimer.restart()
        if (!compact) expandedSizeTimer.restart()
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
        onTriggered: settingsViewModel.setWidgetExpandedSize(
                         Math.round(widget.width), Math.round(widget.height))
    }

    Rectangle {
        anchors.fill: parent
        radius: Theme.rLarge
        color: Theme.elevated
        border.color: Theme.borderStrong

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 6
            spacing: Theme.s4

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 28
                spacing: Theme.s4

                Item {
                    id: dragArea
                    objectName: "widgetDragArea"
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    Text {
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        text: "Today · " + taskList.count
                        color: Theme.text
                        font.pixelSize: 15
                        font.weight: Font.DemiBold
                        elide: Text.ElideRight
                        width: parent.width
                    }
                    DragHandler {
                        target: null
                        enabled: !settingsViewModel.widgetLockPosition
                        onActiveChanged: if (active) widget.startSystemMove()
                    }
                    TapHandler {
                        acceptedButtons: Qt.LeftButton
                        onDoubleTapped: widget.openMain()
                    }
                }

                PourButton {
                    text: "Open"
                    Layout.preferredHeight: 28
                    ToolTip.text: "Open PourTask"
                    onClicked: widget.openMain()
                }
                PourButton {
                    objectName: "widgetCompactButton"
                    text: widget.compact ? "Expand" : "Collapse"
                    Layout.preferredHeight: 28
                    ToolTip.text: widget.compact ? "Expand" : "Compact"
                    onClicked: widget.setCompact(!widget.compact)
                }
            }

            ListView {
                id: taskList
                objectName: "widgetTaskList"
                visible: !widget.compact
                Layout.fillWidth: true
                Layout.fillHeight: true
                model: appViewModel.todayTasks
                spacing: 2
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                delegate: WidgetTaskRow {
                    onToggled: value => appViewModel.setCompleted(taskId, value)
                    onOpened: widget.openTask(taskId)
                }
                Text {
                    objectName: "widgetEmptyState"
                    anchors.top: parent.top
                    anchors.topMargin: Theme.s8
                    anchors.horizontalCenter: parent.horizontalCenter
                    visible: taskList.count === 0
                    text: "No tasks for today"
                    color: Theme.secondary
                    font.pixelSize: Theme.bodyText
                }
            }

            PourTextField {
                id: quickAdd
                objectName: "widgetQuickAdd"
                visible: !widget.compact
                Layout.fillWidth: true
                Layout.preferredHeight: 32
                placeholderText: strings.quick_add
                Accessible.name: "Add a task for today"
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
                visible: !widget.compact && widget.quickAddError !== ""
                text: widget.quickAddError
                color: Theme.danger
                font.pixelSize: Theme.metadata
                Layout.fillWidth: true
                elide: Text.ElideRight
            }
        }
    }

    TapHandler {
        acceptedButtons: Qt.RightButton
        onTapped: widgetMenu.popup()
    }
    Menu {
        id: widgetMenu
        MenuItem {
            objectName: "widgetOpenAction"
            text: "Open PourTask"
            onTriggered: widget.openMain()
        }
        MenuItem {
            objectName: "widgetCompactAction"
            text: widget.compact ? "Expand" : "Compact"
            onTriggered: widget.setCompact(!widget.compact)
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
        targetWindow: widget
        edges: Qt.LeftEdge
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 6
        cursorShape: Qt.SizeHorCursor
    }
    WidgetResizeHandle {
        objectName: "widgetRightResizeHandle"
        targetWindow: widget
        edges: Qt.RightEdge
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 6
        cursorShape: Qt.SizeHorCursor
    }
    WidgetResizeHandle {
        objectName: "widgetTopResizeHandle"
        targetWindow: widget
        edges: Qt.TopEdge
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: 6
        cursorShape: Qt.SizeVerCursor
    }
    WidgetResizeHandle {
        objectName: "widgetBottomResizeHandle"
        targetWindow: widget
        edges: Qt.BottomEdge
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: 6
        cursorShape: Qt.SizeVerCursor
    }
    WidgetResizeHandle {
        targetWindow: widget
        edges: Qt.LeftEdge | Qt.TopEdge
        anchors.left: parent.left
        anchors.top: parent.top
        width: 10
        height: 10
        cursorShape: Qt.SizeFDiagCursor
    }
    WidgetResizeHandle {
        targetWindow: widget
        edges: Qt.RightEdge | Qt.TopEdge
        anchors.right: parent.right
        anchors.top: parent.top
        width: 10
        height: 10
        cursorShape: Qt.SizeBDiagCursor
    }
    WidgetResizeHandle {
        targetWindow: widget
        edges: Qt.LeftEdge | Qt.BottomEdge
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        width: 10
        height: 10
        cursorShape: Qt.SizeBDiagCursor
    }
    WidgetResizeHandle {
        targetWindow: widget
        edges: Qt.RightEdge | Qt.BottomEdge
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        width: 10
        height: 10
        cursorShape: Qt.SizeFDiagCursor
    }
}
