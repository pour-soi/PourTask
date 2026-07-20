$ErrorActionPreference = 'Stop'
& "$PSScriptRoot\..\.venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean "$PSScriptRoot\..\packaging\PourTask.spec"
