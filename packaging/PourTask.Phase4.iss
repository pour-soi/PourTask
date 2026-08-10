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

#ifndef Phase4AppId
  #define Phase4AppId "{{F927AD06-CC4D-4B73-91D4-74259DC59EF4}"
#endif
#ifndef Phase4DefaultDir
  #define Phase4DefaultDir "{localappdata}\Programs\PourTask-Phase4"
#endif
#define Phase4UninstallKey "Software\Microsoft\Windows\CurrentVersion\Uninstall\" + Phase4AppId + "_is1"

[Setup]
AppId={#Phase4AppId}
AppName=PourTask Phase 4 Test
AppVersion={#AppVersion}
AppPublisher=Pour
DefaultDirName={#Phase4DefaultDir}
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

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: none; ValueName: "PourTask Phase4 Beta Fixture"; Flags: uninsdeletevalue dontcreatekey

[Icons]
Name: "{autoprograms}\PourTask Phase 4 Test"; Filename: "{app}\PourTask.exe"; Parameters: "--pourupgrade-phase4-test --pourupgrade-tray"

[UninstallDelete]
Type: files; Name: "{localappdata}\PourUpgrade\registrations-test\com.pour.pourtask.phase4.json"

[Code]
procedure VerifyPhase4UninstallMetadata;
var
  DisplayName: String;
  DisplayVersion: String;
begin
  if not RegKeyExists(HKCU64, '{#Phase4UninstallKey}') then
    RaiseException('The controlled Phase 4 uninstall identity is missing.');

  if (not RegQueryStringValue(HKCU64, '{#Phase4UninstallKey}', 'DisplayName', DisplayName)) or
     (DisplayName <> 'PourTask Phase 4 Test {#AppVersion}') then
  begin
    if not RegWriteStringValue(HKCU64, '{#Phase4UninstallKey}', 'DisplayName',
      'PourTask Phase 4 Test {#AppVersion}') then
      RaiseException('The controlled Phase 4 uninstall DisplayName could not be corrected.');
  end;

  if (not RegQueryStringValue(HKCU64, '{#Phase4UninstallKey}', 'DisplayVersion', DisplayVersion)) or
     (DisplayVersion <> '{#AppVersion}') then
  begin
    if not RegWriteStringValue(HKCU64, '{#Phase4UninstallKey}', 'DisplayVersion', '{#AppVersion}') then
      RaiseException('The controlled Phase 4 uninstall DisplayVersion could not be corrected.');
  end;

  if (not RegQueryStringValue(HKCU64, '{#Phase4UninstallKey}', 'DisplayName', DisplayName)) or
     (DisplayName <> 'PourTask Phase 4 Test {#AppVersion}') or
     (not RegQueryStringValue(HKCU64, '{#Phase4UninstallKey}', 'DisplayVersion', DisplayVersion)) or
     (DisplayVersion <> '{#AppVersion}') then
    RaiseException('The controlled Phase 4 uninstall metadata could not be verified.');
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
    VerifyPhase4UninstallMetadata;
end;
