import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"

Item {
    id: editor
    property var task: ({})
    property var viewModel
    property bool creating: false
    property bool completed: !creating && Boolean(task.completed)
    property bool assignedMonthManual: !creating
    readonly property bool popupOpen: scheduledField.popupOpen || dueField.popupOpen || monthField.popupOpen
    signal cancelRequested()

    function source() { return creating ? viewModel.newTaskDefaults : task }
    function load() {
        var value = source() || ({})
        titleField.text = value.title || ""
        notesField.text = value.notes || ""
        scheduledField.text = value.scheduledDate || ""
        dueField.text = value.dueDate || ""
        monthField.text = value.assignedMonth || ""
        assignedMonthManual = creating ? Boolean(value.assignedMonthManual) : true
        clearErrors()
        if (creating) Qt.callLater(titleField.forceActiveFocus)
    }
    function clearErrors() {
        titleError.text = ""; scheduledField.errorText = ""
        dueField.errorText = ""; monthField.errorText = ""
    }
    function firstError(errors) {
        if (errors.title) return titleField
        if (errors.scheduled) return scheduledField
        if (errors.due) return dueField
        if (errors.assigned) return monthField
        return null
    }
    function applyErrors(errors) {
        titleError.text = errors.title || ""
        scheduledField.errorText = errors.scheduled || ""
        dueField.errorText = errors.due || ""
        monthField.errorText = errors.assigned || ""
        var field = firstError(errors)
        if (field) field === titleField ? field.forceActiveFocus() : field.focusInput()
    }
    function save() {
        scheduledField.normalize()
        dueField.normalize()
        monthField.normalize()
        var result = creating
                ? viewModel.createTask(titleField.text, notesField.text, scheduledField.text, dueField.text, monthField.text)
                : viewModel.saveDetail(titleField.text, notesField.text, scheduledField.text, dueField.text, monthField.text)
        if (!result.ok) applyErrors(result.errors || ({}))
    }
    function updateAutomaticMonth() {
        if (assignedMonthManual) return
        var scheduled = viewModel.normalizeDate(scheduledField.text)
        var due = viewModel.normalizeDate(dueField.text)
        var sourceIso = scheduled.valid && scheduled.iso ? scheduled.iso : (due.valid ? due.iso : "")
        monthField.setAutomatic(sourceIso ? sourceIso.slice(0, 7) : "")
    }

    Component.onCompleted: load()
    onTaskChanged: if (!creating) load()
    onCreatingChanged: load()

    Shortcut { sequence: "Ctrl+Return"; enabled: editor.visible; onActivated: editor.save() }
    Shortcut { sequence: "Ctrl+Enter"; enabled: editor.visible; onActivated: editor.save() }
    ScrollView {
        anchors.fill: parent
        clip: true
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        ColumnLayout {
            width: Math.max(0, editor.width - Theme.s4)
            spacing: Theme.s8
            Text { text: "TITLE"; color: Theme.dim; font.pixelSize: Theme.labelText; font.weight: Font.DemiBold }
            PourTextField {
                id: titleField; objectName: "taskTitleField"; Layout.fillWidth: true
                readOnly: editor.completed; error: titleError.text.length > 0
                placeholderText: editor.creating ? "What needs to be done?" : "Task title"
                onTextEdited: titleError.text = ""
            }
            FieldError { id: titleError }
            Text { text: "NOTES"; color: Theme.dim; font.pixelSize: Theme.labelText; font.weight: Font.DemiBold }
            PourTextArea {
                id: notesField; objectName: "taskNotesField"
                Layout.fillWidth: true; Layout.preferredHeight: Math.max(110, editor.height * 0.22)
                readOnly: editor.completed
                placeholderText: "Add notes, URLs, Chinese or English text"
            }
            Text { text: "SCHEDULE DATE"; color: Theme.dim; font.pixelSize: Theme.labelText; font.weight: Font.DemiBold }
            PourDateField {
                id: scheduledField; objectName: "scheduleDateField"; pickerObjectName: "scheduleCalendarButton"
                viewModel: editor.viewModel
                Layout.fillWidth: true; readOnly: editor.completed; placeholderText: "Schedule Date · MM/DD/YYYY"
                onPopupOpening: { dueField.closePopup(); monthField.closePopup() }
                onNormalized: editor.updateAutomaticMonth()
            }
            Text { text: "DUE DATE"; color: Theme.dim; font.pixelSize: Theme.labelText; font.weight: Font.DemiBold }
            PourDateField {
                id: dueField; objectName: "dueDateField"; pickerObjectName: "dueCalendarButton"
                viewModel: editor.viewModel
                Layout.fillWidth: true; readOnly: editor.completed; placeholderText: "Due Date · MM/DD/YYYY"
                onPopupOpening: { scheduledField.closePopup(); monthField.closePopup() }
                onNormalized: editor.updateAutomaticMonth()
            }
            Text { text: "ASSIGNED MONTH"; color: Theme.dim; font.pixelSize: Theme.labelText; font.weight: Font.DemiBold }
            PourMonthField {
                id: monthField; objectName: "assignedMonthField"
                viewModel: editor.viewModel
                Layout.fillWidth: true; readOnly: editor.completed; placeholderText: "Assigned Month · MM/YYYY"
                onPopupOpening: { scheduledField.closePopup(); dueField.closePopup() }
                onManuallyEdited: editor.assignedMonthManual = true
            }
            RowLayout {
                Layout.fillWidth: true; Layout.topMargin: Theme.s8; spacing: Theme.s8
                PrimaryButton {
                    objectName: editor.creating ? "saveTaskButton" : "saveChangesButton"
                    visible: !editor.completed
                    text: editor.creating ? "Save Task" : "Save"
                    iconName: "completed"; onClicked: editor.save()
                }
                PourButton {
                    objectName: "cancelTaskButton"
                    visible: editor.creating; text: "Cancel"; onClicked: editor.cancelRequested()
                }
                PrimaryButton {
                    visible: editor.completed; text: "Restore"; iconName: "completed"
                    onClicked: editor.viewModel.setCompleted(editor.task.id, false)
                }
                Item { Layout.fillWidth: true }
                PourButton {
                    objectName: "deleteTaskButton"
                    visible: !editor.creating; text: "Delete"
                    onClicked: editor.viewModel.deleteTask(editor.task.id)
                }
            }
        }
    }
}
