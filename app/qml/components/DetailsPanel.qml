import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"

Rectangle {
    id: panel
    property var task: ({})
    property var viewModel
    property bool creating: Boolean(viewModel && viewModel.isCreating)
    readonly property bool popupOpen: editor.popupOpen
    readonly property bool hasTask: Boolean(task && task.id)
    signal collapseRequested()
    color: Theme.surface

    ColumnLayout {
        anchors.fill: parent; anchors.margins: Theme.s24; spacing: Theme.s12
        RowLayout {
            Layout.fillWidth: true
            Text {
                objectName: "taskDetailsHeading"
                text: panel.creating ? "New Task" : "Task Details"
                color: Theme.text
                font.pixelSize: 18
                font.weight: Font.Bold
                elide: Text.ElideRight
                Layout.fillWidth: true
            }
            PourButton {
                objectName: "collapseEditorButton"
                text: "›"
                ToolTip.text: "Collapse task details"
                onClicked: panel.collapseRequested()
            }
        }
        Rectangle {
            objectName: "taskDetailsDivider"
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            Layout.bottomMargin: Theme.s4
            color: Theme.borderStrong
        }
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
