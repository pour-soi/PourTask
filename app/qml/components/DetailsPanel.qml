import QtQuick
import QtQuick.Layouts
import "../theme"

Rectangle {
    id: panel
    property var task: ({})
    readonly property bool hasTask: Boolean(task && task.id)
    color: Theme.surface

    ColumnLayout {
        anchors.fill: parent; anchors.margins: Theme.s24; spacing: Theme.s12
        Text { text: "Task Details"; color: Theme.text; font.pixelSize: 18; font.weight: Font.DemiBold }
        Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: Theme.border }
        Item {
            visible: !panel.hasTask; Layout.fillWidth: true; Layout.fillHeight: true
            Text { anchors.centerIn: parent; text: "Select a task to view details."; color: Theme.secondary; font.pixelSize: Theme.bodyText }
        }
        ColumnLayout {
            visible: panel.hasTask; Layout.fillWidth: true; Layout.fillHeight: true; spacing: Theme.s12
            Text { text: "TITLE"; color: Theme.dim; font.pixelSize: Theme.labelText; font.weight: Font.DemiBold }
            PourTextField { id: detailTitle; Layout.fillWidth: true; text: panel.task.title || ""; readOnly: panel.task.completed || false; placeholderText: "Task title" }
            Text { text: "NOTES"; color: Theme.dim; font.pixelSize: Theme.labelText; font.weight: Font.DemiBold }
            PourTextArea { id: detailNotes; Layout.fillWidth: true; Layout.fillHeight: true; text: panel.task.notes || ""; readOnly: panel.task.completed || false; placeholderText: "Add notes, URLs, Chinese or English text" }
            Text { text: "SCHEDULE"; color: Theme.dim; font.pixelSize: Theme.labelText; font.weight: Font.DemiBold }
            PourTextField { id: scheduledField; Layout.fillWidth: true; text: panel.task.scheduledDate || ""; readOnly: panel.task.completed || false; placeholderText: "Scheduled date · YYYY-MM-DD" }
            PourTextField { id: dueField; Layout.fillWidth: true; text: panel.task.dueDate || ""; readOnly: panel.task.completed || false; placeholderText: "Deadline · YYYY-MM-DD" }
            PourTextField { id: monthField; Layout.fillWidth: true; text: panel.task.assignedMonth || ""; readOnly: panel.task.completed || false; placeholderText: "Assigned month · YYYY-MM" }
            RowLayout {
                Layout.fillWidth: true; spacing: Theme.s8
                PrimaryButton { visible: !panel.task.completed; text: "Save"; iconName: "completed"; onClicked: appViewModel.saveDetail(detailTitle.text, detailNotes.text, scheduledField.text, dueField.text, monthField.text) }
                PrimaryButton { visible: panel.task.completed; text: "Restore"; iconName: "completed"; onClicked: appViewModel.setCompleted(panel.task.id, false) }
                Item { Layout.fillWidth: true }
                PourButton { text: "Delete"; onClicked: appViewModel.deleteTask(panel.task.id) }
            }
        }
    }
}
