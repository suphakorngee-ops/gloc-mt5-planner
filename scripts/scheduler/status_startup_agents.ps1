$StartupDir = [Environment]::GetFolderPath("Startup")
$Files = @(
    "Gloc-Rloc-Loop.vbs",
    "Gloc-Oloc-Loop.vbs"
)

Write-Host "Startup folder: $StartupDir"
foreach ($File in $Files) {
    $Path = Join-Path $StartupDir $File
    if (Test-Path -LiteralPath $Path) {
        Write-Host "${File}: installed"
    }
    else {
        Write-Host "${File}: not installed"
    }
}
