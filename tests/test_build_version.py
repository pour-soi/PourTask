from pathlib import Path

import pytest

from app.update_integration import phase4_registration
from scripts.build_version import bundled_version_source, resolve_build_version


def project(tmp_path, version="1.2.0"):
    (tmp_path / "VERSION").write_text(version, encoding="utf-8")
    return tmp_path


def test_phase4_override_without_build_mode_fails(tmp_path):
    with pytest.raises(ValueError, match="requires POURTASK_PHASE4_BUILD=1"):
        resolve_build_version(project(tmp_path), {"POURTASK_PHASE4_VERSION": "1.2.0-beta.1"})


def test_phase4_mode_without_version_fails(tmp_path):
    with pytest.raises(ValueError, match="requires POURTASK_PHASE4_VERSION"):
        resolve_build_version(project(tmp_path), {"POURTASK_PHASE4_BUILD": "1"})


@pytest.mark.parametrize("version", ["1.2.0", "1.2.0-rc.1", "invalid"])
def test_phase4_requires_valid_beta_prerelease(tmp_path, version):
    with pytest.raises(ValueError):
        resolve_build_version(project(tmp_path), {
            "POURTASK_PHASE4_BUILD": "1", "POURTASK_PHASE4_VERSION": version,
        })


def test_phase4_beta_resolution_and_bundled_version(tmp_path):
    resolved = resolve_build_version(project(tmp_path), {
        "POURTASK_PHASE4_BUILD": "1", "POURTASK_PHASE4_VERSION": "1.2.0-beta.1",
    })
    source = bundled_version_source(tmp_path, resolved)
    assert (resolved.semver, resolved.numeric, resolved.version_tuple) == (
        "1.2.0-beta.1", "1.2.0.1", (1, 2, 0, 1),
    )
    assert source.read_text(encoding="utf-8") == "1.2.0-beta.1"


def test_stable_resolution_is_unchanged(tmp_path):
    resolved = resolve_build_version(project(tmp_path), {})
    assert (resolved.semver, resolved.numeric, resolved.phase4) == ("1.2.0", "1.2.0.0", False)
    assert bundled_version_source(tmp_path, resolved) == tmp_path / "VERSION"


def test_registration_preserves_prerelease_semver(tmp_path):
    registration = phase4_registration(tmp_path / "beta" / "PourTask.exe", tmp_path / "data", "1.2.0-beta.1")
    assert registration.currentVersion == "1.2.0-beta.1"


def test_fixture_installers_keep_distinct_numeric_identity_contracts():
    root = Path(__file__).parents[1] / "packaging"
    beta = (root / "PourTask.Phase4.iss").read_text(encoding="utf-8")
    stable = (root / "PourTask.Stage43StableFixture.iss").read_text(encoding="utf-8")
    assert "VersionInfoVersion={#NumericVersion}" in beta
    assert "VersionInfoVersion={#NumericVersion}" in stable
    assert "F927AD06-CC4D-4B73-91D4-74259DC59EF4" in beta
    assert "CE634188-5D2E-4DC9-85EB-851060BB6092" in stable


def test_phase4_build_script_binds_installer_to_resolved_version():
    script = (Path(__file__).parents[1] / "scripts" / "build_phase4_fixture.ps1").read_text(encoding="utf-8")
    assert "build_version.py" in script
    assert "InstallerInfo.FileVersion.Trim() -ne $resolved.numeric" in script
    assert "InstallerInfo.ProductVersion.Trim() -ne $resolved.numeric" in script
    assert "PourTask Phase 4 Test" in script
