$ErrorActionPreference = "Continue"

$Tasks = @("Gloc Rloc Loop", "Gloc Oloc Loop")

foreach ($Task in $Tasks) {
    $Item = Get-ScheduledTask -TaskName $Task -ErrorAction SilentlyContinue
    if ($Item) {
        $Info = Get-ScheduledTaskInfo -TaskName $Task
        Write-Host "$Task"
        Write-Host "  state: $($Item.State)"
        Write-Host "  last_run: $($Info.LastRunTime)"
        Write-Host "  last_result: $($Info.LastTaskResult)"
        Write-Host "  next_run: $($Info.NextRunTime)"
    }
    else {
        Write-Host "$Task"
        Write-Host "  state: not registered"
    }
}
