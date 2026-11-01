<#
Windows 10/11 fallback ONLY if registration-free COM manifests fail.
Creates one per-user 32-bit CLSID key; no admin required. Does not overwrite a
pre-existing Aureal registration (including vendor drivers or another wrapper).
This is no longer a pure drop-in: it changes the current Windows user's COM
registry view. Never use on Windows 9x or on an old AU8830 reference machine.
#>
param(
 [Parameter(Mandatory=$true)][string]$GameDir,
 [switch]$Unregister
)
$ErrorActionPreference='Stop'
$dir=(Resolve-Path -LiteralPath $GameDir).Path
$dll=[IO.Path]::Combine($dir,'a3dapi.dll')
if (-not (Test-Path -LiteralPath $dll)) {throw "DLL not found: $dll"}
$keyname='Software\Classes\CLSID\{92FA2C24-253C-11D2-90FB-006008A1F441}\InprocServer32'
$root=[Microsoft.Win32.RegistryKey]::OpenBaseKey([Microsoft.Win32.RegistryHive]::CurrentUser,[Microsoft.Win32.RegistryView]::Registry32)
try {
  $existing=$root.OpenSubKey($keyname,$false)
  if ($Unregister) {
    if (-not $existing) {Write-Host 'No per-user registration exists';exit 0}
    $current=[string]$existing.GetValue('')
    $existing.Close()
    if ($current -ne $dll) {throw "The existing registration belongs to another DLL: $current"}
    $root.DeleteSubKey($keyname)
    Write-Host "Removed only the matching per-user class registration: $dll"
  } else {
    if ($existing) {
      $previous=[string]$existing.GetValue('')
      $existing.Close()
      throw "COM class is already registered for: $previous. Refusing overwrite."
    }
    $key=$root.CreateSubKey($keyname)
    try {
      $key.SetValue('',$dll,[Microsoft.Win32.RegistryValueKind]::String)
      $key.SetValue('ThreadingModel','Both',[Microsoft.Win32.RegistryValueKind]::String)
    } finally {$key.Close()}
    Write-Host "Registered a3dapi.dll under the current user's 32-bit COM view: $dll"
  }
} finally {$root.Close()}
