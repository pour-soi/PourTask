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
    pyz, a.scripts, [],
    name="PourTask", debug=False, bootloader_ignore_signals=False,
    strip=False, upx=True, console=False, exclude_binaries=True,
)
collect = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="PourTask",
)
