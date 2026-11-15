# Stops the project's downloads as soon as the machine joins a network other than the allowed one.
# Useful when a laptop may switch to a metered connection (for example a phone hotspot) while
# downloads are running, because the downloads stream far more data than they keep.
#
#   powershell -ExecutionPolicy Bypass -File scripts\network_guard.ps1 -Allowed "My office Wi-Fi"
#
# The guard ends by itself when no download is left running.
param(
    [Parameter(Mandatory = $true)][string]$Allowed,
    [string]$Log = "data\network_guard.log",
    [int]$Seconds = 5,
    [int]$Grace = 120
)
$waited = 0
"$(Get-Date -Format s) guard started, allowed network: $Allowed" | Add-Content $Log
while ($true) {
    $names = @(Get-NetConnectionProfile -ErrorAction SilentlyContinue | ForEach-Object { $_.Name })
    # "Identifying..." appears for a few seconds when Wi-Fi reconnects; only a named other network counts,
    # unless the identification lasts longer than $Grace seconds.
    $other = @($names | Where-Object { $_ -notlike $Allowed -and $_ -notlike 'Identifying*' -and $_ })
    $unknown = @($names | Where-Object { $_ -like 'Identifying*' })
    if ($unknown.Count -gt 0 -and $other.Count -eq 0) { $waited += $Seconds } else { $waited = 0 }
    if ($waited -gt $Grace) { $other = $unknown }
    $downloads = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
        Where-Object { $_.CommandLine -match 'eerie_uk\.(download|eobs|ceda)|fetch_era5_wind' })
    if ($other.Count -gt 0) {
        $downloads | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -Confirm:$false }
        "$(Get-Date -Format s) stopped $($downloads.Count) download(s); network: $($other -join ', ')" | Add-Content $Log
        break
    }
    if ($downloads.Count -eq 0) {
        "$(Get-Date -Format s) no downloads running; guard ends" | Add-Content $Log
        break
    }
    Start-Sleep -Seconds $Seconds
}
