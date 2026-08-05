from pathlib import Path
import runpy

project = Path(SPECPATH).parent
resolver = runpy.run_path(str(project / "scripts" / "build_version.py"))
resolved = resolver["resolve_build_version"](project)
version_source = resolver["bundled_version_source"](project, resolved)
version = resolved.semver
version_tuple = resolved.version_tuple
print(f"BUILD_SEMVER={resolved.semver}")
print(f"BUILD_NUMERIC_VERSION={resolved.numeric}")
version_info = project / "build" / "PourTask-version-info.txt"
version_info.parent.mkdir(parents=True, exist_ok=True)
version_info.write_text(
    f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={version_tuple},
    prodvers={version_tuple},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [
          StringStruct('CompanyName', 'Pour'),
          StringStruct('FileDescription', 'PourTask'),
          StringStruct('FileVersion', '{version}'),
          StringStruct('InternalName', 'PourTask'),
          StringStruct('LegalCopyright', 'Copyright (c) PourTask contributors'),
          StringStruct('OriginalFilename', 'PourTask.exe'),
          StringStruct('ProductName', 'PourTask'),
          StringStruct('ProductVersion', '{version}')
        ]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
""",
    encoding="utf-8",
)

a = Analysis(
    [str(project / "main.py")],
    pathex=[str(project)],
    binaries=[],
    datas=[
        (str(project / "app" / "qml"), "app/qml"),
        (str(project / "app" / "database" / "schema.sql"), "app/database"),
        (str(project / "assets" / "icons"), "assets/icons"),
        (str(version_source), "."),
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
    version=str(version_info),
    icon=str(project / "assets" / "icons" / "PourTask.ico"),
)
collect = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="PourTask",
)
