# PowerShell script to set up scheduled jobs on Windows
# Sets up:
# 1. Hourly GA4 token generation (runs every hour)
# 2. Daily sync at 12:00 AM IST (6:30 PM UTC / 18:30 UTC) every day

$TokenTaskName = "McRAE_GA4_Token_Generation"
$SyncTaskName = "McRAE_Daily_Sync_Job"
$TokenScriptPath = Join-Path $PSScriptRoot "generate_ga4_token.py"
$SyncScriptPath = Join-Path $PSScriptRoot "daily_sync_job.py"
$PythonPath = (Get-Command python).Source
$WorkingDir = $PSScriptRoot

Write-Host "Setting up scheduled jobs..." -ForegroundColor Green
Write-Host "Python: $PythonPath" -ForegroundColor Cyan
Write-Host "Working Directory: $WorkingDir" -ForegroundColor Cyan
Write-Host ""

# Create logs directory if it doesn't exist
$LogsDir = Join-Path $PSScriptRoot "logs"
if (-not (Test-Path $LogsDir)) {
    New-Item -ItemType Directory -Path $LogsDir | Out-Null
}

# Setup 1: Hourly GA4 Token Generation
if (Test-Path $TokenScriptPath) {
    Write-Host "Setting up GA4 token generation job (hourly)..." -ForegroundColor Cyan
    
    # Remove existing task if it exists
    $existingTokenTask = Get-ScheduledTask -TaskName $TokenTaskName -ErrorAction SilentlyContinue
    if ($existingTokenTask) {
        Write-Host "Removing existing token task..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TokenTaskName -Confirm:$false
    }
    
    # Create action (run Python script)
    $tokenAction = New-ScheduledTaskAction -Execute $PythonPath -Argument "`"$TokenScriptPath`"" -WorkingDirectory $WorkingDir
    
    # Create trigger (hourly)
    $tokenTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date).ToString("HH:mm") -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Days 9999)
    
    # Create settings
    $tokenSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    
    # Create principal
    $tokenPrincipal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest
    
    # Register the task
    try {
        Register-ScheduledTask -TaskName $TokenTaskName -Action $tokenAction -Trigger $tokenTrigger -Settings $tokenSettings -Principal $tokenPrincipal -Description "Hourly GA4 token generation for McRAE Analytics" | Out-Null
        Write-Host "[SUCCESS] GA4 token generation job scheduled (hourly)!" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Failed to create token generation task: $_" -ForegroundColor Red
    }
} else {
    Write-Host "[WARNING] generate_ga4_token.py not found - skipping token generation task" -ForegroundColor Yellow
}

Write-Host ""

# Setup 2: Daily Sync Job
Write-Host "Setting up daily sync job..." -ForegroundColor Cyan

# Remove existing task if it exists
$existingSyncTask = Get-ScheduledTask -TaskName $SyncTaskName -ErrorAction SilentlyContinue
if ($existingSyncTask) {
    Write-Host "Removing existing sync task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $SyncTaskName -Confirm:$false
}

# Create action (run Python script)
$syncAction = New-ScheduledTaskAction -Execute $PythonPath -Argument "`"$SyncScriptPath`"" -WorkingDirectory $WorkingDir

# Create trigger (daily at 12:00 AM local time)
# Note: Adjust time based on your server's timezone
# IST is UTC+5:30, so 12:00 AM IST = 6:30 PM UTC
$syncTrigger = New-ScheduledTaskTrigger -Daily -At "12:00AM"

# Create settings
$syncSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Create principal
$syncPrincipal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest

# Register the task
try {
    Register-ScheduledTask -TaskName $SyncTaskName -Action $syncAction -Trigger $syncTrigger -Settings $syncSettings -Principal $syncPrincipal -Description "Daily sync job for McRAE Analytics - Syncs AgencyAnalytics, GA4, and Scrunch AI data at 12 AM IST" | Out-Null
    Write-Host "[SUCCESS] Daily sync job scheduled!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Details:" -ForegroundColor Cyan
    if (Test-Path $TokenScriptPath) {
        Write-Host "  GA4 Token Generation: Every hour"
        Write-Host "    Task Name: $TokenTaskName"
        Write-Host "    Script: generate_ga4_token.py"
    }
    Write-Host "  Daily Sync: Daily at 12:00 AM"
    Write-Host "    Task Name: $SyncTaskName"
    Write-Host "    Script: daily_sync_job.py"
    Write-Host ""
    Write-Host "To verify, run:" -ForegroundColor Yellow
    if (Test-Path $TokenScriptPath) {
        Write-Host "  Get-ScheduledTask -TaskName $TokenTaskName" -ForegroundColor Yellow
    }
    Write-Host "  Get-ScheduledTask -TaskName $SyncTaskName" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To test manually, run:" -ForegroundColor Yellow
    if (Test-Path $TokenScriptPath) {
        Write-Host "  python generate_ga4_token.py" -ForegroundColor Yellow
    }
    Write-Host "  python daily_sync_job.py" -ForegroundColor Yellow
} catch {
    Write-Host "[ERROR] Failed to create scheduled task: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "You may need to run PowerShell as Administrator" -ForegroundColor Yellow
    exit 1
}

