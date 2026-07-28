import QtQuick
import QtQuick.Layouts
import "../theme"

Rectangle {
    id: section
    property string title: ""
    property string description: ""
    default property alias contentData: body.data

    Layout.fillWidth: true
    implicitHeight: sectionColumn.implicitHeight + Theme.s24
    radius: Theme.rControl
    color: Theme.subtle
    border.color: Theme.border

    ColumnLayout {
        id: sectionColumn
        anchors.fill: parent
        anchors.margins: Theme.s12
        spacing: Theme.s8

        Text {
            text: section.title
            color: Theme.text
            font.pixelSize: Theme.groupHeading
            font.weight: Font.DemiBold
            font.letterSpacing: 0.3
            Layout.fillWidth: true
        }
        Text {
            visible: text.length > 0
            text: section.description
            color: Theme.secondary
            font.pixelSize: Theme.metadata
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
        ColumnLayout {
            id: body
            Layout.fillWidth: true
            spacing: Theme.s8
        }
    }
}
