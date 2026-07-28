#ifndef AppVersion
  #error AppVersion must be provided by the build script
#endif
#ifndef NumericVersion
  #error NumericVersion must be provided by the build script
#endif
#ifndef SourceDir
  #error SourceDir must be provided by the build script
#endif
#ifndef OutputDir
  #error OutputDir must be provided by the build script
#endif

[Setup]
AppId={{B9ED315F-7DE7-43FA-8B85-7B1FF1ED64A5}
AppName=PourTask
AppVersion={#AppVersion}
AppVerName=PourTask {#AppVersion}
AppPublisher=Pour
AppPublisherURL=https://github.com/pour-soi/PourTask
AppSupportURL=https://github.com/pour-soi/PourTask/issues
DefaultDirName={localappdata}\Programs\PourTask
DefaultGroupName=PourTask
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
OutputDir={#OutputDir}
OutputBaseFilename=PourTask-v{#AppVersion}-Windows-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\icons\PourTask.ico
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName=PourTask {#AppVersion}
UninstallDisplayIcon={app}\PourTask.exe
VersionInfoVersion={#NumericVersion}
VersionInfoCompany=Pour
VersionInfoDescription=PourTask Windows Installer
VersionInfoProductName=PourTask
VersionInfoProductVersion={#NumericVersion}

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "installed.marker"; DestDir: "{app}"; DestName: ".pourtask-installed"; Attribs: hidden; Flags: ignoreversion

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: none; ValueName: "PourTask"; Flags: uninsdeletevalue dontcreatekey

[Icons]
Name: "{autoprograms}\PourTask"; Filename: "{app}\PourTask.exe"; IconFilename: "{app}\PourTask.exe"
Name: "{autodesktop}\PourTask"; Filename: "{app}\PourTask.exe"; IconFilename: "{app}\PourTask.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
Filename: "{app}\PourTask.exe"; Description: "Launch PourTask"; Flags: nowait postinstall skipifsilent
