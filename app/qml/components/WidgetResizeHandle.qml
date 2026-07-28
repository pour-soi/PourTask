import QtQuick

MouseArea {
    required property var targetWindow
    required property int edges
    signal interactionChanged(bool active)
    hoverEnabled: true
    acceptedButtons: Qt.LeftButton
    onPressed: {
        interactionChanged(true)
        targetWindow.startSystemResize(edges)
    }
    onReleased: interactionChanged(false)
    onCanceled: interactionChanged(false)
}
