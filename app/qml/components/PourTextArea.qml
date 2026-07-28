import QtQuick
import QtQuick.Controls
import "../theme"

TextArea {
    id: control
    leftPadding: Theme.s12; rightPadding: Theme.s12; topPadding: Theme.s12; bottomPadding: Theme.s12
    color: Theme.text; placeholderTextColor: Theme.dim
    selectionColor: Theme.accentDim; selectedTextColor: Theme.text
    font.pixelSize: Theme.bodyText; wrapMode: TextEdit.Wrap
    background: Rectangle {
        radius: Theme.rControl
        color: control.activeFocus ? Theme.surface
                                   : (control.hovered ? Theme.subtle : Theme.input)
        border.width: control.activeFocus ? 2 : 1
        border.color: control.activeFocus ? Theme.accent : Theme.border
        Behavior on color { ColorAnimation { duration: Theme.fast } }
        Behavior on border.color { ColorAnimation { duration: Theme.fast } }
    }
}
