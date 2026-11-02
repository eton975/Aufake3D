# Aufake3D v0.8.18 - one-time A3D2 initial preference (Windows PowerShell 5.1+).
# This runs once per installed kit, then NEVER rewrites the player's selected provider.
# We intentionally DO NOT use +set s_milesdriver a3d2, autoexec.cfg, or a DLL alias.
# The game keeps full control of provider switching and its normal config saves.
param(
    [Parameter(Mandatory=$true)][ValidateSet('Alice2000','Alice2011')][string]$Game,
    [Parameter(Mandatory=$true)][string]$GameDir
)
$ErrorActionPreference = 'Stop'
$GameDir = [IO.Path]::GetFullPath($GameDir)
$marker = Join-Path $GameDir 'AUFAKE3D_A3D2_INITIAL_DEFAULT_DONE.txt'
if ([IO.File]::Exists($marker)) { exit 0 }

try {
    $targets = New-Object 'System.Collections.Generic.List[string]'
    $localConfig = Join-Path $GameDir 'base\config.cfg'
    if ($Game -eq 'Alice2000') {
        $targets.Add($localConfig)
    } else {
        # The 2011 release normally saves its active config under Documents\My Games.
        # Do not touch a second base config: duplicate preferences can
        # override the user's later in-game choice on future launches.
        $docs = [Environment]::GetFolderPath('MyDocuments')
        if ([string]::IsNullOrWhiteSpace($docs)) {
            throw 'Windows Documents location is unavailable'
        }
        $userConfig = Join-Path $docs "My Games\American McGee's Alice\config.cfg"
        $targets.Add($userConfig)
    }

    foreach ($target in $targets) {
        $parent = [IO.Path]::GetDirectoryName($target)
        if (-not [IO.Directory]::Exists($parent)) {
            # Do not create unexpected folders in an incomplete game installation.
            if ($target -eq $localConfig -and -not [IO.Directory]::Exists((Join-Path $GameDir 'base'))) {
                throw "Game base folder is missing: $parent"
            }
            [IO.Directory]::CreateDirectory($parent) | Out-Null
        }
        $exists = [IO.File]::Exists($target)
        if ($exists) {
            $bytes = [IO.File]::ReadAllBytes($target)
            # Preserve original bytes, including non-ASCII contents, without requiring
            # a particular Windows ANSI code page. Refuse unexpected UTF-16 text.
            if ($bytes.Length -ge 2 -and (($bytes[0] -eq 0xff -and $bytes[1] -eq 0xfe) -or
                ($bytes[0] -eq 0xfe -and $bytes[1] -eq 0xff))) {
                throw "Unsupported UTF-16 config (left untouched): $target"
            }
            $encoding = [Text.Encoding]::GetEncoding(28591) # byte-preserving Latin-1
            $raw = $encoding.GetString($bytes)
            $backup = "$target.AUFAKE3D_before_A3D2_default.bak"
            if (-not [IO.File]::Exists($backup)) { [IO.File]::Copy($target, $backup) }
        } else {
            $encoding = [Text.Encoding]::ASCII
            $raw = ''
        }
        # Update all active saved selections, not commented lines. Keep all other
        # game settings unchanged. New settings use the engine's standard seta syntax.
        $pattern = '(?im)^[ \t]*seta?[ \t]+s_milesdriver[ \t]+(?:"[^"\r\n]*"|[^\r\n \t]+)[^\r\n]*'
        if ([Text.RegularExpressions.Regex]::IsMatch($raw, $pattern)) {
            $updated = [Text.RegularExpressions.Regex]::Replace($raw, $pattern, 'seta s_milesdriver "a3d2"')
        } else {
            $sep = if ($raw.EndsWith("`r`n") -or $raw.EndsWith("`n")) { '' } else { "`r`n" }
            $updated = $raw + $sep + 'seta s_milesdriver "a3d2"' + "`r`n"
        }
        if ($raw -cne $updated -or -not $exists) {
            $temp = "$target.aufake3d-writing.tmp"
            $outBytes = $encoding.GetBytes($updated)
            [IO.File]::WriteAllBytes($temp, $outBytes)
            try {
                [IO.File]::Copy($temp, $target, $true)
            } finally {
                if ([IO.File]::Exists($temp)) { [IO.File]::Delete($temp) }
            }
        }
    }
    # Write marker last: subsequent launches preserve in-game Miles/Dolby choices.
    [IO.File]::WriteAllText($marker,
        'A3D2 was set as the initial sound provider once. Delete this marker ONLY if you intentionally want to repeat the one-time config setup.' + [Environment]::NewLine,
        [Text.Encoding]::ASCII)
    Write-Host 'Aufake3D: initial A3D2 preference saved (one time only).'
    exit 0
} catch {
    Write-Warning ('Aufake3D could not set the initial A3D2 preference: ' + $_.Exception.Message)
    Write-Warning 'No startup provider will be forced. Choose A3D2 in the game settings if necessary.'
    exit 1
}
