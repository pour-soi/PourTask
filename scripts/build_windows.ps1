$ErrorActionPreference = 'Stop'

$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
$Spec = Join-Path $ProjectRoot 'packaging\PourTask.spec'
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

New-Item -ItemType Directory -Path $PortableDirectory | Out-Null
Copy-Item -Path (Join-Path $BuiltDirectory '*') -Destination $PortableDirectory -Recurse
Copy-Item -LiteralPath (Join-Path $ProjectRoot 'LICENSE') -Destination $PortableDirectory
Copy-Item -LiteralPath (Join-Path $ProjectRoot 'README.md') -Destination $PortableDirectory
Copy-Item -LiteralPath (Join-Path $ProjectRoot 'README_CN.md') -Destination $PortableDirectory
Copy-Item -LiteralPath (Join-Path $ProjectRoot 'CHANGELOG.md') -Destination $PortableDirectory

Compress-Archive -LiteralPath $PortableDirectory -DestinationPath $ZipPath -CompressionLevel Optimal
$Hash = (Get-FileHash -LiteralPath $ZipPath -Algorithm SHA256).Hash.ToLowerInvariant()
"$Hash  $PackageName.zip" | Set-Content -LiteralPath $ChecksumPath -Encoding ascii

Write-Output "VERSION=$Version"
Write-Output "PORTABLE_DIRECTORY=$PortableDirectory"
Write-Output "ZIP=$ZipPath"
Write-Output "SHA256=$Hash"
