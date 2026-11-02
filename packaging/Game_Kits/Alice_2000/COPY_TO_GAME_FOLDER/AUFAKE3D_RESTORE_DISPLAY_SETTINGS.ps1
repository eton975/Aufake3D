# Aufake3D v0.9.0: OPTIONAL one-time Alice 2000 display-setting recovery.
# Restore only saved rendering/video cvars from the pre-A3D2 backup.
# This helper is NEVER invoked by the launcher. Other game settings are retained.
[CmdletBinding()]
param([string]$GameDir = $PSScriptRoot)
$ErrorActionPreference = 'Stop'
$GameDir = [IO.Path]::GetFullPath($GameDir)
$config = Join-Path $GameDir 'base\config.cfg'
$source = "$config.AUFAKE3D_before_A3D2_default.bak"
if (-not [IO.File]::Exists($config)) { throw "Active game configuration not found: $config" }
if (-not [IO.File]::Exists($source)) { throw "Pre-install backup not found: $source" }
$enc = [Text.Encoding]::GetEncoding(28591) # reversible 8-bit mapping
$active = $enc.GetString([IO.File]::ReadAllBytes($config))
$original = $enc.GetString([IO.File]::ReadAllBytes($source))
$pattern = '(?im)^[ \t]*seta?[ \t]+((?:r|vid|gl)_[A-Za-z0-9_]+)[ \t]+(?:(?:"[^"\r\n]*")|[^\r\n \t]+)[^\r\n]*'
$saved = [Text.RegularExpressions.Regex]::Matches($original, $pattern)
if ($saved.Count -eq 0) { throw 'Original backup contains no saved display settings. Active config left untouched.' }
$restore = @{}
foreach ($m in $saved) { $restore[$m.Groups[1].Value.ToLowerInvariant()] = $m.Value }
$new = $active
$nl = if ($active.Contains("`r`n")) { "`r`n" } else { "`n" }
foreach ($name in ($restore.Keys | Sort-Object)) {
    $line = $restore[$name]
    $keyPattern = '(?im)^[ \t]*seta?[ \t]+' + [Text.RegularExpressions.Regex]::Escape($name) + '[ \t]+[^\r\n]*'
    $hits = [Text.RegularExpressions.Regex]::Matches($new, $keyPattern)
    if ($hits.Count -eq 0) {
        if ($new.Length -gt 0 -and -not $new.EndsWith("`n")) { $new += $nl }
        $new += $line + $nl
    } else {
        # Replace from end to start to preserve indices and every unrelated line.
        for ($i = $hits.Count - 1; $i -ge 0; $i--) {
            $m = $hits[$i]
            $new = $new.Substring(0, $m.Index) + $line + $new.Substring($m.Index + $m.Length)
        }
    }
}
if ($new -ceq $active) { Write-Host 'Display settings already match the pre-install backup; nothing changed.'; exit 0 }
# Save the CURRENT game config first. Do not touch the original Aufake3D backup.
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
$before = "$config.AUFAKE3D_before_display_repair_$stamp.bak"
[IO.File]::Copy($config, $before)
$temp = "$config.aufake3d-display-repair.tmp"
try {
    [IO.File]::WriteAllBytes($temp, $enc.GetBytes($new))
    [IO.File]::Copy($temp, $config, $true)
} finally {
    if ([IO.File]::Exists($temp)) { [IO.File]::Delete($temp) }
}
Write-Host "Recovered $($restore.Count) original display options from: $source"
Write-Host "All non-display options (including s_milesdriver) were preserved. Backup of current file: $before"
