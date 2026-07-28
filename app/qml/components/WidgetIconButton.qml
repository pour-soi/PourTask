import QtQuick
import QtQuick.Controls
import "../theme"

Button {
    id: control
    property string iconName: ""
    implicitWidth: 28
    implicitHeight: 26
    padding: 0
    hoverEnabled: true
    Accessible.role: Accessible.Button
    Accessible.name: ToolTip.text
    ToolTip.visible: hovered
    ToolTip.delay: 450
    contentItem: PourIcon {
        name: control.iconName
        iconColor: control.down ? Theme.elevated : Theme.secondary
        width: 15
        height: 15
        anchors.centerIn: parent
    }
    background: Rectangle {
        radius: Theme.rSmall
        color: control.down ? Theme.accent
                            : (control.hovered ? Theme.hover : "transparent")
        border.color: control.activeFocus ? Theme.accent : "transparent"
    }
}
