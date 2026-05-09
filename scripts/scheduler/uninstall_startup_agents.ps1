$ErrorActionPreference = "Continue"

$StartupDir = [Environment]::GetFolderPath("Startup")
$Files = @(
    "Gloc-Rloc-Loop.vbs",
    "Gloc-Oloc-Loop.vbs"
)

foreach ($File in $Files) {
    $Path = Join-Path $StartupDir $File
    if (Test-Path -LiteralPath $Path) {
        Remove-Item -LiteralPath $Path -Force
        Write-Host "removed: $Path"
    }
    else {
        Write-Host "not found: $Path"
    }
}
