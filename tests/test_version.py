from pathlib import Path

from app import __version__


def test_release_version():
    version_file = Path(__file__).parents[1] / "VERSION"
    assert version_file.read_text(encoding="utf-8").strip() == "1.2.0-beta.1"
    assert __version__ == "1.2.0-beta.1"
