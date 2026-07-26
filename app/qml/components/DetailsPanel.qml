import QtQuick
import QtQuick.Layouts
import "../theme"

Rectangle {
    id: panel
    property var task: ({})
    property var viewModel
    property bool creating: Boolean(viewModel && viewModel.isCreating)
    readonly property bool popupOpen: editor.popupOpen
    readonly property bool hasTask: Boolean(task && task.id)
    color: Theme.surface

    ColumnLayout {
        anchors.fill: parent; anchors.margins: Theme.s24; spacing: Theme.s12
        Text { text: panel.creating ? "New Task" : "Task Details"; color: Theme.text; font.pixelSize: 18; font.weight: Font.DemiBold }
        Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: Theme.border }
        Item {
            visible: !panel.hasTask && !panel.creating; Layout.fillWidth: true; Layout.fillHeight: true
            Text { anchors.centerIn: parent; text: "Select a task to view details."; color: Theme.secondary; font.pixelSize: Theme.bodyText }
        }
        TaskEditor {
            id: editor
            objectName: "taskEditor"
            visible: panel.hasTask || panel.creating
            Layout.fillWidth: true; Layout.fillHeight: true
            task: panel.task; creating: panel.creating
            viewModel: panel.viewModel
            onCancelRequested: panel.viewModel.cancelNewTask()
        }
    }
}
