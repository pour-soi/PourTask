$ErrorActionPreference = 'Stop'

$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
$OutputRoot = Join-Path $env:TEMP 'PourTask-Phase4-corrected-build'
if (Test-Path -LiteralPath $OutputRoot) { throw "Output root already exists: $OutputRoot" }

$resolved = (& $Python (Join-Path $PSScriptRoot 'build_version.py') | ConvertFrom-Json)
New-Item -ItemType Directory -Path $OutputRoot | Out-Null
& $Python -m PyInstaller --noconfirm --clean (Join-Path $ProjectRoot 'packaging\PourTask.spec')
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE" }

$Package = Join-Path $OutputRoot 'package'
Copy-Item -LiteralPath (Join-Path $ProjectRoot 'dist\PourTask') -Destination $Package -Recurse
$Executable = Join-Path $Package 'PourTask.exe'
$BundledVersion = (Get-Content -LiteralPath (Join-Path $Package '_internal\VERSION') -Raw).Trim()
$ExecutableInfo = (Get-Item -LiteralPath $Executable).VersionInfo
foreach ($actual in @($ExecutableInfo.FileVersion, $ExecutableInfo.ProductVersion, $BundledVersion)) {
    if ($actual.Trim() -ne $resolved.semver) { throw "Packaged version mismatch: $actual" }
}

$InnoCompiler = Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'
if (-not (Test-Path -LiteralPath $InnoCompiler)) { throw "Inno Setup compiler not found: $InnoCompiler" }
$InstallerOutput = Join-Path $OutputRoot 'installer'
New-Item -ItemType Directory -Path $InstallerOutput | Out-Null
& $InnoCompiler "/DAppVersion=$($resolved.semver)" "/DNumericVersion=$($resolved.numeric)" `
    "/DSourceDir=$Package" "/DOutputDir=$InstallerOutput" `
    (Join-Path $ProjectRoot 'packaging\PourTask.Phase4.iss')
if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed with exit code $LASTEXITCODE" }

$Installer = Join-Path $InstallerOutput "PourTask-Phase4-v$($resolved.semver)-Windows-Setup.exe"
$InstallerInfo = (Get-Item -LiteralPath $Installer).VersionInfo
if ($InstallerInfo.FileVersion.Trim() -ne $resolved.numeric -or
    $InstallerInfo.ProductVersion.Trim() -ne $resolved.numeric) {
    throw "Installer numeric version is not bound to $($resolved.semver)"
}
if ($InstallerInfo.ProductName.Trim() -ne 'PourTask Phase 4 Test') {
    throw "Unexpected installer product identity: $($InstallerInfo.ProductName)"
}
Write-Output "INTENDED_SEMVER=$($resolved.semver)"
Write-Output "NUMERIC_INSTALLER_VERSION=$($resolved.numeric)"
Write-Output "EXECUTABLE_FILE_VERSION=$($ExecutableInfo.FileVersion.Trim())"
Write-Output "EXECUTABLE_PRODUCT_VERSION=$($ExecutableInfo.ProductVersion.Trim())"
Write-Output "BUNDLED_RUNTIME_VERSION=$BundledVersion"
Write-Output "INSTALLER_PRODUCT_NAME=$($InstallerInfo.ProductName.Trim())"
Write-Output "UNINSTALL_DISPLAY_NAME=PourTask Phase 4 Test $($resolved.semver)"
Write-Output "UNINSTALL_DISPLAY_VERSION=$($resolved.semver)"
Write-Output "INSTALLER=$Installer"
Write-Output "INSTALLER_SIZE=$((Get-Item -LiteralPath $Installer).Length)"
Write-Output "INSTALLER_SHA256=$((Get-FileHash -LiteralPath $Installer -Algorithm SHA256).Hash)"
