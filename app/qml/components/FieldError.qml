import QtQuick
import QtQuick.Layouts
import "../theme"

Text {
    Layout.fillWidth: true
    visible: text.length > 0
    color: Theme.danger
    font.pixelSize: Theme.labelText
    wrapMode: Text.WordWrap
}
