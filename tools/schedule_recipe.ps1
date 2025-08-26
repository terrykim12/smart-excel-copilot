param(
  [string]$PythonExe = "python",
  [string]$ProjectDir = "$PSScriptRoot\..",
  [string]$RecipePath = "$ProjectDir\recipes\clean_dedupe_weekly.yaml",
  [string]$TaskName = "SmartExcelCopilot_Weekly",
  [string]$When = "SUNDAYS 08:00"
)

$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument "-m app.cli replay --recipe `"$RecipePath`" --apply" -WorkingDirectory $ProjectDir
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 8am
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Description "SmartExcelCopilot weekly recipe" -Force
Write-Host "✅ Scheduled: $TaskName (Sundays 08:00)"
