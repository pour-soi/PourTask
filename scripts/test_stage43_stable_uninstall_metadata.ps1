param(
    [ValidateSet('Automated', 'PrepareInteractive', 'LaunchInteractiveUnpackaged', 'WatchInteractive', 'InspectInteractive', 'VerifyInteractive', 'CleanupInteractive')]
    [string] $Mode = 'Automated',
    [string] $ReproductionRoot,
    [int] $ProcessId
)

$ErrorActionPreference = 'Stop'

function Assert-IsolatedPath([string] $AllowedRoot, [string] $Candidate, [string] $Label) {
    $CanonicalRoot = [IO.Path]::GetFullPath($AllowedRoot).TrimEnd('\')
    $CanonicalCandidate = [IO.Path]::GetFullPath($Candidate)
    if (-not $CanonicalCandidate.StartsWith($CanonicalRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "$Label escapes the isolated regression root."
    }
    $Denied = @(
        (Join-Path $env:LOCALAPPDATA 'PourTask'),
        (Join-Path $env:LOCALAPPDATA 'PourTask-Stage43-StableFixture'),
        (Join-Path $env:LOCALAPPDATA 'Programs\PourTask-Stage43-StableFixture'),
        (Join-Path $env:LOCALAPPDATA 'PourTask-Phase4'),
        (Join-Path $env:LOCALAPPDATA 'Programs\PourTask-Phase4')
    )
    if ($Denied | Where-Object {
        $DeniedPath = [IO.Path]::GetFullPath($_).TrimEnd('\')
        $CanonicalCandidate -eq $DeniedPath -or $CanonicalCandidate.StartsWith($DeniedPath + '\', [StringComparison]::OrdinalIgnoreCase)
    }) { throw "$Label targets a denied Stable Fixture path." }
    for ($Current = Get-Item -LiteralPath $CanonicalRoot -Force; $Current; $Current = $Current.Parent) {
        if ($Current.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "$Label crosses a reparse point." }
    }
    return $CanonicalCandidate
}

function Add-PackageInspectionType {
    if ('StableFixturePackageInspection' -as [type]) { return }
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Text;
public static class StableFixturePackageInspection {
    const uint PROCESS_QUERY_LIMITED_INFORMATION = 0x1000;
    const uint TOKEN_QUERY = 0x0008;
    [DllImport("kernel32.dll", SetLastError=true)] static extern IntPtr OpenProcess(uint access, bool inherit, int processId);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool CloseHandle(IntPtr handle);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode)] static extern int GetPackageFullName(IntPtr process, ref uint length, StringBuilder name);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode)] static extern int GetPackageFamilyName(IntPtr process, ref uint length, StringBuilder name);
    [DllImport("advapi32.dll", SetLastError=true)] static extern bool OpenProcessToken(IntPtr process, uint access, out IntPtr token);
    [DllImport("advapi32.dll", SetLastError=true)] static extern bool GetTokenInformation(IntPtr token, int infoClass, out uint info, uint length, out uint returned);
    static string ReadName(IntPtr process, bool family, out int result) {
        uint length = 0;
        result = family ? GetPackageFamilyName(process, ref length, null) : GetPackageFullName(process, ref length, null);
        if (result == 15700) return null;
        if (result != 122) return null;
        var value = new StringBuilder((int)length);
        result = family ? GetPackageFamilyName(process, ref length, value) : GetPackageFullName(process, ref length, value);
        return result == 0 ? value.ToString() : null;
    }
    public static string Inspect(int processId) {
        IntPtr process = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, false, processId);
        if (process == IntPtr.Zero) throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
        try {
            int fullResult, familyResult;
            string full = ReadName(process, false, out fullResult);
            string family = ReadName(process, true, out familyResult);
            uint elevated = 0, elevationType = 0, returned;
            IntPtr token;
            if (!OpenProcessToken(process, TOKEN_QUERY, out token)) throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
            try {
                if (!GetTokenInformation(token, 20, out elevated, 4, out returned)) throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
                if (!GetTokenInformation(token, 18, out elevationType, 4, out returned)) throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
            } finally { CloseHandle(token); }
            return String.Join("|", fullResult, full ?? "", familyResult, family ?? "", elevated, elevationType);
        } finally { CloseHandle(process); }
    }
}
'@
}

$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path
$InnoCompiler = Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'
if (-not (Test-Path -LiteralPath $InnoCompiler)) { throw 'Inno Setup compiler was not found.' }
if ($Mode -ne 'Automated' -and -not $ReproductionRoot) { throw 'ReproductionRoot is required for interactive modes.' }

$Root = if ($Mode -eq 'Automated') {
    Join-Path $env:TEMP ("PourTask-Stage43-metadata-regression-" + [guid]::NewGuid().ToString('N'))
} else { [IO.Path]::GetFullPath($ReproductionRoot) }
if (-not (Test-Path -LiteralPath $Root)) { New-Item -ItemType Directory -Path $Root | Out-Null }
$null = Assert-IsolatedPath $env:TEMP $Root 'reproduction-root'
$StatePath = Join-Path $Root 'reproduction-state.json'

if ($Mode -in @('LaunchInteractiveUnpackaged', 'WatchInteractive', 'InspectInteractive', 'VerifyInteractive', 'CleanupInteractive')) {
    if (-not (Test-Path -LiteralPath $StatePath)) { throw 'Interactive reproduction state is missing.' }
    $State = Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
    $TestId = $State.testId
} else { $TestId = [guid]::NewGuid().ToString('D').ToUpperInvariant() }
$SentinelToken = if ($State) { [string] $State.sentinelToken } else { [guid]::NewGuid().ToString('N') }

$AppName = "PourTask Stage43 Stable Fixture Metadata Regression $TestId"
$Source = Join-Path $Root 'source'
$Install = Join-Path $Root 'install'
$Data = Join-Path $Root 'data'
$RegistrationRoot = Join-Path $Root 'registrations'
$RegistrationPath = Join-Path $RegistrationRoot 'stable-fixture.synthetic.json'
$Output = Join-Path $Root 'output'
$Logs = Join-Path $Root 'logs'
$UninstallLog = Join-Path $Logs 'uninstall.log'
$StartupIdentity = $AppName
$ShortcutIdentity = $AppName
$UninstallLauncher = Join-Path ([Environment]::GetFolderPath('Programs')) "$ShortcutIdentity.lnk"
$UninstallKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\{$TestId}_is1"
$SentinelRoot = "HKCU:\Software\PourTask-Stage43-UninstallRegression\$TestId"
$SentinelKey = Join-Path $SentinelRoot 'OutsideScope'
$RealStableAppId = 'CE634188-5D2E-4DC9-85EB-851060BB6092'
$RealBetaAppId = 'F927AD06-CC4D-4B73-91D4-74259DC59EF4'

foreach ($Path in @($Source, $Install, $Data, $RegistrationRoot, $RegistrationPath, $Output, $Logs, $UninstallLog, $StatePath)) {
    $null = Assert-IsolatedPath $Root $Path 'controlled-path'
}
if ($TestId -in @($RealStableAppId, $RealBetaAppId)) { throw 'Synthetic AppId matches a real controlled Fixture identity.' }

function Assert-OutsideScopeSentinel {
    if (-not (Test-Path -LiteralPath $SentinelKey)) { throw 'Outside-scope sentinel identity was removed.' }
    $Actual = (Get-ItemProperty -LiteralPath $SentinelKey -Name 'sentinel').sentinel
    if ($Actual -ne $SentinelToken) { throw 'Outside-scope sentinel identity was modified.' }
}

function Assert-UninstallEvidence {
    if (-not (Test-Path -LiteralPath $UninstallLog)) { throw 'Instrumented uninstall log is missing.' }
    $Lines = @(Get-Content -LiteralPath $UninstallLog)
    $Needle = "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Uninstall\{$TestId}_is1"
    $DeletionLines = @($Lines | Where-Object { $_ -like "*Deleting registry key:*$Needle*" })
    if ($DeletionLines.Count -eq 0) { throw 'The exact Stable Fixture ARP deletion was not reached.' }
    if ($Lines | Where-Object { $_ -like '*Deletion failed (*' }) { throw 'The Stable Fixture uninstall log contains a deletion failure.' }
    if (Test-Path -LiteralPath $UninstallKey) { throw 'Synthetic Stable Fixture ARP identity remains.' }
    if (Test-Path -LiteralPath $Install) { throw 'Synthetic Stable Fixture installation remains.' }
    if (Test-Path -LiteralPath $RegistrationPath) { throw 'Synthetic Stable Fixture registration remains.' }
    if ((Get-ItemProperty -LiteralPath 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name $StartupIdentity -ErrorAction SilentlyContinue).$StartupIdentity) {
        throw 'Synthetic Stable Fixture startup identity remains.'
    }
    if (Test-Path -LiteralPath $UninstallLauncher) { throw 'Synthetic Stable Fixture shortcut remains.' }
    Assert-OutsideScopeSentinel
    Write-Output "ARP_DELETE_LOG_LINE=$($DeletionLines[0])"
    Write-Output "ARP_DELETE_ATTEMPTS=$($DeletionLines.Count)"
    Write-Output 'OUTSIDE_SCOPE_SENTINEL=unchanged'
}

if ($Mode -eq 'CleanupInteractive') {
    if (Test-Path -LiteralPath $UninstallKey) { throw 'Refusing cleanup while the synthetic ARP identity remains.' }
    Assert-OutsideScopeSentinel
    if (Test-Path -LiteralPath $SentinelRoot) { Remove-Item -LiteralPath $SentinelRoot -Recurse }
    if (Test-Path -LiteralPath $Root) { Remove-Item -LiteralPath $Root -Recurse }
    Write-Output 'INTERACTIVE_CLEANUP=complete'
    return
}
if ($Mode -eq 'VerifyInteractive') { Assert-UninstallEvidence; Write-Output 'INTERACTIVE_UNINSTALL=verified'; return }
if ($Mode -eq 'WatchInteractive') {
    $OutputPath = Join-Path $Root 'process-inspection.txt'
    $Deadline = [DateTime]::UtcNow.AddSeconds(30)
    do {
        $Candidate = Get-CimInstance Win32_Process | Where-Object {
            $_.Name -eq '_unins.tmp' -and $_.ExecutablePath -and
            $_.ExecutablePath.StartsWith([IO.Path]::GetFullPath($env:TEMP).TrimEnd('\') + '\is-', [StringComparison]::OrdinalIgnoreCase)
        } | Sort-Object CreationDate -Descending | Select-Object -First 1
        if ($Candidate) { break }
        Start-Sleep -Milliseconds 50
    } while ([DateTime]::UtcNow -lt $Deadline)
    if (-not $Candidate) { throw 'Timed out waiting for the Inno second phase.' }
    & $PSCommandPath -Mode InspectInteractive -ReproductionRoot $Root -ProcessId $Candidate.ProcessId |
        Set-Content -LiteralPath $OutputPath
    return
}
if ($Mode -eq 'InspectInteractive') {
    if ($ProcessId -le 0) { throw 'ProcessId is required.' }
    $Process = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId"
    if (-not $Process -or $Process.Name -ne '_unins.tmp') { throw 'The inspected process is not the active Inno second phase.' }
    $CanonicalProcess = [IO.Path]::GetFullPath($Process.ExecutablePath)
    $ExpectedTempPrefix = [IO.Path]::GetFullPath($env:TEMP).TrimEnd('\') + '\is-'
    if (-not $CanonicalProcess.StartsWith($ExpectedTempPrefix, [StringComparison]::OrdinalIgnoreCase)) { throw 'The Inno process escaped the controlled temporary location.' }
    Add-PackageInspectionType
    $Parts = [StableFixturePackageInspection]::Inspect($ProcessId).Split('|')
    $Owner = Invoke-CimMethod -InputObject $Process -MethodName GetOwner
    $HostVisible = Test-Path -LiteralPath $UninstallKey
    Write-Output "PROCESS_ID=$ProcessId"
    Write-Output "PROCESS_PATH=$CanonicalProcess"
    Write-Output "PARENT_PROCESS_ID=$($Process.ParentProcessId)"
    Write-Output "CREATION_TIME=$($Process.CreationDate.ToUniversalTime().ToString('o'))"
    Write-Output "PACKAGE_FULL_NAME_RESULT=$($Parts[0])"
    Write-Output "PACKAGE_FULL_NAME=$($Parts[1])"
    Write-Output "PACKAGE_FAMILY_NAME_RESULT=$($Parts[2])"
    Write-Output "PACKAGE_FAMILY_NAME=$($Parts[3])"
    Write-Output "ELEVATED=$([bool][int]$Parts[4])"
    Write-Output "TOKEN_ELEVATION_TYPE=$($Parts[5])"
    Write-Output "USER=$($Owner.Domain)\$($Owner.User)"
    Write-Output "HOST_ARP_VISIBLE=$HostVisible"
    if ([int]$Parts[0] -eq 15700) {
        Write-Output "PROCESS_CONTEXT_ARP_VISIBLE=$HostVisible"
    } else {
        Write-Output 'PROCESS_CONTEXT_ARP_VISIBLE=requires-package-probe'
    }
    return
}
if ($Mode -eq 'LaunchInteractiveUnpackaged') {
    Add-PackageInspectionType
    $Current = [StableFixturePackageInspection]::Inspect($PID).Split('|')
    if ([int]$Current[0] -ne 15700) { throw "Launcher is packaged (GetPackageFullName=$($Current[0]))." }
    if (Test-Path -LiteralPath $UninstallLog) { Remove-Item -LiteralPath $UninstallLog }
    $Process = Start-Process -FilePath (Join-Path $Install 'unins000.exe') -ArgumentList ('/LOG="' + $UninstallLog + '"') -PassThru
    Write-Output "INTERACTIVE_UNINSTALL_PID=$($Process.Id)"
    Write-Output 'INTERACTIVE_LAUNCH_CONTEXT=unpackaged'
    return
}

New-Item -ItemType Directory -Path $Source, $Data, $RegistrationRoot, $Output, $Logs -Force | Out-Null
Set-Content -LiteralPath (Join-Path $Data 'synthetic-data.txt') -Value 'isolated-stable-fixture-data' -NoNewline
New-Item -ItemType Directory -Path $SentinelKey -Force | Out-Null
Set-ItemProperty -LiteralPath $SentinelKey -Name 'sentinel' -Value $SentinelToken

function Build-And-Install([string] $Version) {
    Set-Content -LiteralPath (Join-Path $Source 'PourTask.exe') -Value $Version -NoNewline
    Set-Content -LiteralPath $RegistrationPath -Value $Version -NoNewline
    & $InnoCompiler "/DAppVersion=$Version" "/DNumericVersion=$Version" "/DSourceDir=$Source" "/DOutputDir=$Output" `
        "/DStage43AppId={{$TestId}" "/DStage43AppName=$AppName" "/DStage43DefaultDir=$Install" `
        "/DStage43RegistrationPath=$RegistrationPath" "/DStage43StartupValueName=$StartupIdentity" `
        "/DStage43ShortcutName=$ShortcutIdentity" "/DStage43UninstallLogPath=$UninstallLog" `
        (Join-Path $ProjectRoot 'packaging\PourTask.Stage43StableFixture.iss') | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Inno compilation failed for $Version." }
    $Installer = Join-Path $Output "PourTask-Stage43-StableFixture-v$Version-Windows-Setup.exe"
    $Installed = Start-Process -FilePath $Installer -ArgumentList '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART' -Wait -PassThru -WindowStyle Hidden
    if ($Installed.ExitCode -ne 0) { throw "Installer failed for $Version." }
}

try {
    Build-And-Install '9.9.9.40'
    Build-And-Install '9.9.9.41'
    Set-ItemProperty -LiteralPath 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name $StartupIdentity -Value 'isolated-stable-fixture-startup'
    $Current = Get-ItemProperty -LiteralPath $UninstallKey
    if ($Current.DisplayName -ne "$AppName 9.9.9.41" -or $Current.DisplayVersion -ne '9.9.9.41') { throw 'Synthetic Stable Fixture metadata is stale.' }
    Assert-OutsideScopeSentinel
    [pscustomobject]@{ testId=$TestId; sentinelToken=$SentinelToken; appName=$AppName; root=$Root; install=$Install; data=$Data; registrationPath=$RegistrationPath; uninstallKey=$UninstallKey; uninstallLog=$UninstallLog; uninstallLauncher=$UninstallLauncher } | ConvertTo-Json | Set-Content -LiteralPath $StatePath -NoNewline
    if ($Mode -eq 'PrepareInteractive') {
        Write-Output "TEST_APP_ID={$TestId}"
        Write-Output "TEST_ROOT=$Root"
        Write-Output "UNINSTALL_LAUNCHER=$UninstallLauncher"
        Write-Output "UNINSTALL_LOG=$UninstallLog"
        Write-Output 'INTERACTIVE_REPRODUCTION=ready'
        return
    }
    Add-PackageInspectionType
    $CurrentContext = [StableFixturePackageInspection]::Inspect($PID).Split('|')
    if ([int]$CurrentContext[0] -ne 15700) { throw "Automated launcher is packaged (GetPackageFullName=$($CurrentContext[0]))." }
    Write-Output 'AUTOMATED_LAUNCH_CONTEXT=unpackaged'
    $Removed = Start-Process -FilePath (Join-Path $Install 'unins000.exe') -ArgumentList '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', "/LOG=$UninstallLog" -Wait -PassThru -WindowStyle Hidden
    if ($Removed.ExitCode -ne 0) { throw 'Automated uninstaller failed.' }
    Assert-UninstallEvidence
    Write-Output 'AUTOMATED_STABLE_FIXTURE_UNINSTALL=passed'
} finally {
    if ($Mode -eq 'Automated') {
        if (Test-Path -LiteralPath $UninstallKey) { Remove-Item -LiteralPath $UninstallKey -Recurse }
        Remove-ItemProperty -LiteralPath 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name $StartupIdentity -ErrorAction SilentlyContinue
        if (Test-Path -LiteralPath $UninstallLauncher) { Remove-Item -LiteralPath $UninstallLauncher }
        if (Test-Path -LiteralPath $SentinelRoot) { Remove-Item -LiteralPath $SentinelRoot -Recurse }
        if (Test-Path -LiteralPath $Root) { Remove-Item -LiteralPath $Root -Recurse }
    }
}
