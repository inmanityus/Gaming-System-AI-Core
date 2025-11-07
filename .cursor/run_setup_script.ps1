$ErrorActionPreference = 'Stop'
$KeyPath = Join-Path $PSScriptRoot 'aws/gaming-system-ai-core-admin.pem'
$KnownHosts = Join-Path $PSScriptRoot 'aws/known_hosts'
if (-not (Test-Path $KnownHosts)) {
  New-Item -ItemType File -Path $KnownHosts -Force | Out-Null
}

$hostName = '3.95.183.186'
$remoteCommand = @(
  "chmod +x ~/setup-ue5-server.sh",
  "bash -lc '~/setup-ue5-server.sh'"
) -join ' && '

$sshArgs = @(
  '-i', $KeyPath,
  '-o', 'StrictHostKeyChecking=no',
  '-o', "UserKnownHostsFile=$KnownHosts",
  "ubuntu@$hostName",
  $remoteCommand
)

& ssh @sshArgs

