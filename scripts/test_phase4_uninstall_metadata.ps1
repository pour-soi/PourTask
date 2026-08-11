param(
    [string] $IsolationValidationRoot,
    [string] $IsolationValidationPath,
    [ValidateSet('Automated', 'PrepareInteractive', 'LaunchInteractiveUnpackaged', 'VerifyInteractive', 'CleanupInteractive')]
    [string] $Mode = 'Automated',
    [string] $ReproductionRoot
)

$ErrorActionPreference = 'Stop'

function Assert-IsolatedPath([string] $AllowedRoot, [string] $Candidate, [string] $Label) {
    $CanonicalRoot = [IO.Path]::GetFullPath($AllowedRoot).TrimEnd('\')
    $CanonicalCandidate = [IO.Path]::GetFullPath($Candidate)
    if (-not $CanonicalCandidate.StartsWith($CanonicalRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "$Label escapes the isolated regression root."
    }
    $Denied = @(
        (Join-Path $env:LOCALAPPDATA 'PourUpgrade\registrations-test'),
        (Join-Path $env:LOCALAPPDATA 'PourTask-Phase4'),
        (Join-Path $env:LOCALAPPDATA 'Programs\PourTask-Phase4')
    )
    if ($Denied | Where-Object { $CanonicalCandidate.StartsWith([IO.Path]::GetFullPath($_).TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase) -or $CanonicalCandidate -eq [IO.Path]::GetFullPath($_).TrimEnd('\') }) {
        throw "$Label targets a live Phase 4 path."
    }
    return $CanonicalCandidate
}

function Assert-UnpackagedProcess {
    if (-not ('Phase4PackageIdentity' -as [type])) {
        Add-Type -TypeDefinition @'
using System.Runtime.InteropServices;
using System.Text;
public static class Phase4PackageIdentity {
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode)]
    public static extern int GetCurrentPackageFullName(ref uint packageFullNameLength, StringBuilder packageFullName);
}
'@
    }
    [uint32] $Length = 0
    $Result = [Phase4PackageIdentity]::GetCurrentPackageFullName([ref] $Length, $null)
    $AppModelErrorNoPackage = 15700
    if ($Result -ne $AppModelErrorNoPackage) {
        throw "Physical uninstall launch context is packaged (GetCurrentPackageFullName=$Result)."
    }
}

if ($IsolationValidationRoot -or $IsolationValidationPath) {
    if (-not $IsolationValidationRoot -or -not $IsolationValidationPath) { throw 'Both validation paths are required.' }
    Write-Output (Assert-IsolatedPath $IsolationValidationRoot $IsolationValidationPath 'validation-path')
    return
}

$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path
$InnoCompiler = Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'
if (-not (Test-Path -LiteralPath $InnoCompiler)) { throw 'Inno Setup compiler was not found.' }

if ($Mode -ne 'Automated' -and -not $ReproductionRoot) {
    throw 'ReproductionRoot is required for interactive modes.'
}
$Root = if ($Mode -eq 'Automated') {
    Join-Path $env:TEMP ("PourTask-Phase4-metadata-regression-" + [guid]::NewGuid().ToString('N'))
} else {
    Assert-IsolatedPath $env:TEMP $ReproductionRoot 'reproduction-root'
}
$StatePath = Join-Path $Root 'reproduction-state.json'

if ($Mode -in @('LaunchInteractiveUnpackaged', 'VerifyInteractive', 'CleanupInteractive')) {
    if (-not (Test-Path -LiteralPath $StatePath)) { throw 'Interactive reproduction state is missing.' }
    $State = Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
    $TestId = $State.testId
} else {
    $TestId = [guid]::NewGuid().ToString('D').ToUpperInvariant()
}

$SyntheticAppId = "com.pour.pourtask.phase4.synthetic.$($TestId.ToLowerInvariant())"
$Source = Join-Path $Root 'source'
$Install = Join-Path $Root 'install'
$Data = Join-Path $Root 'data'
$Registrations = Join-Path $Root 'registrations'
$Output = Join-Path $Root 'output'
$RegistrationPath = Join-Path $Registrations "$SyntheticAppId.json"
$StartupIdentity = "PourTask Phase4 Metadata Regression $TestId"
$ShortcutIdentity = "PourTask Phase4 Metadata Regression $TestId"
$SimulatedLiveRoot = Join-Path $Root 'simulated-live-registration'
$SimulatedLiveRegistration = Join-Path $SimulatedLiveRoot 'com.pour.pourtask.phase4.json'
$Logs = Join-Path $Root 'logs'
$UninstallLog = Join-Path $Logs 'uninstall.log'
$UninstallLauncher = Join-Path ([Environment]::GetFolderPath('Programs')) "$ShortcutIdentity.lnk"
$UninstallKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\{$TestId}_is1"

foreach ($ControlledPath in @($Source, $Install, $Data, $Registrations, $Output, $RegistrationPath, $SimulatedLiveRegistration, $Logs, $UninstallLog, $StatePath)) {
    $null = Assert-IsolatedPath $Root $ControlledPath 'controlled-path'
}
if (-not $UninstallLauncher.StartsWith([Environment]::GetFolderPath('Programs') + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Instrumented uninstall shortcut escaped the current-user Start Menu.'
}
if ($SyntheticAppId -eq 'com.pour.pourtask.phase4') { throw 'Synthetic application identity is not isolated.' }

function Assert-UninstallEvidence {
    if (-not (Test-Path -LiteralPath $UninstallLog)) { throw 'Instrumented uninstall log is missing.' }
    $LogLines = @(Get-Content -LiteralPath $UninstallLog)
    $Needle = "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Uninstall\{$TestId}_is1"
    $DeletionLines = @($LogLines | Where-Object { $_ -like "*Deleting registry key:*$Needle*" })
    if ($DeletionLines.Count -eq 0) { throw 'The exact ARP deletion was not reached.' }
    if ($LogLines | Where-Object { $_ -like '*Deletion failed (*' }) { throw 'The uninstall log contains a registry deletion failure.' }
    if (Test-Path -LiteralPath $UninstallKey) { throw 'Test uninstall identity remains.' }
    if (Test-Path -LiteralPath $Install) { throw 'Test installation root remains.' }
    if (Test-Path -LiteralPath $RegistrationPath) { throw 'Synthetic registration remains.' }
    Write-Output "ARP_DELETE_LOG_LINE=$($DeletionLines[0])"
    Write-Output "ARP_DELETE_ATTEMPTS=$($DeletionLines.Count)"
}

if ($Mode -eq 'CleanupInteractive') {
    if (Test-Path -LiteralPath $UninstallKey) { throw 'Refusing cleanup while the isolated ARP identity remains.' }
    if (Test-Path -LiteralPath $Root) { Remove-Item -LiteralPath $Root -Recurse }
    Write-Output 'INTERACTIVE_CLEANUP=complete'
    return
}

if ($Mode -eq 'VerifyInteractive') {
    Assert-UninstallEvidence
    Write-Output 'INTERACTIVE_UNINSTALL=verified'
    return
}

if ($Mode -eq 'LaunchInteractiveUnpackaged') {
    Assert-UnpackagedProcess
    $Uninstaller = Join-Path $Install 'unins000.exe'
    if (-not (Test-Path -LiteralPath $Uninstaller)) { throw 'Interactive reproduction uninstaller is missing.' }
    if (Test-Path -LiteralPath $UninstallLog) { Remove-Item -LiteralPath $UninstallLog }
    $Process = Start-Process -FilePath $Uninstaller -ArgumentList ('/LOG="' + $UninstallLog + '"') -PassThru
    Write-Output "INTERACTIVE_UNINSTALL_PID=$($Process.Id)"
    Write-Output 'INTERACTIVE_LAUNCH_CONTEXT=unpackaged'
    return
}

New-Item -ItemType Directory -Path $Data, $Registrations, $SimulatedLiveRoot, $Logs -Force | Out-Null
Set-Content -LiteralPath $SimulatedLiveRegistration -Value 'live-registration-preservation-sentinel' -NoNewline
$LiveSentinelHash = (Get-FileHash -LiteralPath $SimulatedLiveRegistration -Algorithm SHA256).Hash

function Build-And-Install([string] $SemVer, [string] $NumericVersion) {
    New-Item -ItemType Directory -Path $Source, $Output -Force | Out-Null
    Set-Content -LiteralPath (Join-Path $Source 'PourTask.exe') -Value $SemVer -NoNewline
    Set-Content -LiteralPath (Join-Path $Source 'runtime-version.txt') -Value $SemVer -NoNewline
    @{ appId = $SyntheticAppId; currentVersion = $SemVer; dataRoot = $Data } | ConvertTo-Json | Set-Content -LiteralPath $RegistrationPath -NoNewline
    Copy-Item -LiteralPath $RegistrationPath -Destination (Join-Path $Source 'registration-version.json') -Force
    & $InnoCompiler "/DAppVersion=$SemVer" "/DNumericVersion=$NumericVersion" `
        "/DSourceDir=$Source" "/DOutputDir=$Output" "/DPhase4AppId={{$TestId}" `
        "/DPhase4DefaultDir=$Install" "/DPhase4RegistrationPath=$RegistrationPath" `
        "/DPhase4StartupValueName=$StartupIdentity" "/DPhase4ShortcutName=$ShortcutIdentity" `
        "/DPhase4UninstallLogPath=$UninstallLog" `
        (Join-Path $ProjectRoot 'packaging\PourTask.Phase4.iss') | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Inno compilation failed for $SemVer." }
    $Installer = Join-Path $Output "PourTask-Phase4-v$SemVer-Windows-Setup.exe"
    $Process = Start-Process -FilePath $Installer -ArgumentList '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART' -Wait -PassThru -WindowStyle Hidden
    if ($Process.ExitCode -ne 0) { throw "Installer failed for $SemVer with exit code $($Process.ExitCode)." }
}

try {
    Build-And-Install '9.9.9-beta.40' '9.9.9.40'
    $Old = Get-ItemProperty -LiteralPath $UninstallKey
    if ($Old.DisplayVersion -ne '9.9.9-beta.40') { throw 'Older metadata was not installed.' }

    Build-And-Install '9.9.9-beta.41' '9.9.9.41'
    $Current = Get-ItemProperty -LiteralPath $UninstallKey
    if ($Current.DisplayName -ne 'PourTask Phase 4 Test 9.9.9-beta.41') { throw 'DisplayName was not refreshed.' }
    if ($Current.DisplayVersion -ne '9.9.9-beta.41') { throw 'DisplayVersion was not refreshed.' }
    if ((Get-Content -LiteralPath (Join-Path $Install 'runtime-version.txt') -Raw) -ne '9.9.9-beta.41') { throw 'Runtime version is stale.' }
    if ((Get-Content -LiteralPath (Join-Path $Install 'registration-version.json') -Raw) -notmatch '9\.9\.9-beta\.41') { throw 'Registration version is stale.' }
    if ((Get-Content -LiteralPath (Join-Path $Install 'registration-version.json') -Raw) -notmatch [regex]::Escape($SyntheticAppId)) { throw 'Synthetic application identity is stale.' }

    [pscustomobject]@{
        testId = $TestId
        syntheticAppId = $SyntheticAppId
        root = $Root
        install = $Install
        registrationPath = $RegistrationPath
        uninstallKey = $UninstallKey
        uninstallLog = $UninstallLog
        uninstallLauncher = $UninstallLauncher
    } | ConvertTo-Json | Set-Content -LiteralPath $StatePath -NoNewline

    if ($Mode -eq 'PrepareInteractive') {
        if (-not (Test-Path -LiteralPath $UninstallLauncher)) { throw 'Instrumented uninstall launcher is missing.' }
        Write-Output "TEST_APP_ID={$TestId}"
        Write-Output "TEST_ROOT=$Root"
        Write-Output "UNINSTALL_LAUNCHER=$UninstallLauncher"
        Write-Output "UNINSTALL_LOG=$UninstallLog"
        Write-Output 'INTERACTIVE_REPRODUCTION=ready'
        return
    }

    $Uninstaller = Join-Path $Install 'unins000.exe'
    $Process = Start-Process -FilePath $Uninstaller -ArgumentList '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', "/LOG=$UninstallLog" -Wait -PassThru -WindowStyle Hidden
    if ($Process.ExitCode -ne 0) { throw "Uninstaller failed with exit code $($Process.ExitCode)." }
    Assert-UninstallEvidence
    if (-not (Test-Path -LiteralPath $SimulatedLiveRegistration)) { throw 'Simulated live registration was deleted.' }
    if ((Get-FileHash -LiteralPath $SimulatedLiveRegistration -Algorithm SHA256).Hash -ne $LiveSentinelHash) { throw 'Simulated live registration was modified.' }
    Write-Output 'OLD_VERSION=9.9.9-beta.40'
    Write-Output 'NEW_VERSION=9.9.9-beta.41'
    Write-Output 'UNINSTALL_IDENTITIES=1'
    Write-Output "SYNTHETIC_APP_ID=$SyntheticAppId"
    Write-Output 'LIVE_REGISTRATION_SENTINEL=preserved'
    Write-Output 'CLEANUP=complete'
}
finally {
    if ($Mode -eq 'Automated') {
        if (Test-Path -LiteralPath $UninstallKey) { Remove-Item -LiteralPath $UninstallKey -Recurse }
        if (Test-Path -LiteralPath $Root) { Remove-Item -LiteralPath $Root -Recurse }
    }
}
