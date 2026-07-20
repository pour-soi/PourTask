import QtQuick
import "../theme"

PourTextField {
    id: control
    leftPadding: Theme.s32 + Theme.s4
    placeholderText: "Search tasks..."
    PourIcon { name: "search"; width: 16; height: 16; iconColor: control.activeFocus ? Theme.accent : Theme.dim; anchors.left: parent.left; anchors.leftMargin: Theme.s12; anchors.verticalCenter: parent.verticalCenter }
}
