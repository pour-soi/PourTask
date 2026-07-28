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

    width: ListView.view ? ListView.view.width : 0
    height: 30
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
            checked: row.completed
            onToggled: row.toggled(checked)
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
