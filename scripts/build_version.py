"""Resolve the single version contract used by PourTask package builds.

SemVer text is retained in the executable string metadata, bundled VERSION,
runtime version, and registration. Windows fixed/installer versions use
``major.minor.patch.beta_number`` (zero for a stable version).
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path


VERSION_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:-beta\.(\d+))?$")


@dataclass(frozen=True)
class BuildVersion:
    semver: str
    numeric: str
    version_tuple: tuple[int, int, int, int]
    phase4: bool


def resolve_build_version(project: Path, environment=None) -> BuildVersion:
    environment = os.environ if environment is None else environment
    phase4 = environment.get("POURTASK_PHASE4_BUILD") == "1"
    override = environment.get("POURTASK_PHASE4_VERSION", "").strip()
    if override and not phase4:
        raise ValueError("POURTASK_PHASE4_VERSION requires POURTASK_PHASE4_BUILD=1")
    if phase4 and not override:
        raise ValueError("POURTASK_PHASE4_BUILD=1 requires POURTASK_PHASE4_VERSION")

    semver = override if phase4 else (Path(project) / "VERSION").read_text(encoding="utf-8").strip()
    match = VERSION_PATTERN.fullmatch(semver)
    if not match:
        raise ValueError(f"Unsupported PourTask version: {semver}")
    if phase4 and not match.group(4):
        raise ValueError("Phase 4 builds require a beta prerelease version")

    values = tuple(int(value or 0) for value in match.groups())
    return BuildVersion(semver, ".".join(str(value) for value in values), values, phase4)


def bundled_version_source(project: Path, version: BuildVersion) -> Path:
    project = Path(project)
    if not version.phase4:
        return project / "VERSION"
    path = project / "build" / "phase4" / "VERSION"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(version.semver, encoding="utf-8")
    return path


if __name__ == "__main__":
    resolution = resolve_build_version(Path(__file__).resolve().parents[1])
    print(json.dumps(asdict(resolution), separators=(",", ":")))
