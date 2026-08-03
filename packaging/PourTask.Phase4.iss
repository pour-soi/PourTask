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
AppId={{F927AD06-CC4D-4B73-91D4-74259DC59EF4}
AppName=PourTask Phase 4 Test
AppVersion={#AppVersion}
AppPublisher=Pour
DefaultDirName={localappdata}\Programs\PourTask-Phase4
DefaultGroupName=PourTask Phase 4 Test
DisableProgramGroupPage=yes
OutputDir={#OutputDir}
OutputBaseFilename=PourTask-Phase4-v{#AppVersion}-Windows-Setup
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName=PourTask Phase 4 Test {#AppVersion}
UninstallDisplayIcon={app}\PourTask.exe
VersionInfoVersion={#NumericVersion}
VersionInfoCompany=Pour
VersionInfoDescription=PourTask Phase 4 Test Installer
VersionInfoProductName=PourTask Phase 4 Test
VersionInfoProductVersion={#NumericVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\icons\PourTask.ico

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "installed.marker"; DestDir: "{app}"; DestName: ".pourtask-phase4-installed"; Attribs: hidden; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\PourTask Phase 4 Test"; Filename: "{app}\PourTask.exe"; Parameters: "--pourupgrade-phase4-test --pourupgrade-tray"

[UninstallDelete]
Type: files; Name: "{localappdata}\PourUpgrade\registrations-test\com.pour.pourtask.phase4.json"
