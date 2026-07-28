import QtQuick
import QtQuick.Controls
import "../theme"

AbstractButton {
    id: control
    property int indicatorSize: 20
    checkable: true
    implicitWidth: Theme.s32
    implicitHeight: Theme.s32
    Accessible.role: Accessible.CheckBox
    Accessible.checked: checked
    background: Rectangle {
        anchors.centerIn: parent
        width: control.indicatorSize; height: control.indicatorSize
        radius: Math.max(4, control.indicatorSize * 0.3)
        color: control.checked ? Theme.accent : (control.hovered ? Theme.hover : Theme.surface)
        border.width: control.activeFocus ? 2 : 1
        border.color: control.checked ? Theme.accent : (control.hovered ? Theme.accent : Theme.borderStrong)
        Behavior on color { ColorAnimation { duration: Theme.fast } }
        Canvas {
            anchors.fill: parent
            visible: control.checked
            onPaint: {
                var c = getContext("2d")
                c.clearRect(0, 0, width, height)
                c.strokeStyle = "#ffffff"; c.lineWidth = 1.8; c.lineCap = "round"; c.lineJoin = "round"
                c.beginPath()
                c.moveTo(width * .28, height * .5)
                c.lineTo(width * .43, height * .65)
                c.lineTo(width * .73, height * .33)
                c.stroke()
            }
        }
    }
}
