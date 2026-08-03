from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from app.paths import phase4_test_mode, stage43_stable_fixture_mode


class SingleInstanceGuard(QObject):
    activateRequested = Signal()

    def __init__(self, name: str | None = None):
        super().__init__()
        identity = (
            "PourTask.Stage43StableFixture.SingleInstance" if stage43_stable_fixture_mode()
            else "PourTask.Phase4.SingleInstance" if phase4_test_mode()
            else "PourTask.SingleInstance"
        )
        self.name = name or identity
        self.server = QLocalServer(self)
        self._connections = []
        self._client_socket = None

    def acquire(self, startup_launch: bool = False) -> bool:
        socket = QLocalSocket(self)
        self._client_socket = socket
        socket.connectToServer(self.name)
        if socket.waitForConnected(250):
            socket.write(b"startup" if startup_launch else b"activate")
            socket.flush()
            socket.waitForBytesWritten(250)
            return False

        QLocalServer.removeServer(self.name)
        if not self.server.listen(self.name):
            return False
        self.server.newConnection.connect(self._accept_connections)
        return True

    def _accept_connections(self) -> None:
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            self._connections.append(socket)
            socket.readyRead.connect(lambda connection=socket: self._consume(connection))
            socket.disconnected.connect(
                lambda connection=socket: self._forget(connection)
            )
            if not socket.bytesAvailable():
                socket.waitForReadyRead(100)
            if socket.bytesAvailable():
                self._consume(socket)

    def _consume(self, socket) -> None:
        message = bytes(socket.readAll())
        if message == b"activate":
            self.activateRequested.emit()
        socket.disconnectFromServer()

    def _forget(self, socket) -> None:
        if socket in self._connections:
            self._connections.remove(socket)
