param(
  [string]$Command
)

$ErrorActionPreference = 'Stop'
$KeyPath = Join-Path $PSScriptRoot 'aws/gaming-system-ai-core-admin.pem'
$KnownHosts = Join-Path $PSScriptRoot 'aws/known_hosts'
if (-not (Test-Path $KnownHosts)) {
  New-Item -ItemType File -Path $KnownHosts -Force | Out-Null
}

$commandFromFile = $null
if (-not $Command -and (Test-Path (Join-Path $PSScriptRoot 'remote-command.txt'))) {
  $commandFromFile = Get-Content -Path (Join-Path $PSScriptRoot 'remote-command.txt') -Raw
}

$finalCommand = if ($Command) { $Command } elseif ($commandFromFile) { $commandFromFile } else { throw 'No command provided' }

$hostName = '3.95.183.186'
$sshArgs = @(
  '-i', $KeyPath,
  '-o', 'StrictHostKeyChecking=no',
  '-o', "UserKnownHostsFile=$KnownHosts",
  "ubuntu@$hostName",
  $finalCommand
)

& ssh @sshArgs

