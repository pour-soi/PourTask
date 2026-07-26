pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"

Popup {
    id: popup
    width: 304
    height: 354
    padding: Theme.s12
    modal: false
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    property string selectedIso: ""
    property int viewYear: new Date().getFullYear()
    property int viewMonth: new Date().getMonth()
    signal dateSelected(string isoDate)
    signal cleared()
    Shortcut {
        sequence: "Escape"; context: Qt.ApplicationShortcut; enabled: popup.opened
        onActivated: popup.close()
    }

    function pad(value) { return value < 10 ? "0" + value : String(value) }
    function iso(day) {
        return day.getFullYear() + "-" + pad(day.getMonth() + 1) + "-" + pad(day.getDate())
    }
    function shownDate(index) {
        var first = new Date(viewYear, viewMonth, 1)
        return new Date(viewYear, viewMonth, index - first.getDay() + 1)
    }
    function selectIso(isoValue) {
        selectedIso = isoValue || ""
        if (selectedIso) {
            var selected = new Date(selectedIso + "T12:00:00")
            viewYear = selected.getFullYear()
            viewMonth = selected.getMonth()
        }
    }
    function showFor(item, isoValue) {
        selectIso(isoValue)
        var selected = selectedIso ? new Date(selectedIso + "T12:00:00") : new Date()
        viewYear = selected.getFullYear()
        viewMonth = selected.getMonth()
        parent = Overlay.overlay
        var point = item.mapToItem(parent, 0, item.height)
        x = Math.max(Theme.s8, Math.min(point.x, parent.width - width - Theme.s8))
        y = point.y + height <= parent.height - Theme.s8
                ? point.y : Math.max(Theme.s8, point.y - item.height - height)
        open()
    }

    background: Rectangle {
        radius: Theme.radius
        color: Theme.elevated
        border.color: Theme.borderStrong
    }
    contentItem: ColumnLayout {
        spacing: Theme.s8
        RowLayout {
            Layout.fillWidth: true
            PourButton { text: "‹"; Accessible.name: "Previous month"; onClicked: {
                var d = new Date(popup.viewYear, popup.viewMonth - 1, 1)
                popup.viewYear = d.getFullYear(); popup.viewMonth = d.getMonth()
            }}
            Text {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                text: Qt.formatDate(new Date(popup.viewYear, popup.viewMonth, 1), "MMMM yyyy")
                color: Theme.text; font.pixelSize: Theme.bodyText; font.weight: Font.DemiBold
            }
            PourButton { text: "›"; Accessible.name: "Next month"; onClicked: {
                var d = new Date(popup.viewYear, popup.viewMonth + 1, 1)
                popup.viewYear = d.getFullYear(); popup.viewMonth = d.getMonth()
            }}
        }
        GridLayout {
            Layout.fillWidth: true
            columns: 7; rowSpacing: Theme.s4; columnSpacing: Theme.s4
            Repeater {
                model: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
                Text {
                    required property string modelData
                    Layout.preferredWidth: 34
                    horizontalAlignment: Text.AlignHCenter
                    text: modelData; color: Theme.dim; font.pixelSize: Theme.labelText
                }
            }
            Repeater {
                model: 42
                delegate: Button {
                    id: dayButton
                    required property int index
                    property date value: popup.shownDate(index)
                    property string valueIso: popup.iso(value)
                    property bool selected: valueIso === popup.selectedIso
                    property bool today: valueIso === popup.iso(new Date())
                    Layout.preferredWidth: 34; Layout.preferredHeight: 30
                    text: value.getDate()
                    onClicked: { popup.dateSelected(valueIso); popup.close() }
                    contentItem: Text {
                        text: dayButton.text
                        color: dayButton.selected ? Theme.elevated : (dayButton.value.getMonth() === popup.viewMonth ? Theme.text : Theme.dim)
                        horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
                        font.pixelSize: Theme.labelText; font.weight: dayButton.today ? Font.DemiBold : Font.Normal
                    }
                    background: Rectangle {
                        radius: Theme.rSmall
                        color: dayButton.selected ? Theme.accent : (dayButton.hovered ? Theme.hover : "transparent")
                        border.width: dayButton.today && !dayButton.selected ? 1 : 0
                        border.color: Theme.accent
                    }
                }
            }
        }
        Item { Layout.fillHeight: true }
        RowLayout {
            Layout.fillWidth: true
            PourButton {
                objectName: popup.objectName + "TodayButton"
                text: "Today"; onClicked: { popup.dateSelected(popup.iso(new Date())); popup.close() }
            }
            Item { Layout.fillWidth: true }
            PourButton {
                objectName: popup.objectName + "ClearButton"
                text: "Clear"; onClicked: { popup.cleared(); popup.close() }
            }
        }
    }
}
