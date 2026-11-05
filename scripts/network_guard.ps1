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
    [int]$Seconds = 5
)
"$(Get-Date -Format s) guard started, allowed network: $Allowed" | Add-Content $Log
while ($true) {
    $names = @(Get-NetConnectionProfile -ErrorAction SilentlyContinue | ForEach-Object { $_.Name })
    $other = @($names | Where-Object { $_ -notlike $Allowed })
    $downloads = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
        Where-Object { $_.CommandLine -match 'eerie_uk\.(download|eobs)' })
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
