$ErrorActionPreference = 'Stop'

$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
$Spec = Join-Path $ProjectRoot 'packaging\PourTask.spec'
$InstallerSpec = Join-Path $ProjectRoot 'packaging\PourTask.iss'
$Dist = Join-Path $ProjectRoot 'dist'
$Release = Join-Path $ProjectRoot 'release'

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Project virtual environment not found: $Python"
}

$Version = (& $Python -c 'from app.version import __version__; print(__version__)').Trim()
if (-not $Version) {
    throw 'Unable to resolve the PourTask version.'
}

& $Python -m PyInstaller --noconfirm --clean $Spec
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE."
}

$BuiltDirectory = Join-Path $Dist 'PourTask'
$PackageName = "PourTask-v$Version-Windows"
$PortableDirectory = Join-Path $Release $PackageName
$ZipPath = Join-Path $Release "$PackageName.zip"
$ChecksumPath = "$ZipPath.sha256"
$InstallerName = "$PackageName-Setup.exe"
$InstallerPath = Join-Path $Release $InstallerName
$InstallerChecksumPath = "$InstallerPath.sha256"

if (-not (Test-Path -LiteralPath (Join-Path $BuiltDirectory 'PourTask.exe'))) {
    throw "Expected packaged executable was not created: $BuiltDirectory"
}
if (-not $PortableDirectory.StartsWith("$Release\", [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to prepare a portable directory outside the release folder: $PortableDirectory"
}

New-Item -ItemType Directory -Force -Path $Release | Out-Null
if (Test-Path -LiteralPath $PortableDirectory) {
    Remove-Item -LiteralPath $PortableDirectory -Recurse -Force
}
if (Test-Path -LiteralPath $ZipPath) {
    Remove-Item -LiteralPath $ZipPath -Force
}
if (Test-Path -LiteralPath $ChecksumPath) {
    Remove-Item -LiteralPath $ChecksumPath -Force
}
if (Test-Path -LiteralPath $InstallerPath) {
    Remove-Item -LiteralPath $InstallerPath -Force
}
if (Test-Path -LiteralPath $InstallerChecksumPath) {
    Remove-Item -LiteralPath $InstallerChecksumPath -Force
}

New-Item -ItemType Directory -Path $PortableDirectory | Out-Null
Copy-Item -Path (Join-Path $BuiltDirectory '*') -Destination $PortableDirectory -Recurse
Copy-Item -LiteralPath (Join-Path $ProjectRoot 'LICENSE') -Destination $PortableDirectory
Copy-Item -LiteralPath (Join-Path $ProjectRoot 'README.md') -Destination $PortableDirectory
Copy-Item -LiteralPath (Join-Path $ProjectRoot 'README_CN.md') -Destination $PortableDirectory
Copy-Item -LiteralPath (Join-Path $ProjectRoot 'CHANGELOG.md') -Destination $PortableDirectory

Compress-Archive -LiteralPath $PortableDirectory -DestinationPath $ZipPath -CompressionLevel Optimal
$Hash = (Get-FileHash -LiteralPath $ZipPath -Algorithm SHA256).Hash.ToLowerInvariant()
"$Hash  $PackageName.zip" | Set-Content -LiteralPath $ChecksumPath -Encoding ascii

$InnoCompiler = Get-Command ISCC.exe -ErrorAction SilentlyContinue
if (-not $InnoCompiler) {
    $LocalInnoCompiler = Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'
    $ProgramFilesInnoCompiler = Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe'
    if (Test-Path -LiteralPath $LocalInnoCompiler) {
        $InnoCompiler = Get-Item -LiteralPath $LocalInnoCompiler
    } elseif (Test-Path -LiteralPath $ProgramFilesInnoCompiler) {
        $InnoCompiler = Get-Item -LiteralPath $ProgramFilesInnoCompiler
    } else {
        throw 'Inno Setup 6 compiler (ISCC.exe) was not found.'
    }
}

$VersionParts = [regex]::Match($Version, '^(\d+)\.(\d+)\.(\d+)(?:-beta\.(\d+))?$')
if (-not $VersionParts.Success) {
    throw "Unsupported PourTask version for installer metadata: $Version"
}
$PrereleaseNumber = if ($VersionParts.Groups[4].Success) {
    $VersionParts.Groups[4].Value
} else {
    '0'
}
$NumericVersion = '{0}.{1}.{2}.{3}' -f $VersionParts.Groups[1].Value,
    $VersionParts.Groups[2].Value,
    $VersionParts.Groups[3].Value,
    $PrereleaseNumber

$InnoCompilerPath = if ($InnoCompiler.Source) {
    $InnoCompiler.Source
} else {
    $InnoCompiler.FullName
}

& $InnoCompilerPath `
    "/DAppVersion=$Version" `
    "/DNumericVersion=$NumericVersion" `
    "/DSourceDir=$PortableDirectory" `
    "/DOutputDir=$Release" `
    $InstallerSpec
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup failed with exit code $LASTEXITCODE."
}
if (-not (Test-Path -LiteralPath $InstallerPath)) {
    throw "Expected installer was not created: $InstallerPath"
}
$InstallerHash = (Get-FileHash -LiteralPath $InstallerPath -Algorithm SHA256).Hash.ToLowerInvariant()
"$InstallerHash  $InstallerName" | Set-Content -LiteralPath $InstallerChecksumPath -Encoding ascii

Write-Output "VERSION=$Version"
Write-Output "PORTABLE_DIRECTORY=$PortableDirectory"
Write-Output "ZIP=$ZipPath"
Write-Output "SHA256=$Hash"
Write-Output "INSTALLER=$InstallerPath"
Write-Output "INSTALLER_SHA256=$InstallerHash"
