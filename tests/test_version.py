from app import __version__


def test_release_version():
    assert __version__ == "1.1.0"
