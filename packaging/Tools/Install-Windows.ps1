# Aufake3D v0.9.0: reversible Windows game-local installer (no Python required)
[CmdletBinding()]
param(
 [Alias('Profile')][ValidateSet('alice2011','alice2000','quake3','halflife','unreal','rtcw')][string]$TargetProfile='alice2011',
 [Parameter(Mandatory=$true)][string]$GameExe,
 [switch]$DryRun,
 [switch]$Rollback
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$root=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$exe=(Resolve-Path -LiteralPath $GameExe -ErrorAction Stop).Path
$dir=Split-Path -Parent $exe
$receiptPath=Join-Path $dir '.aufake3d_current.json'
function HashFile([string]$p){return (Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLowerInvariant()}
function Relative([string]$base,[string]$p){return $p.Substring($base.TrimEnd('\').Length+1)}
if($Rollback){
 if(!(Test-Path -LiteralPath $receiptPath -PathType Leaf)){throw 'No release receipt to roll back'}
 $r=Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
 if($r.game_exe -ine $exe -or (HashFile $exe) -ne $r.game_exe_sha256){throw 'Game executable changed; refusing rollback'}
 foreach($it in $r.files){
  $dest=Join-Path $dir $it.rel
  if(!(Test-Path -LiteralPath $dest -PathType Leaf) -or (HashFile $dest) -ne $it.installed_sha256){throw "Installed file changed; refusing rollback: $dest"}
 }
 foreach($it in $r.files){
  $dest=Join-Path $dir $it.rel
  if($it.exists){
   $backup=Join-Path $r.backup_dir ('original\'+$it.rel)
   if(!(Test-Path -LiteralPath $backup -PathType Leaf) -or (HashFile $backup) -ne $it.original_sha256){throw "Backup changed/missing: $backup"}
   Copy-Item -LiteralPath $backup -Destination $dest -Force
  } else {Remove-Item -LiteralPath $dest -Force}
 }
 Remove-Item -LiteralPath $receiptPath -Force
 Write-Host 'Rolled back game-local files. Backup retained.' -ForegroundColor Green
 exit 0
}
if(Test-Path -LiteralPath $receiptPath){throw 'An existing v0.9.0 receipt exists. Roll back before reinstalling.'}
$names=@{alice2011='alice.exe';alice2000='alice.exe';quake3='quake3.exe';halflife='hl.exe'}
if([IO.Path]::GetFileName($exe) -ine $names[$TargetProfile]){throw "Expected $($names[$TargetProfile]) for profile $TargetProfile"}
$shaExe=HashFile $exe
if($TargetProfile -eq 'alice2011' -and $shaExe -ne '08bcbe4b549633b24c90a1ab36bf516bd8873432c68b37248c98ee4225506e50'){
 throw 'Unrecognized Alice 2011 executable hash; exact version-specific adapter not safe'}
$items=New-Object System.Collections.Generic.List[object]
function AddFile([string]$source,[string]$destination){
 if(@($items | Where-Object { $_.dest -ieq $destination }).Count -gt 0){return}
 if(!(Test-Path -LiteralPath $source -PathType Leaf)){throw "Missing included payload: $source"}
 if(!(Test-Path -LiteralPath (Split-Path -Parent $destination) -PathType Container)){throw "Destination folder missing: $destination"}
 if($source -ieq $exe -or $destination -ieq $exe){throw 'Game executable modification refused'}
 $items.Add([pscustomobject]@{src=$source;dest=$destination;rel=(Relative $dir $destination)})
}
# Both manual copying and this installer use the SAME kit data.
$kitMap=Get-Content -LiteralPath (Join-Path $root 'Game_Kits\INSTALL_MAP.json') -Raw | ConvertFrom-Json
$entry=$kitMap.profiles.$TargetProfile
if(!$entry){throw "Unknown game kit: $TargetProfile"}
$kitBase=Join-Path $root ('Game_Kits\'+$entry.folder+'\COPY_TO_GAME_FOLDER')
$onDisk=@(Get-ChildItem -LiteralPath $kitBase -Recurse -File | ForEach-Object { $_.FullName.Substring($kitBase.TrimEnd('\').Length+1).Replace('\','/') })
if(@(Compare-Object -ReferenceObject @($entry.files | Sort-Object) -DifferenceObject @($onDisk | Sort-Object)).Count -ne 0){throw 'Kit files differ from INSTALL_MAP.json; installation refused'}
if($TargetProfile -eq 'alice2011'){
 $snd=Join-Path $dir 'SndDrivers'
 if(!(Test-Path -LiteralPath (Join-Path $dir 'winmm.dll')) -or !(Test-Path -LiteralPath (Join-Path $dir 'VorpalFix.ini'))){throw 'VorpalFix winmm.dll / VorpalFix.ini missing'}
 if(!(Test-Path -LiteralPath (Join-Path $snd 'mssa3d2.m3d'))){throw 'Original mssa3d2.m3d missing'}
 $original=$null
 foreach($name in @('a3d_mss_real.dll','mss32.dll')){
  $candidate=Join-Path $snd $name
  if((Test-Path -LiteralPath $candidate -PathType Leaf) -and (HashFile $candidate) -eq '14fb663762695a02e06b144c487254b08163185fa009efb32df733882cd570de'){$original=$candidate;break}
 }
 if(!$original){throw 'Exact original Miles DLL missing; no safe proxy substitution possible'}
} elseif($TargetProfile -eq 'alice2000') {
 if(!(Test-Path -LiteralPath (Join-Path $dir 'SndDrivers\mss32.dll'))){throw 'Original classic Alice Miles DLL missing'}
}
foreach($rel in $entry.files){
 $winRel=$rel.Replace('/','\')
 AddFile (Join-Path $kitBase $winRel) (Join-Path $dir $winRel)
}
if($TargetProfile -eq 'alice2011'){
 # Add original vendor Miles copies in both locations (never part of redistributable kit).
 foreach($folder in @($dir,$snd)){
  AddFile $original (Join-Path $folder 'a3d_mss_real.dll')
 }
}
# Materialize vendor DLL bytes BEFORE replacing any original, to avoid source/target overlap.
$cached=New-Object System.Collections.Generic.List[object]
foreach($item in $items){
 if((Test-Path -LiteralPath $item.dest) -and ((Get-Item -LiteralPath $item.dest -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)){throw "Refusing symlink destination: $($item.dest)"}
 $bytes=[IO.File]::ReadAllBytes($item.src)
 $hash= [BitConverter]::ToString(([Security.Cryptography.SHA256]::Create()).ComputeHash($bytes)).Replace('-','').ToLowerInvariant()
 $cached.Add([pscustomobject]@{src=$item.src;dest=$item.dest;rel=$item.rel;bytes=$bytes;exists=(Test-Path -LiteralPath $item.dest -PathType Leaf);original_sha256=$(if(Test-Path -LiteralPath $item.dest -PathType Leaf){HashFile $item.dest}else{$null});installed_sha256=$hash})
 Write-Host "$(if(Test-Path -LiteralPath $item.dest){'BACKUP+REPLACE'}else{'CREATE'}) $($item.rel)"
}
if($DryRun){Write-Host 'Dry-run complete. Nothing modified.';exit 0}
$backup=Join-Path $dir ('.aufake3d_backup_v090\'+(Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
New-Item -ItemType Directory -Path $backup -Force|Out-Null
foreach($item in $cached){if($item.exists){$dst=Join-Path $backup ('original\'+$item.rel);New-Item -ItemType Directory -Path (Split-Path -Parent $dst) -Force|Out-Null;Copy-Item -LiteralPath $item.dest -Destination $dst -Force}}
try{
 foreach($item in $cached){[IO.File]::WriteAllBytes($item.dest,$item.bytes)}
 $receipt=[ordered]@{release='0.9.0';profile=$TargetProfile;game_exe=$exe;game_exe_sha256=$shaExe;backup_dir=$backup;files=@($cached | ForEach-Object {[ordered]@{rel=$_.rel;exists=$_.exists;original_sha256=$_.original_sha256;installed_sha256=$_.installed_sha256}})}
 $receipt|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $backup 'receipt.json') -Encoding UTF8
 $receipt|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $receiptPath -Encoding UTF8
} catch {
 foreach($item in $cached){$old=Join-Path $backup ('original\'+$item.rel);if($item.exists -and (Test-Path $old)){Copy-Item -LiteralPath $old -Destination $item.dest -Force}elseif(!$item.exists -and (Test-Path $item.dest)){Remove-Item -LiteralPath $item.dest -Force}}
 throw
}
Write-Host 'Installed. Original game EXE was not modified.' -ForegroundColor Green
Write-Host "Launch: $dir\RUN_AUFAKE3D_WINDOWS.cmd"
Write-Host "Rollback: powershell -File Tools\Install-Windows.ps1 -GameExe `"$exe`" -Rollback"
