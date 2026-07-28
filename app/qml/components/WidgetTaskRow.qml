import QtQuick
import QtQuick.Layouts
import "../theme"

Rectangle {
    id: row
    objectName: "widgetTaskRow"
    required property string taskId
    required property string title
    required property bool completed
    required property string displayDate
    required property string dateKind
    signal toggled(bool completed)
    signal opened()
    signal interactionChanged(bool active)
    property bool completionPending: false

    width: ListView.view ? ListView.view.width : 0
    height: Theme.widgetTaskRowHeight
    visible: true
    opacity: 1
    z: 2
    radius: Theme.rSmall
    color: mouse.containsMouse ? Theme.hover : "transparent"

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: Theme.s4
        anchors.rightMargin: Theme.s4
        spacing: Theme.s4

        TaskCheckBox {
            id: completionBox
            indicatorSize: 16
            implicitWidth: Theme.widgetHeaderHeight
            implicitHeight: Theme.widgetHeaderHeight
            checked: row.completed
            onToggled: {
                if (checked) {
                    row.completionPending = true
                    completionFade.restart()
                } else {
                    row.toggled(false)
                }
            }
            onPressedChanged: row.interactionChanged(pressed)
            Accessible.name: "Complete " + row.title
        }
        Text {
            objectName: "widgetTaskTitle"
            text: row.title
            color: Theme.text
            font.pixelSize: Theme.bodyText
            elide: Text.ElideRight
            maximumLineCount: 1
            Layout.fillWidth: true
        }
        Text {
            visible: row.dateKind === "Deadline" && row.displayDate !== ""
            text: row.displayDate
            color: Theme.secondary
            font.pixelSize: Theme.metadata
        }
    }

    SequentialAnimation {
        id: completionFade
        NumberAnimation { target: row; property: "opacity"; to: 0.35; duration: 90 }
        ScriptAction {
            script: {
                row.toggled(true)
                row.completionPending = false
            }
        }
    }

    MouseArea {
        id: mouse
        anchors.fill: parent
        anchors.leftMargin: 32
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: row.opened()
        onPressedChanged: row.interactionChanged(pressed || completionBox.pressed)
    }
}
