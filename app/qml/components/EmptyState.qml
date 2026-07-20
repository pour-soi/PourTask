import QtQuick
import QtQuick.Layouts
import "../theme"

ColumnLayout {
    property string title: ""
    property string subtitle: ""
    spacing: Theme.s8
    Text { text: parent.title; color: Theme.text; font.pixelSize: 15; font.weight: Font.DemiBold; Layout.alignment: Qt.AlignHCenter }
    Text { text: parent.subtitle; color: Theme.secondary; font.pixelSize: Theme.bodyText; horizontalAlignment: Text.AlignHCenter; wrapMode: Text.WordWrap; Layout.maximumWidth: 320; Layout.alignment: Qt.AlignHCenter }
}
