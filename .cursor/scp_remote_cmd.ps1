$ErrorActionPreference = 'Stop'
$KeyPath = Join-Path $PSScriptRoot 'aws/gaming-system-ai-core-admin.pem'
$KnownHosts = Join-Path $PSScriptRoot 'aws/known_hosts'
if (-not (Test-Path $KnownHosts)) {
  New-Item -ItemType File -Path $KnownHosts -Force | Out-Null
}

$repoRoot = Split-Path $PSScriptRoot -Parent
$localScript = Join-Path $PSScriptRoot 'remote_cmd.sh'
if (-not (Test-Path $localScript)) {
  throw "remote_cmd.sh not found at $localScript"
}

$destination = 'ubuntu@3.95.183.186:/home/ubuntu/remote_cmd.sh'

$scpArgs = @(
  '-i', $KeyPath,
  '-o', 'StrictHostKeyChecking=no',
  '-o', "UserKnownHostsFile=$KnownHosts",
  $localScript,
  $destination
)

& scp @scpArgs

