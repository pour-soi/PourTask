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

[Setup]
AppId={{CE634188-5D2E-4DC9-85EB-851060BB6092}
AppName=PourTask Stage 4.3 Stable Fixture
AppVersion={#AppVersion}
AppPublisher=Pour
DefaultDirName={localappdata}\Programs\PourTask-Stage43-StableFixture
DefaultGroupName=PourTask Stage 4.3 Stable Fixture
DisableProgramGroupPage=yes
OutputDir={#OutputDir}
OutputBaseFilename=PourTask-Stage43-StableFixture-v{#AppVersion}-Windows-Setup
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName=PourTask Stage 4.3 Stable Fixture {#AppVersion}
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
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: none; ValueName: "PourTask Stage43 Stable Fixture"; Flags: uninsdeletevalue dontcreatekey

[Icons]
Name: "{autoprograms}\PourTask Stage 4.3 Stable Fixture"; Filename: "{app}\PourTask.exe"; Parameters: "--stage43-stable-fixture --startup"
