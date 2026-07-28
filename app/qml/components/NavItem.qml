import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"

AbstractButton {
    id: control
    property string iconName: ""
    property bool selected: false
    implicitHeight: Theme.navHeight
    hoverEnabled: true
    Accessible.role: Accessible.Button
    ToolTip.visible: hovered && ToolTip.text.length > 0
    ToolTip.delay: 550
    contentItem: RowLayout {
        spacing: Theme.s12
        Item { Layout.preferredWidth: Theme.s4; Layout.fillHeight: true
            Rectangle { anchors.left: parent.left; anchors.verticalCenter: parent.verticalCenter; width: 3; height: 22; radius: 2; color: Theme.accent; visible: control.selected }
        }
        PourIcon { name: control.iconName; iconColor: control.selected ? Theme.accent : Theme.secondary; Layout.preferredWidth: 20; Layout.preferredHeight: 20 }
        Text { text: control.text; color: control.selected ? Theme.text : Theme.secondary; font.pixelSize: Theme.sidebarText; font.weight: control.selected ? Font.DemiBold : Font.Normal; Layout.fillWidth: true }
    }
    background: Rectangle {
        radius: Theme.rControl
        color: control.down ? Theme.pressed : (control.selected ? Theme.accentDim : (control.hovered ? Theme.hover : "transparent"))
        Behavior on color { ColorAnimation { duration: Theme.fast } }
    }
}
