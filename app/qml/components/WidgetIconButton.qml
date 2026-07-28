import QtQuick
import QtQuick.Controls
import "../theme"

Button {
    id: control
    property string iconName: ""
    implicitWidth: Theme.compactControlHeight
    implicitHeight: Theme.compactControlHeight
    padding: 0
    hoverEnabled: true
    Accessible.role: Accessible.Button
    Accessible.name: ToolTip.text
    ToolTip.visible: hovered
    ToolTip.delay: 450
    contentItem: PourIcon {
        name: control.iconName
        iconColor: control.down ? Theme.elevated : Theme.secondary
        width: Theme.iconSmall
        height: Theme.iconSmall
        anchors.centerIn: parent
    }
    background: Rectangle {
        radius: Theme.rSmall
        color: control.down ? Theme.accent
                            : (control.hovered ? Theme.hover : "transparent")
        border.color: control.activeFocus ? Theme.accent : "transparent"
    }
}
