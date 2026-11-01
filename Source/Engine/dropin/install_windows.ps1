<#
Application-local installation of the unofficial A3D compatibility DLLs.
Uses only files adjacent to this script. No administrator or global registry
changes. Refuses to overwrite *any* preexisting file; original game untouched.
The manifest's COM activation still requires Windows/Wine runtime validation.
#>
param(
 [Parameter(Mandatory=$true)][string]$Game,
 [ValidateSet('alice','quake3')][string]$Kind = 'alice',
 [switch]$PatchAlice
)
$ErrorActionPreference = 'Stop'
$gamePath = (Resolve-Path -LiteralPath $Game).Path
$dir = Split-Path -Parent $gamePath
$name = Split-Path -Leaf $gamePath
if ([IO.Path]::GetExtension($name).ToLowerInvariant() -ne '.exe') { throw 'Provide a 32-bit game .exe' }
if ($PatchAlice -and ($Kind -ne 'alice' -or $name.ToLowerInvariant() -ne 'alice.exe')) {throw 'PatchAlice requires Alice.exe'}
$original = [IO.File]::ReadAllBytes($gamePath)
if ($original.Length -lt 256 -or $original[0] -ne 77 -or $original[1] -ne 90) {throw 'Not an MZ executable'}
$files = @{}
$launch = $name
if ($PatchAlice) {
  # Explicit bytes are compatible with Windows PowerShell 5.1.
  $old = [byte[]]@(0xB0,0,0x52,0,0x53,0xE8,0x70,0x95,7,0,0x83,0xC4,8,0x85,0xC0,0x75,0x1A)
  $new = [byte[]]@(0xB0,0,0x52,0,0x53,0xE8,0x70,0x95,7,0,0x83,0xC4,8,0x85,0xC0,0x74,0x1A)
  $hits=@()
  for ($i=0; $i -le $original.Length-$old.Length; $i++) {
    if ($original[$i] -ne $old[0]) {continue}
    $match=$true
    for ($j=1; $j -lt $old.Length; $j++) {if ($original[$i+$j] -ne $old[$j]) {$match=$false;break}}
    if ($match) {$hits+= $i}
  }
  if ($hits.Count -ne 1) {throw "Known Alice hardware-check sequence not found exactly once ($($hits.Count) matches)"}
  $original[$hits[0]+$old.Length-2] = 0x74
  $launch='Alice-A3D2.exe'
  $files[$launch]=$original
}
$files[$launch+'.manifest'] = [IO.File]::ReadAllBytes((Join-Path $PSScriptRoot ($launch+'.manifest')))
$files['a3dapi.dll'] = [IO.File]::ReadAllBytes((Join-Path $PSScriptRoot 'bin\a3dapi.dll'))
if ($Kind -eq 'quake3') {$files['a3d.dll']=[IO.File]::ReadAllBytes((Join-Path $PSScriptRoot 'bin\a3d.dll'))}
$files['a3d-comtest.exe']=[IO.File]::ReadAllBytes((Join-Path $PSScriptRoot 'bin\a3d-comtest.exe'))
$files['a3d-comtest.exe.manifest']=[IO.File]::ReadAllBytes((Join-Path $PSScriptRoot 'a3d-comtest.exe.manifest'))
foreach ($filename in $files.Keys) {
  $target = Join-Path $dir $filename
  if ([IO.File]::Exists($target)) {throw "Existing file would be overwritten: $target"}
}
$made = New-Object System.Collections.Generic.List[string]
try {
  foreach ($filename in $files.Keys) {
    $target = Join-Path $dir $filename
    $stream=New-Object System.IO.FileStream($target,[IO.FileMode]::CreateNew)
    try {$stream.Write($files[$filename],0,$files[$filename].Length)} finally {$stream.Dispose()}
    $made.Add($target)
  }
} catch {
  foreach($target in $made) {[IO.File]::Delete($target)}
  throw
}
Write-Host "Created local A3D game files beside $name (no registry modifications)."
Write-Host "Launch $launch. Test a3d-comtest.exe to verify COM activation."
Write-Host 'The legacy Quake III a3d.dll path is a DirectSound compatibility bridge, not A3D2 Wavetracing.'
