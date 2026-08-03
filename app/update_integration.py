from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import QObject, QTimer
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from app.paths import phase4_local_appdata, phase4_test_mode

PHASE4_APP_ID = "com.pour.pourtask.phase4"
PHASE4_PROTOCOL_ID = "pourtask-phase4-v1"
MAX_MESSAGE_BYTES = 16 * 1024


@dataclass(frozen=True)
class Registration:
    appId: str
    displayName: str
    publisher: str
    currentVersion: str
    installationScope: str
    trustedRepositoryOwner: str
    trustedRepositoryName: str
    releaseChannel: str
    installRoot: str
    mainExecutableIdentity: dict
    helperProcessIdentities: list
    protectedRootMappings: dict
    restartCapabilities: list
    protocolIdentity: str


def phase4_registration(executable: Path, data_root: Path, version: str) -> Registration:
    executable = executable.resolve()
    return Registration(
        PHASE4_APP_ID, "PourTask Phase 4 Test", "Pour", version, "per-user",
        "pour-soi", "PourUpgrade-TestRelease", "phase4-test", str(executable.parent),
        {"relativePath": executable.name, "publisher": "Pour", "identity": "PourTask"},
        [], {"database": str((data_root / "data").resolve()),
             "local-data": str((data_root / "backups").resolve()),
             "settings": str((data_root / "settings.json").resolve())},
        ["foreground", "tray", "none"], PHASE4_PROTOCOL_ID,
    )


class RegistrationStore:
    def __init__(self, path: Path): self.path = Path(path)

    def write(self, registration: Registration) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(asdict(registration), indent=2), encoding="utf-8")
        temporary.replace(self.path)

    def read(self) -> Registration:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if set(data) != set(Registration.__dataclass_fields__):
            raise ValueError("Registration fields are invalid.")
        registration = Registration(**data)
        if registration.appId != PHASE4_APP_ID or registration.protocolIdentity != PHASE4_PROTOCOL_ID:
            raise ValueError("Registration identity is invalid.")
        return registration

    def remove(self) -> None:
        self.path.unlink(missing_ok=True)


class UpdaterLauncher:
    def __init__(self, executable: Path | None = None, runner=subprocess.Popen):
        package = "PourUpgrade-Phase4" if test_mode() else "PourUpgrade"
        base = phase4_local_appdata() if test_mode() else Path(os.environ.get("LOCALAPPDATA", ""))
        default = base / "Programs" / package / "PourUpgrade.exe"
        self.executable, self.runner = Path(executable or default), runner

    def launch_for_pourtask(self) -> tuple[bool, str]:
        if not self.executable.is_file():
            return False, "PourUpgrade is not installed or is unavailable."
        self.runner([str(self.executable), "--focus-app", PHASE4_APP_ID], cwd=str(self.executable.parent))
        return True, "PourUpgrade is handling the update check."


class ShutdownRequestValidator:
    fields = {"appId", "requestId", "targetVersion", "requestedRestartMode", "createdAt",
              "expiresAt", "nonce", "protocolIdentity"}

    def __init__(self): self.consumed = set()

    def validate(self, payload: bytes, *, now: datetime | None = None) -> dict:
        if len(payload) > MAX_MESSAGE_BYTES: raise ValueError("message-too-large")
        try: request = json.loads(payload)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc: raise ValueError("malformed-message") from exc
        if not isinstance(request, dict) or set(request) != self.fields: raise ValueError("malformed-message")
        if request["appId"] != PHASE4_APP_ID: raise ValueError("wrong-app-id")
        if request["protocolIdentity"] != PHASE4_PROTOCOL_ID: raise ValueError("wrong-protocol-identity")
        if request["requestedRestartMode"] not in {"foreground", "tray", "none"}: raise ValueError("invalid-restart-mode")
        if not request["requestId"] or request["requestId"] in self.consumed: raise ValueError("replayed-request")
        try:
            created = datetime.fromisoformat(request["createdAt"].replace("Z", "+00:00"))
            expires = datetime.fromisoformat(request["expiresAt"].replace("Z", "+00:00"))
            nonce = base64.b64decode(request["nonce"], validate=True)
        except (ValueError, TypeError) as exc: raise ValueError("malformed-message") from exc
        now = now or datetime.now(timezone.utc)
        if created > now or expires <= now or expires <= created or (expires - created).total_seconds() > 600:
            raise ValueError("expired-request")
        if len(nonce) < 16: raise ValueError("invalid-nonce")
        self.consumed.add(request["requestId"])
        return request


def prepare_shutdown(request: dict, *, pending_edits: bool, save_state) -> dict:
    if pending_edits: return {"status": "requires-user-action"}
    try: saved = bool(save_state())
    except OSError: saved = False
    return {"status": "ready" if saved else "failed",
            "errorCode": None if saved else "state-save-failed"}


def health_report(version: str, launch_mode: str, state_restored: bool,
                  attempt_id: str, request_id: str) -> dict:
    return {"appId": PHASE4_APP_ID, "runningVersion": version, "launchMode": launch_mode,
            "stateRestored": bool(state_restored), "processIdentity": "PourTask",
            "attemptId": attempt_id, "requestId": request_id}


def test_mode() -> bool:
    return phase4_test_mode()


def register_test_installation(executable: Path, data_root: Path, version: str) -> Path | None:
    if not test_mode() or not (executable.parent / ".pourtask-phase4-installed").is_file():
        return None
    registration_root = os.environ.get("POURUPGRADE_REGISTRATION_ROOT") or str(
        phase4_local_appdata() / "PourUpgrade" / "registrations-test"
    )
    path = Path(registration_root).resolve() / f"{PHASE4_APP_ID}.json"
    RegistrationStore(path).write(phase4_registration(executable, data_root, version))
    return path


def _frame(value: dict) -> bytes:
    payload = json.dumps(value, separators=(",", ":")).encode()
    if len(payload) > MAX_MESSAGE_BYTES: raise ValueError("message-too-large")
    return len(payload).to_bytes(4, "little") + payload


class UpdatePipeServer(QObject):
    def __init__(self, pipe_name: str, *, pending_edits, save_state, quit_app, parent=None):
        super().__init__(parent); self.validator = ShutdownRequestValidator(); self.pending_edits = pending_edits
        self.save_state, self.quit_app, self.buffers = save_state, quit_app, {}
        self.server = QLocalServer(self); QLocalServer.removeServer(pipe_name)
        if not self.server.listen(pipe_name): raise RuntimeError("Phase 4 control pipe could not be opened.")
        self.server.newConnection.connect(self._accept)

    def _accept(self):
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection(); self.buffers[socket] = bytearray()
            socket.readyRead.connect(lambda current=socket: self._read(current))
            socket.disconnected.connect(lambda current=socket: self.buffers.pop(current, None))

    def _read(self, socket):
        buffer = self.buffers[socket]; buffer.extend(bytes(socket.readAll()))
        if len(buffer) < 4: return
        length = int.from_bytes(buffer[:4], "little")
        if length <= 0 or length > MAX_MESSAGE_BYTES:
            self._reply(socket, {"status": "failed", "errorCode": "malformed-message"}); return
        if len(buffer) < length + 4: return
        try:
            request = self.validator.validate(bytes(buffer[4:4 + length]))
            response = prepare_shutdown(request, pending_edits=bool(self.pending_edits()), save_state=self.save_state)
        except ValueError as exc:
            response = {"status": "failed", "errorCode": str(exc)}
        self._reply(socket, response)
        if response["status"] == "ready": QTimer.singleShot(0, self.quit_app)

    @staticmethod
    def _reply(socket, response):
        socket.write(_frame(response)); socket.flush(); socket.waitForBytesWritten(250); socket.disconnectFromServer()


def send_health(pipe_name: str, report: dict) -> bool:
    socket = QLocalSocket(); socket.connectToServer(pipe_name)
    if not socket.waitForConnected(1000): return False
    socket.write(_frame(report)); socket.flush(); sent = socket.waitForBytesWritten(1000); socket.disconnectFromServer()
    return sent
