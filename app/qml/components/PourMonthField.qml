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
    readonly property bool narrow: width < 340
    readonly property bool popupOpen: picker.opened
    signal normalized(string isoMonth)
    signal manuallyEdited()
    signal popupOpening()

    function focusInput() { input.forceActiveFocus() }
    function closePopup() { picker.close() }
    function normalize() {
        var result = viewModel.normalizeMonth(input.text)
        if (!result.valid) {
            errorText = "Enter a valid month, for example 07/2026."
            return false
        }
        input.text = result.display; errorText = ""; normalized(result.iso)
        return true
    }
    function openPicker() {
        if (readOnly) return
        popupOpening()
        var result = viewModel.normalizeMonth(input.text)
        picker.showFor(control, result.valid ? result.iso : "")
    }
    function setAutomatic(isoMonth) {
        var result = viewModel.normalizeMonth(isoMonth)
        input.text = result.display; errorText = ""; normalized(result.iso)
    }
    function clearValue(userAction) {
        input.text = ""; errorText = ""; normalized("")
        if (userAction) manuallyEdited()
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
            onTextEdited: { control.errorText = ""; control.manuallyEdited() }
            onEditingFinished: control.normalize()
            onAccepted: control.normalize()
            onActiveFocusChanged: { if (activeFocus && !readOnly) control.openPicker() }
            TapHandler { onTapped: control.openPicker() }
            Keys.onPressed: event => {
                if (event.key === Qt.Key_Down && (event.modifiers & Qt.AltModifier)) {
                    control.openPicker(); event.accepted = true
                }
            }
        }
        Button {
            id: monthButton
            objectName: control.objectName + "PickerButton"
            implicitWidth: Theme.controlHeight; implicitHeight: Theme.controlHeight
            enabled: !control.readOnly
            onClicked: picker.opened ? picker.close() : control.openPicker()
            contentItem: PourIcon { name: "month"; iconColor: monthButton.enabled ? Theme.accent : Theme.dim }
            background: Rectangle {
                radius: Theme.rControl
                color: monthButton.down ? Theme.pressed : (monthButton.hovered ? Theme.hover : Theme.elevated)
                border.color: Theme.border
            }
        }
        PourButton {
            objectName: control.objectName + "ClearButton"
            visible: control.text.length > 0 && !control.readOnly
            text: "Clear"
            Layout.fillWidth: control.narrow
            onClicked: control.clearValue(true)
        }
    }
    FieldError { text: control.errorText }
    MonthPickerPopup {
        id: picker
        objectName: control.objectName + "Popup"
        onMonthSelected: iso => {
            var result = control.viewModel.normalizeMonth(iso)
            input.text = result.display; control.errorText = ""
            control.manuallyEdited(); control.normalized(iso)
        }
        onCleared: control.clearValue(true)
    }
}
