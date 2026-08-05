from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import QObject, QTimer
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from app.paths import AppPaths, phase4_test_mode, stage43_stable_fixture_mode

PHASE4_APP_ID = "com.pour.pourtask.phase4"
PHASE4_PROTOCOL_ID = "pourtask-phase4-v1"
MAX_MESSAGE_BYTES = 16 * 1024
HEALTH_PIPE_PATTERN = re.compile(r"^pourtask-phase4-health-[0-9a-f]{32}$")
OPAQUE_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")


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


@dataclass(frozen=True)
class HealthConfiguration:
    pipe_name: str
    attempt_id: str
    request_id: str
    expires_at: datetime

    @classmethod
    def from_environment(cls, environment=None, *, now: datetime | None = None):
        environment = os.environ if environment is None else environment
        now = now or datetime.now(timezone.utc)
        pipe_name = environment.get("POURTASK_PHASE4_HEALTH_PIPE", "")
        attempt_id = environment.get("POURTASK_PHASE4_ATTEMPT_ID", "")
        request_id = environment.get("POURTASK_PHASE4_REQUEST_ID", "")
        if environment.get("POURTASK_PHASE4_PROTOCOL_ID") != PHASE4_PROTOCOL_ID:
            return None
        if not HEALTH_PIPE_PATTERN.fullmatch(pipe_name):
            return None
        if not OPAQUE_ID_PATTERN.fullmatch(attempt_id) or not OPAQUE_ID_PATTERN.fullmatch(request_id):
            return None
        try:
            expires_at = datetime.fromisoformat(environment.get("POURTASK_PHASE4_HEALTH_EXPIRES_AT", "").replace("Z", "+00:00"))
        except ValueError:
            return None
        if expires_at.tzinfo is None or expires_at <= now or (expires_at - now).total_seconds() > 60:
            return None
        return cls(pipe_name, attempt_id, request_id, expires_at)


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
    def __init__(self, executable: Path | None = None, runner=subprocess.Popen, paths: AppPaths | None = None):
        package = "PourUpgrade-Phase4" if test_mode() else "PourUpgrade"
        base = (paths or AppPaths.default()).logical_local_appdata
        default = base / "Programs" / package / "PourUpgrade.exe"
        self.executable, self.runner = Path(executable or default), runner

    def launch_for_pourtask(self) -> tuple[bool, str]:
        if stage43_stable_fixture_mode():
            return False, "Updates are disabled for the isolated Stable Fixture."
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


def prepare_shutdown(request: dict, *, pending_edits: bool | str, save_state) -> dict:
    if pending_edits == "save-failed":
        return {"status": "failed", "errorCode": "task-save-failed"}
    if pending_edits is True or pending_edits == "dirty": return {"status": "requires-user-action"}
    try: saved = bool(save_state())
    except OSError: saved = False
    return {"status": "ready" if saved else "failed",
            "errorCode": None if saved else "state-save-failed"}


def health_report(version: str, launch_mode: str, state_restored: bool,
                  attempt_id: str, request_id: str, process_id: int | None = None) -> dict:
    return {"protocolIdentity": PHASE4_PROTOCOL_ID, "appId": PHASE4_APP_ID,
            "runningVersion": version, "launchMode": launch_mode,
            "stateRestored": bool(state_restored), "processIdentity": "PourTask",
            "processId": process_id or os.getpid(), "attemptId": attempt_id, "requestId": request_id}


def test_mode() -> bool:
    return phase4_test_mode()


def register_test_installation(executable: Path, paths: AppPaths, version: str) -> Path | None:
    if not test_mode() or not (executable.parent / ".pourtask-phase4-installed").is_file():
        return None
    path = paths.registration_root / f"{PHASE4_APP_ID}.json"
    RegistrationStore(path).write(phase4_registration(executable, paths.root, version))
    return path


def _frame(value: dict) -> bytes:
    payload = json.dumps(value, separators=(",", ":")).encode()
    if len(payload) > MAX_MESSAGE_BYTES: raise ValueError("message-too-large")
    return len(payload).to_bytes(4, "little") + payload


class UpdatePipeServer(QObject):
    def __init__(self, pipe_name: str, *, pending_edits, save_state, quit_app,
                 requires_user_action=lambda: None, parent=None):
        super().__init__(parent); self.validator = ShutdownRequestValidator(); self.pending_edits = pending_edits
        self.save_state, self.quit_app = save_state, quit_app
        self.requires_user_action, self.buffers = requires_user_action, {}
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
            response = prepare_shutdown(request, pending_edits=self.pending_edits(), save_state=self.save_state)
        except ValueError as exc:
            response = {"status": "failed", "errorCode": str(exc)}
        self._reply(socket, response)
        if response["status"] == "requires-user-action": QTimer.singleShot(0, self.requires_user_action)
        if response["status"] == "ready": QTimer.singleShot(0, self.quit_app)

    @staticmethod
    def _reply(socket, response):
        socket.write(_frame(response)); socket.flush(); socket.waitForBytesWritten(250); socket.disconnectFromServer()

    def close(self):
        for socket in list(self.buffers):
            socket.abort()
        self.buffers.clear()
        name = self.server.serverName()
        self.server.close()
        if name:
            QLocalServer.removeServer(name)


def send_health(pipe_name: str, report: dict) -> bool:
    socket = QLocalSocket(); socket.connectToServer(pipe_name)
    if not socket.waitForConnected(100): return False
    frame = _frame(report); written = socket.write(frame); socket.flush()
    sent = written == len(frame) and (socket.bytesToWrite() == 0 or socket.waitForBytesWritten(250))
    socket.disconnectFromServer()
    return sent


class HealthSender(QObject):
    def __init__(self, configuration: HealthConfiguration, report: dict, *, sender=send_health,
                 clock=lambda: datetime.now(timezone.utc), parent=None):
        super().__init__(parent)
        self.configuration, self.report, self.sender, self.clock = configuration, report, sender, clock
        self.started = self.sent = False

    def start(self) -> None:
        if self.started:
            return
        self.started = True
        QTimer.singleShot(0, self._attempt)

    def _attempt(self) -> None:
        if self.sent or self.clock() >= self.configuration.expires_at:
            return
        self.sent = bool(self.sender(self.configuration.pipe_name, self.report))
        if not self.sent:
            QTimer.singleShot(100, self._attempt)
