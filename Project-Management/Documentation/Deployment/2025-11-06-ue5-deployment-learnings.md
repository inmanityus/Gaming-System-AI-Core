UE5 Deployment Learnings - 2025-11-06

- Database seeding relies on docker-compose and container-local hostname db with port 5432
- Capability Registry GET /api/v1/versions/ -encodedCommand aQBkAA== now aggregates capabilities without the helper endpoint and must stay aligned with migration schema -inputFormat xml -outputFormat text
- /clean-session produces emergency backups under .cursor/emergency-backup-YYYYmmddHHMMSS for rollback assurance
- Environmental narrative tables must exist before integration tests re-running migration 010_environmental_narrative.sql resolves UndefinedTable errors
- AWS deployment scripts require configured profile missing default credentials currently block EC2 provisioning
- Credentials file only defines [remote-admin] default profile missing which triggers aws CLI failure
