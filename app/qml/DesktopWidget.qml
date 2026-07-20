import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "theme"
import "components"

ApplicationWindow {
    id: widget
    width: 330; height: 420; visible: false; title: "PourTask Widget"
    flags: Qt.Tool | Qt.FramelessWindowHint
    color: "transparent"
    Rectangle { anchors.fill: parent; radius: Theme.rLarge; color: Theme.elevated; border.color: Theme.border
        ColumnLayout { anchors.fill: parent; anchors.margins: Theme.s16
            Text { text: "Today"; color: Theme.text; font.pixelSize: 18; font.bold: true }
            TextField { Layout.fillWidth: true; placeholderText: strings.quick_add; onAccepted: { appViewModel.addTask(text); text = "" } }
            ListView { Layout.fillWidth: true; Layout.fillHeight: true; model: appViewModel.tasks; spacing: Theme.s8
                delegate: TaskRow { onToggled: value => appViewModel.setCompleted(taskId, value); onOpened: { appViewModel.openDetail(taskId); widget.hide() } }
            }
        }
    }
}
