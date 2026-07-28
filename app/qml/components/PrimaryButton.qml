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
        PourIcon {
            name: control.iconName
            iconColor: !control.enabled ? Theme.dim : (control.down ? Theme.elevated : Theme.accent)
            Layout.preferredWidth: Theme.iconSmall
            Layout.preferredHeight: Theme.iconSmall
        }
        Text {
            text: control.text
            color: !control.enabled ? Theme.dim : (control.down ? Theme.elevated : Theme.text)
            font.pixelSize: Theme.bodyText
            font.weight: Font.DemiBold
        }
    }
    background: Rectangle {
        radius: Theme.rControl
        color: !control.enabled ? Theme.subtle
                               : (control.down ? Theme.accent
                                  : (control.hovered ? Theme.pressed : Theme.accentDim))
        border.color: control.activeFocus ? Theme.accentHover : Theme.accentDim
        Behavior on color { ColorAnimation { duration: Theme.fast } }
    }
}
