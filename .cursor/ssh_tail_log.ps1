$ErrorActionPreference = 'Stop'
$KeyPath = Join-Path $PSScriptRoot 'aws/gaming-system-ai-core-admin.pem'
$KnownHosts = Join-Path $PSScriptRoot 'aws/known_hosts'
if (-not (Test-Path $KnownHosts)) {
  New-Item -ItemType File -Path $KnownHosts -Force | Out-Null
}

$hostName = '3.95.183.186'
$sshArgs = @(
  '-i', $KeyPath,
  '-o', 'StrictHostKeyChecking=no',
  '-o', "UserKnownHostsFile=$KnownHosts",
  "ubuntu@$hostName",
  'tail -n 200 /var/log/ue5-setup.log'
)

& ssh @sshArgs

