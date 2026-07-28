import QtQuick
import QtQuick.Layouts
import "../theme"

Rectangle {
    id: row
    required property string taskId
    required property string title
    required property bool completed
    required property string displayDate
    required property string dateKind
    required property string warning
    property bool selected: false
    property bool compact: false
    signal toggled(bool completed)
    signal opened()

    width: ListView.view.width
    height: compact ? 44 : Theme.taskRowHeight
    radius: Theme.rControl
    color: selected ? Theme.accentDim : (mouse.containsMouse ? Theme.hover : Theme.surface)
    border.width: selected ? 1 : 0
    border.color: selected ? Theme.borderStrong : "transparent"
    opacity: completed ? 0.62 : 1
    Behavior on color { ColorAnimation { duration: Theme.fast } }
    Behavior on opacity { NumberAnimation { duration: Theme.normal } }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: row.compact ? Theme.s8 : Theme.s12
        anchors.rightMargin: row.compact ? Theme.s8 : Theme.s12
        anchors.topMargin: row.compact ? Theme.s4 : Theme.s8
        anchors.bottomMargin: row.compact ? Theme.s4 : Theme.s8
        spacing: row.compact ? Theme.s8 : Theme.s12
        TaskCheckBox {
            checked: row.completed
            onToggled: row.toggled(checked)
            Accessible.name: (checked ? "Restore " : "Complete ") + row.title
        }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: row.compact ? 0 : Theme.s4
            Text {
                text: row.title; color: Theme.text; font.pixelSize: Theme.taskTitle; font.weight: Font.DemiBold
                font.strikeout: row.completed; elide: Text.ElideRight; Layout.fillWidth: true
                maximumLineCount: row.compact ? 1 : 2
            }
            RowLayout {
                visible: !row.compact
                spacing: Theme.s8
                Rectangle {
                    visible: row.warning.length > 0
                    implicitWidth: warningText.implicitWidth + Theme.s12; implicitHeight: 22
                    radius: Theme.rSmall; color: Theme.warningBg
                    Text { id: warningText; anchors.centerIn: parent; text: row.warning; color: Theme.warning; font.pixelSize: Theme.metadata; font.weight: Font.DemiBold }
                }
                Text { text: row.displayDate ? row.dateKind + "  " + row.displayDate : row.dateKind; color: Theme.secondary; font.pixelSize: Theme.metadata }
            }
        }
    }
    MouseArea {
        id: mouse
        anchors.fill: parent
        anchors.leftMargin: row.compact ? 42 : 52
        hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: row.opened()
    }
}
