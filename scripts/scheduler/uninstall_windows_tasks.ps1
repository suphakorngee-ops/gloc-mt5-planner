$ErrorActionPreference = "Continue"

$Tasks = @("Gloc Rloc Loop", "Gloc Oloc Loop")

foreach ($Task in $Tasks) {
    if (Get-ScheduledTask -TaskName $Task -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $Task -Confirm:$false
        Write-Host "removed: $Task"
    }
    else {
        Write-Host "not found: $Task"
    }
}
