param([Parameter(Mandatory=$true)][string]$ToolchainBin)
$ErrorActionPreference = 'Stop'
$steps = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'windows-build-recipe.json') -Raw | ConvertFrom-Json
foreach ($step in $steps) {
  $program = Join-Path $ToolchainBin $step.program
  $arguments = @($step.args)
  if ($step.program -eq 'lld-link.exe' -and !(Test-Path -LiteralPath $program)) {
    $program = Join-Path $ToolchainBin 'ld.lld.exe'
    $arguments = @('-flavor','link') + $arguments
  }
  if (!(Test-Path -LiteralPath $program)) { throw "Missing tool: $program" }
  Push-Location -LiteralPath (Join-Path $PSScriptRoot $step.directory)
  try {
    New-Item -ItemType Directory -Path 'build' -Force | Out-Null
    & $program @arguments
    if ($LASTEXITCODE -ne 0) { throw "Build failed: $($step.program)" }
  } finally { Pop-Location }
}
Write-Host 'Build complete. Native game testing is separate.'
