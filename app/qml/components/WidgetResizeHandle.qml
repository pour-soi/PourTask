import QtQuick

MouseArea {
    required property var targetWindow
    required property int edges
    hoverEnabled: true
    acceptedButtons: Qt.LeftButton
    onPressed: targetWindow.startSystemResize(edges)
}
