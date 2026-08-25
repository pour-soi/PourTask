#ifndef AppVersion
  #error AppVersion must be provided
#endif
#ifndef NumericVersion
  #error NumericVersion must be provided
#endif
#ifndef SourceDir
  #error SourceDir must be provided
#endif
#ifndef OutputDir
  #error OutputDir must be provided
#endif
#ifndef Stage43AppId
  #define Stage43AppId "{{CE634188-5D2E-4DC9-85EB-851060BB6092}"
#endif
#ifndef Stage43AppName
  #define Stage43AppName "PourTask Stage 4.3 Stable Fixture"
#endif
#ifndef Stage43DefaultDir
  #define Stage43DefaultDir "{localappdata}\Programs\PourTask-Stage43-StableFixture"
#endif
#ifndef Stage43StartupValueName
  #define Stage43StartupValueName "PourTask Stage43 Stable Fixture"
#endif
#ifndef Stage43ShortcutName
  #define Stage43ShortcutName "PourTask Stage 4.3 Stable Fixture"
#endif

[Setup]
AppId={#Stage43AppId}
AppName={#Stage43AppName}
AppVersion={#AppVersion}
AppPublisher=Pour
DefaultDirName={#Stage43DefaultDir}
DefaultGroupName={#Stage43ShortcutName}
DisableProgramGroupPage=yes
OutputDir={#OutputDir}
OutputBaseFilename=PourTask-Stage43-StableFixture-v{#AppVersion}-Windows-Setup
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName={#Stage43AppName} {#AppVersion}
UninstallDisplayIcon={app}\PourTask.exe
VersionInfoVersion={#NumericVersion}
VersionInfoCompany=Pour
VersionInfoDescription=PourTask Stage 4.3 Stable Fixture Installer
VersionInfoProductName=PourTask Stage 4.3 Stable Fixture
VersionInfoProductVersion={#NumericVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\icons\PourTask.ico

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "installed.marker"; DestDir: "{app}"; DestName: ".pourtask-stage43-stable-fixture"; Attribs: hidden; Flags: ignoreversion

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: none; ValueName: "{#Stage43StartupValueName}"; Flags: uninsdeletevalue dontcreatekey

[Icons]
#ifdef Stage43UninstallLogPath
Name: "{autoprograms}\{#Stage43ShortcutName}"; Filename: "{uninstallexe}"; Parameters: "/LOG=""{#Stage43UninstallLogPath}"""
#else
Name: "{autoprograms}\{#Stage43ShortcutName}"; Filename: "{app}\PourTask.exe"; Parameters: "--stage43-stable-fixture --startup"
#endif

#ifdef Stage43RegistrationPath
[UninstallDelete]
Type: files; Name: "{#Stage43RegistrationPath}"
#endif
