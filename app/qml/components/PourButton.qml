import QtQuick
import QtQuick.Controls
import "../theme"

Button {
    id: control
    implicitHeight: Theme.controlHeight
    font.pixelSize: 13
    contentItem: Text { text: control.text; color: control.down ? Theme.elevated : Theme.text; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
    background: Rectangle {
        radius: Theme.rControl
        color: control.down ? Theme.accent : (control.hovered ? Theme.accentDim : Theme.elevated)
        border.color: control.activeFocus ? Theme.accent : Theme.border
        Behavior on color { ColorAnimation { duration: Theme.fast } }
    }
}
