import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"

ColumnLayout {
    id: control
    spacing: Theme.s4
    property alias text: input.text
    property alias placeholderText: input.placeholderText
    property alias readOnly: input.readOnly
    property var viewModel
    property string errorText: ""
    property string pickerObjectName: ""
    readonly property bool narrow: width < 340
    readonly property bool popupOpen: calendar.opened
    signal normalized(string isoDate)
    signal popupOpening()

    function focusInput() { input.forceActiveFocus() }
    function closePopup() { calendar.close() }
    function normalize() {
        var result = viewModel.normalizeDate(input.text)
        if (!result.valid) {
            errorText = "Enter a valid date, for example " +
                    (placeholderText.indexOf("Due") >= 0 ? "08/01/2026." : "07/23/2026.")
            return false
        }
        input.text = result.display
        errorText = ""
        calendar.selectIso(result.iso)
        normalized(result.iso)
        return true
    }
    function openCalendar() {
        if (readOnly) return
        popupOpening()
        var result = viewModel.normalizeDate(input.text)
        calendar.showFor(control, result.valid ? result.iso : "")
    }
    function clearValue() {
        input.text = ""; errorText = ""; normalized("")
    }

    GridLayout {
        Layout.fillWidth: true
        columns: control.narrow ? 2 : 3
        columnSpacing: Theme.s4
        rowSpacing: Theme.s4
        PourTextField {
            id: input
            objectName: control.objectName + "Input"
            Layout.fillWidth: true
            Layout.columnSpan: control.narrow ? 2 : 1
            error: control.errorText.length > 0
            selectByMouse: true
            onTextEdited: control.errorText = ""
            onEditingFinished: control.normalize()
            onAccepted: control.normalize()
            onActiveFocusChanged: { if (activeFocus && !readOnly) control.openCalendar() }
            TapHandler { onTapped: control.openCalendar() }
            Keys.onPressed: event => {
                if (event.key === Qt.Key_Down && (event.modifiers & Qt.AltModifier)) {
                    control.openCalendar(); event.accepted = true
                }
            }
        }
        Button {
            id: calendarButton
            objectName: control.pickerObjectName
            implicitWidth: Theme.controlHeight; implicitHeight: Theme.controlHeight
            enabled: !control.readOnly
            onClicked: calendar.opened ? calendar.close() : control.openCalendar()
            contentItem: PourIcon { name: "month"; iconColor: calendarButton.enabled ? Theme.accent : Theme.dim }
            background: Rectangle {
                radius: Theme.rControl
                color: calendarButton.down ? Theme.pressed : (calendarButton.hovered ? Theme.hover : Theme.elevated)
                border.color: Theme.border
            }
        }
        PourButton {
            objectName: control.objectName + "ClearButton"
            visible: control.text.length > 0 && !control.readOnly
            text: "Clear"
            Layout.fillWidth: control.narrow
            onClicked: control.clearValue()
        }
    }
    FieldError { text: control.errorText }
    CalendarPopup {
        id: calendar
        objectName: control.pickerObjectName + "Popup"
        onDateSelected: iso => {
            var result = control.viewModel.normalizeDate(iso)
            input.text = result.display; control.errorText = ""; control.normalized(iso)
        }
        onCleared: control.clearValue()
    }
}
