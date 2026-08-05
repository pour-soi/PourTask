from __future__ import annotations

import ctypes
import os
import sys
from dataclasses import dataclass
from pathlib import Path


_NO_PACKAGE = 15700
_INSUFFICIENT_BUFFER = 122
_KF_FLAG_NO_PACKAGE_REDIRECTION = 0x00010000


class _Guid(ctypes.Structure):
    _fields_ = [
        ("data1", ctypes.c_ulong),
        ("data2", ctypes.c_ushort),
        ("data3", ctypes.c_ushort),
        ("data4", ctypes.c_ubyte * 8),
    ]


_LOCAL_APPDATA = _Guid(
    0xF1B32785, 0x6FBA, 0x4FCF,
    (ctypes.c_ubyte * 8)(0x9D, 0x55, 0x7B, 0x8E, 0x7F, 0x15, 0x70, 0x91),
)


def stage43_stable_fixture_mode() -> bool:
    marker = Path(sys.executable).resolve().parent / ".pourtask-stage43-stable-fixture"
    return "--stage43-stable-fixture" in sys.argv or marker.is_file()


def phase4_test_mode() -> bool:
    marker = Path(sys.executable).resolve().parent / ".pourtask-phase4-installed"
    return os.environ.get("POURTASK_PHASE4_TEST") == "1" or "--pourupgrade-phase4-test" in sys.argv or marker.is_file()


def _windows_known_local_appdata() -> Path:
    pointer = ctypes.c_void_p()
    result = ctypes.windll.shell32.SHGetKnownFolderPath(
        ctypes.byref(_LOCAL_APPDATA), _KF_FLAG_NO_PACKAGE_REDIRECTION, None, ctypes.byref(pointer)
    )
    if result:
        raise OSError(result, "Logical Local AppData is unavailable")
    try:
        return Path(ctypes.wstring_at(pointer))
    finally:
        ctypes.windll.ole32.CoTaskMemFree(pointer)


def _windows_package_family() -> str | None:
    length = ctypes.c_uint(0)
    result = ctypes.windll.kernel32.GetCurrentPackageFamilyName(ctypes.byref(length), None)
    if result == _NO_PACKAGE:
        return None
    if result != _INSUFFICIENT_BUFFER:
        raise OSError(result, "Windows package identity is unavailable")
    value = ctypes.create_unicode_buffer(length.value)
    result = ctypes.windll.kernel32.GetCurrentPackageFamilyName(ctypes.byref(length), value)
    if result:
        raise OSError(result, "Windows package identity is unavailable")
    return value.value


def _canonical(path: Path | str) -> Path:
    value = str(path)
    if not value or "%" in value or "$" in value:
        raise ValueError("unprovable-local-appdata-path")
    if value.startswith(("\\\\", "\\\\?\\", "\\\\.\\")):
        raise ValueError("network-or-device-path-not-owned")
    if any(part in {".", ".."} for part in value.replace("/", "\\").split("\\")):
        raise ValueError("path-traversal-not-owned")
    candidate = Path(value)
    if not candidate.is_absolute():
        raise ValueError("relative-path-not-owned")
    return Path(os.path.abspath(candidate))


def _same_or_child(path: Path, root: Path) -> bool:
    candidate = str(path).rstrip("\\/").casefold()
    parent = str(root).rstrip("\\/").casefold()
    return candidate == parent or candidate.startswith(parent + os.sep.casefold())


def _has_reparse(path: Path) -> bool:
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        if not current.exists():
            continue
        if current.is_symlink() or (hasattr(current, "is_junction") and current.is_junction()):
            return True
    return False


@dataclass(frozen=True)
class LocalAppDataResolution:
    logical_root: Path
    observed_environment_root: Path | None
    package_family: str | None
    package_cache_root: Path | None
    storage_root: Path


class LocalAppDataResolver:
    def __init__(self, *, environment=None, platform_name: str | None = None,
                 known_folder=None, package_family=None, reparse_checker=None):
        self.environment = os.environ if environment is None else environment
        self.platform_name = sys.platform if platform_name is None else platform_name
        self.known_folder = known_folder or _windows_known_local_appdata
        self.package_family = package_family or _windows_package_family
        self.reparse_checker = reparse_checker or _has_reparse

    def resolve(self) -> LocalAppDataResolution:
        observed_value = self.environment.get("LOCALAPPDATA")
        observed = _canonical(observed_value) if observed_value else None
        if self.platform_name != "win32":
            root = observed or _canonical(Path.home() / "AppData" / "Local")
            return LocalAppDataResolution(root, observed, None, None, root)

        logical = _canonical(self.known_folder())
        family = self.package_family()
        if family is None:
            return LocalAppDataResolution(logical, observed, None, None, logical)
        if not family or family in {".", ".."} or "\\" in family or "/" in family:
            raise ValueError("invalid-package-family")
        package_cache = _canonical(logical / "Packages" / family / "LocalCache" / "Local")
        if observed is None or observed != package_cache:
            raise ValueError("unowned-package-localcache")
        return LocalAppDataResolution(logical, observed, family, package_cache, package_cache)

    def fixture_override(self, value: str, *, identity: str,
                         resolution: LocalAppDataResolution, require_identity_name: bool = True) -> Path:
        candidate = _canonical(value)
        if self.reparse_checker(candidate):
            raise ValueError("fixture-reparse-root-not-owned")
        denied = [resolution.logical_root / "PourTask"]
        if resolution.storage_root != resolution.logical_root:
            denied.append(resolution.storage_root / "PourTask")
        other = (
            resolution.storage_root / "PourTask-Stage43-StableFixture"
            if identity == "phase4" else resolution.storage_root / "PourTask-Phase4"
        )
        if any(_same_or_child(candidate, root) for root in [*denied, other]):
            raise ValueError("fixture-root-not-owned")
        expected_name = "PourTask-Phase4" if identity == "phase4" else "PourTask-Stage43-StableFixture"
        if require_identity_name and candidate.name.casefold() != expected_name.casefold():
            raise ValueError("fixture-identity-root-not-owned")
        return candidate


@dataclass(frozen=True)
class AppPaths:
    root: Path
    logical_local_appdata: Path
    storage_local_appdata: Path
    registration_root: Path

    @classmethod
    def default(cls, resolver: LocalAppDataResolver | None = None) -> "AppPaths":
        resolver = resolver or LocalAppDataResolver()
        resolution = resolver.resolve()
        environment = resolver.environment
        stable_fixture = stage43_stable_fixture_mode()
        phase4_fixture = phase4_test_mode()
        if stable_fixture:
            override = environment.get("POURTASK_STAGE43_STABLE_DATA_ROOT")
            root = resolver.fixture_override(override, identity="stable-fixture", resolution=resolution) if override else (
                resolution.storage_root / "PourTask-Stage43-StableFixture"
            )
        elif phase4_fixture:
            override = environment.get("POURTASK_PHASE4_DATA_ROOT")
            root = resolver.fixture_override(override, identity="phase4", resolution=resolution) if override else (
                resolution.storage_root / "PourTask-Phase4"
            )
        else:
            root = resolution.storage_root / "PourTask"

        registration = resolution.storage_root / "PourUpgrade" / "registrations-test"
        registration_override = environment.get("POURUPGRADE_REGISTRATION_ROOT")
        if registration_override and phase4_fixture:
            registration = resolver.fixture_override(
                registration_override, identity="phase4", resolution=resolution,
                require_identity_name=False,
            )
        if (stable_fixture or phase4_fixture) and resolver.reparse_checker(_canonical(root)):
            raise ValueError("fixture-reparse-root-not-owned")
        return cls(_canonical(root), resolution.logical_root, resolution.storage_root, _canonical(registration))

    @property
    def data(self) -> Path: return self.root / "data"
    @property
    def database(self) -> Path: return self.data / "pourtask.db"
    @property
    def backups(self) -> Path: return self.root / "backups"
    @property
    def logs(self) -> Path: return self.root / "logs"
    @property
    def settings(self) -> Path: return self.root / "settings.json"

    def ensure(self) -> None:
        for path in (self.data, self.backups, self.logs):
            path.mkdir(parents=True, exist_ok=True)
