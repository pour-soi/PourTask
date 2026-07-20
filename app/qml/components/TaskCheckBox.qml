import QtQuick
import QtQuick.Controls
import "../theme"

AbstractButton {
    id: control
    checkable: true
    implicitWidth: 24
    implicitHeight: 24
    Accessible.role: Accessible.CheckBox
    Accessible.checked: checked
    background: Rectangle {
        anchors.centerIn: parent
        width: 20; height: 20; radius: 6
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
                c.beginPath(); c.moveTo(5.5, 10); c.lineTo(8.5, 13); c.lineTo(14.5, 6.5); c.stroke()
            }
        }
    }
}
