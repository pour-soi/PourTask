pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"

Popup {
    id: popup
    width: 304
    height: 260
    padding: Theme.s12
    modal: false
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    property string selectedIso: ""
    property int viewYear: new Date().getFullYear()
    signal monthSelected(string isoMonth)
    signal cleared()
    Shortcut {
        sequence: "Escape"; context: Qt.ApplicationShortcut; enabled: popup.opened
        onActivated: popup.close()
    }
    property var months: ["January", "February", "March", "April", "May", "June",
                          "July", "August", "September", "October", "November", "December"]

    function pad(value) { return value < 10 ? "0" + value : String(value) }
    function showFor(item, isoValue) {
        selectedIso = isoValue || ""
        viewYear = selectedIso ? Number(selectedIso.slice(0, 4)) : new Date().getFullYear()
        parent = Overlay.overlay
        var point = item.mapToItem(parent, 0, item.height)
        x = Math.max(Theme.s8, Math.min(point.x, parent.width - width - Theme.s8))
        y = point.y + height <= parent.height - Theme.s8
                ? point.y : Math.max(Theme.s8, point.y - item.height - height)
        open()
    }

    background: Rectangle { radius: Theme.radius; color: Theme.elevated; border.color: Theme.borderStrong }
    contentItem: ColumnLayout {
        spacing: Theme.s8
        RowLayout {
            Layout.fillWidth: true
            PourButton { text: "‹"; Accessible.name: "Previous year"; onClicked: popup.viewYear-- }
            Text {
                Layout.fillWidth: true; horizontalAlignment: Text.AlignHCenter
                text: popup.viewYear; color: Theme.text; font.pixelSize: Theme.bodyText; font.weight: Font.DemiBold
            }
            PourButton { text: "›"; Accessible.name: "Next year"; onClicked: popup.viewYear++ }
        }
        GridLayout {
            Layout.fillWidth: true; columns: 3; rowSpacing: Theme.s8; columnSpacing: Theme.s8
            Repeater {
                model: popup.months
                Button {
                    id: monthButton
                    required property int index
                    required property string modelData
                    property string isoValue: popup.viewYear + "-" + popup.pad(index + 1)
                    property bool selected: isoValue === popup.selectedIso
                    property bool current: popup.viewYear === new Date().getFullYear()
                                           && index === new Date().getMonth()
                    text: modelData.slice(0, 3)
                    onClicked: { popup.monthSelected(isoValue); popup.close() }
                    contentItem: Text {
                        text: monthButton.text
                        color: monthButton.selected ? Theme.elevated : Theme.text
                        horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
                        font.pixelSize: Theme.labelText
                        font.weight: monthButton.selected || monthButton.current ? Font.DemiBold : Font.Normal
                    }
                    background: Rectangle {
                        radius: Theme.rSmall
                        color: monthButton.selected ? Theme.accent : (monthButton.hovered ? Theme.hover : Theme.elevated)
                        border.width: monthButton.current && !monthButton.selected ? 1 : 0
                        border.color: Theme.accent
                    }
                }
            }
        }
        Item { Layout.fillHeight: true }
        RowLayout {
            Layout.fillWidth: true
            Text {
                text: popup.viewYear === new Date().getFullYear() ? "Current year" : ""
                color: Theme.dim; font.pixelSize: Theme.labelText
            }
            Item { Layout.fillWidth: true }
            PourButton {
                objectName: popup.objectName + "ClearButton"
                text: "Clear"; onClicked: { popup.cleared(); popup.close() }
            }
        }
    }
}
