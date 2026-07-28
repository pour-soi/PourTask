import QtQuick
import QtQuick.Controls
import "../theme"

Button {
    id: control
    implicitHeight: Theme.controlHeight
    leftPadding: Theme.s12
    rightPadding: Theme.s12
    hoverEnabled: true
    contentItem: Text {
        text: control.text
        color: control.down ? Theme.elevated : Theme.danger
        font.pixelSize: Theme.bodyText
        font.weight: Font.DemiBold
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
    background: Rectangle {
        radius: Theme.rControl
        color: control.down ? Theme.danger
                            : (control.hovered ? Theme.dangerBg : Theme.elevated)
        border.color: control.activeFocus ? Theme.danger : Theme.border
        Behavior on color { ColorAnimation { duration: Theme.fast } }
        Behavior on border.color { ColorAnimation { duration: Theme.fast } }
    }
}
