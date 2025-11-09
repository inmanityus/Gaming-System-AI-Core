# 📊 Training Monitoring Commands

## Real-Time Monitor

```powershell
pwsh .\scripts\monitor-all-training.ps1
```

## Check Individual Jobs

```powershell
# GPU Setup
aws ssm get-command-invocation --instance-id i-05a16e074a5d79473 --command-id 321b62a7-6d3b-4f25-b7a7-4fe063d0efc4

# Vampire Training
aws ssm get-command-invocation --instance-id i-05a16e074a5d79473 --command-id 267fb42d-086e-4e5b-9b38-0018400fdf7b

# Zombie Training
aws ssm get-command-invocation --instance-id i-05a16e074a5d79473 --command-id 2f51aec2-55ab-4afc-a4cd-124b24c3e721
```

## Check Logs on Instance

```powershell
aws ssm send-command --instance-ids i-05a16e074a5d79473 --document-name "AWS-RunShellScript" --parameters file://scripts/check-training-logs.json
```

## After Training Complete

Run pairwise testing per /all-rules (MANDATORY).
See: `NEXT-SESSION-TRAINING-CHECK.md`

