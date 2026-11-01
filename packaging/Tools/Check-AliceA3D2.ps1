# Aufake3D 0.8.11 -- read-only Windows Alice provider naming audit.
[CmdletBinding()]
param([Parameter(Mandatory=$true)][ValidateSet('alice2000','alice2011')][string]$Profile,
      [Parameter(Mandatory=$true)][string]$GameExe,
      [string]$TracePath='', [string]$ConsolePath='')
$ErrorActionPreference='Stop'
$exe=(Resolve-Path -LiteralPath $GameExe).Path
if([IO.Path]::GetFileName($exe) -ine 'alice.exe'){throw 'Expected alice.exe'}
$hash=(Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant()
Write-Host 'Aufake3D 0.8.11 Alice provider audit (read-only)' -ForegroundColor Cyan
Write-Host ('Profile: '+$Profile)
Write-Host ('Executable SHA256: '+$hash)
if($Profile -eq 'alice2011'){
 Write-Host ('Known verified Alice2011 binary: '+($hash -eq '08bcbe4b549633b24c90a1ab36bf516bd8873432c68b37248c98ee4225506e50'))
}else{Write-Warning 'Alice 2000 selector/provider naming NOT YET VERIFIED on actual game. No automatic 2011 alias transplant.'}
if([string]::IsNullOrWhiteSpace($TracePath)){
 $auto=Join-Path (Split-Path -Parent $exe) 'SndDrivers\a3d-v074f-miles.log'
 if(Test-Path -LiteralPath $auto){$TracePath=$auto}
}
$verified=$false
if($TracePath){
 $log=Get-Content -LiteralPath $TracePath -Raw
 if($log.Contains('AIL_STARTUP_BEGIN')){$log=$log.Substring($log.LastIndexOf('AIL_STARTUP_BEGIN'))}
 $candidate=[regex]::Match($log,'(?m)^A3D2_ENUM_SELECTED_CANDIDATE\s+(0x[0-9a-fA-F]+)\s*$')
 $opening=[regex]::Match($log,'(?m)^AIL_OPEN_BEGIN_PROVIDER\s+(0x[0-9a-fA-F]+)\s*$')
 $opened=[regex]::Match($log,'(?m)^AIL_OPEN_RETURN\s+(0x[0-9a-fA-F]+)\s*$')
 $listener=[regex]::Match($log,'(?m)^AIL_OPEN_LISTENER_RETURN\s+(0x[0-9a-fA-F]+)\s*$')
 $canonical=$log.Contains('AIL_ENUM_PROVIDER_NAME Aureal A3D 2.0 (TM)')
 $verified=$candidate.Success -and $opening.Success -and $opened.Success -and $listener.Success -and $canonical
 if($verified){$verified=([convert]::ToUInt32($candidate.Groups[1].Value.Substring(2),16) -eq [convert]::ToUInt32($opening.Groups[1].Value.Substring(2),16)) -and ($opened.Groups[1].Value -eq '0x00000000') -and ($listener.Groups[1].Value -ne '0x00000000')}
 Write-Host ('Genuine A3D2 handle/listener verified by trace: '+$verified)
 Write-Host ('Proxy canonical name upgrade logged: '+$log.Contains('A3D2_DISPLAY_NAME_UPGRADED Aureal A3D 2.0 (TM)'))
}else{Write-Warning 'No Miles trace supplied/found: provider activation cannot be certified.'}
if($ConsolePath){
 $c=Get-Content -LiteralPath $ConsolePath -Raw
 Write-Host ('Actual game console canonical name: '+($c -match 'Aureal A3D 2\.0 \(TM\)\s+provider opened\.'))
 Write-Host ('Actual game console unknown name: '+($c -match 'unknown\s+provider opened\.'))
}else{Write-Host 'No game console log supplied: visible label is unverified by this script.'}
if(!$verified){exit 3}
exit 0
