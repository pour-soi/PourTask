$ErrorActionPreference = 'Stop'

$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path
$InnoCompiler = Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'
if (-not (Test-Path -LiteralPath $InnoCompiler)) { throw 'Inno Setup compiler was not found.' }

$TestId = [guid]::NewGuid().ToString('D').ToUpperInvariant()
$Root = Join-Path $env:TEMP ("PourTask-Phase4-metadata-regression-" + [guid]::NewGuid().ToString('N'))
$Source = Join-Path $Root 'source'
$Install = Join-Path $Root 'install'
$Output = Join-Path $Root 'output'
$UninstallKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\{$TestId}_is1"

function Build-And-Install([string] $SemVer, [string] $NumericVersion) {
    New-Item -ItemType Directory -Path $Source, $Output -Force | Out-Null
    Set-Content -LiteralPath (Join-Path $Source 'PourTask.exe') -Value $SemVer -NoNewline
    Set-Content -LiteralPath (Join-Path $Source 'runtime-version.txt') -Value $SemVer -NoNewline
    Set-Content -LiteralPath (Join-Path $Source 'registration-version.json') -Value ('{"currentVersion":"' + $SemVer + '"}') -NoNewline
    & $InnoCompiler "/DAppVersion=$SemVer" "/DNumericVersion=$NumericVersion" `
        "/DSourceDir=$Source" "/DOutputDir=$Output" "/DPhase4AppId={{$TestId}" `
        "/DPhase4DefaultDir=$Install" (Join-Path $ProjectRoot 'packaging\PourTask.Phase4.iss') | Out-Null
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

    $Uninstaller = Join-Path $Install 'unins000.exe'
    $Process = Start-Process -FilePath $Uninstaller -ArgumentList '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART' -Wait -PassThru -WindowStyle Hidden
    if ($Process.ExitCode -ne 0) { throw "Uninstaller failed with exit code $($Process.ExitCode)." }
    if (Test-Path -LiteralPath $UninstallKey) { throw 'Test uninstall identity remains.' }
    if (Test-Path -LiteralPath $Install) { throw 'Test installation root remains.' }
    Write-Output 'OLD_VERSION=9.9.9-beta.40'
    Write-Output 'NEW_VERSION=9.9.9-beta.41'
    Write-Output 'UNINSTALL_IDENTITIES=1'
    Write-Output 'CLEANUP=complete'
}
finally {
    if (Test-Path -LiteralPath $UninstallKey) { Remove-Item -LiteralPath $UninstallKey -Recurse }
    if (Test-Path -LiteralPath $Root) { Remove-Item -LiteralPath $Root -Recurse }
}
