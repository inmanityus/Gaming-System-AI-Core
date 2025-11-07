$ErrorActionPreference = 'Stop'
$KeyPath = Join-Path $PSScriptRoot 'aws/gaming-system-ai-core-admin.pem'
$KnownHosts = Join-Path $PSScriptRoot 'aws/known_hosts'
if (-not (Test-Path $KnownHosts)) {
  New-Item -ItemType File -Path $KnownHosts -Force | Out-Null
}

$repoRoot = Split-Path $PSScriptRoot -Parent
$scriptPath = Join-Path $repoRoot 'scripts/linux/setup-ue5-server.sh'
if (-not (Test-Path $scriptPath)) {
  throw "Setup script not found at $scriptPath"
}

$destination = 'ubuntu@3.95.183.186:/home/ubuntu/setup-ue5-server.sh'

$scpArgs = @(
  '-i', $KeyPath,
  '-o', 'StrictHostKeyChecking=no',
  '-o', "UserKnownHostsFile=$KnownHosts",
  $scriptPath,
  $destination
)

& scp @scpArgs

