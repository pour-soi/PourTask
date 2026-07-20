import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"

Button {
    id: control
    property string iconName: "plus"
    implicitHeight: Theme.controlHeight
    leftPadding: Theme.s16; rightPadding: Theme.s16
    hoverEnabled: true
    contentItem: RowLayout {
        spacing: Theme.s8
        PourIcon { name: control.iconName; iconColor: control.down ? Theme.elevated : Theme.accent; Layout.preferredWidth: 16; Layout.preferredHeight: 16 }
        Text { text: control.text; color: control.down ? Theme.elevated : Theme.text; font.pixelSize: Theme.bodyText; font.weight: Font.DemiBold }
    }
    background: Rectangle {
        radius: Theme.rControl
        color: control.down ? Theme.accent : (control.hovered ? Theme.pressed : Theme.accentDim)
        border.color: control.activeFocus ? Theme.accentHover : Theme.accentDim
        Behavior on color { ColorAnimation { duration: Theme.fast } }
    }
}
