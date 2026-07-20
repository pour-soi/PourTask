from pathlib import Path

project = Path(SPECPATH).parent

a = Analysis(
    [str(project / "main.py")],
    pathex=[str(project)],
    binaries=[],
    datas=[
        (str(project / "app" / "qml"), "app/qml"),
        (str(project / "app" / "database" / "schema.sql"), "app/database"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="PourTask", debug=False, bootloader_ignore_signals=False,
    strip=False, upx=True, console=False,
)
