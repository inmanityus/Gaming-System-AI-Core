# README.md
# UE5 Linux Deployment & Automation System

Complete implementation of UE5 Linux deployment, automated updates, and Storyteller capability integration.

## Components

### 1. Linux Server Setup
- `scripts/linux/setup-ue5-server.sh` - Automated UE5 server setup on AWS EC2

### 2. Automated Updates
- `scripts/linux/update-ue-version.sh` - Automated UE5 version updates
- `services/ue-version-monitor/main.py` - Version monitoring service

### 3. Capability Registry
- `services/capability-registry/main.py` - FastAPI service for UE5 capabilities
- `database/migrations/001_capability_registry.sql` - Database schema
- `scripts/populate-ue5-features.py` - Feature population script

### 4. Storyteller Integration
- `services/storyteller/capability_integration.py` - Storyteller capability awareness

### 5. Docker Deployment
- `docker-compose.yml` - Complete service orchestration
- Dockerfiles for all services

### 6. Testing
- `tests/test_ue5_deployment.py` - Comprehensive pairwise test suite

## Quick Start

1. **Setup Linux Server**:
```bash
bash scripts/linux/setup-ue5-server.sh
```

2. **Start Services**:
```bash
docker-compose up -d
```

3. **Populate Features**:
```bash
python scripts/populate-ue5-features.py
```

4. **Run Tests**:
```bash
pytest tests/test_ue5_deployment.py -v
```

## Documentation

- `docs/solutions/UE5-LINUX-DEPLOYMENT-AUTOMATION.md` - Complete deployment guide
- `docs/solutions/UE5-STORYTELLER-CAPABILITY-INTEGRATION.md` - Storyteller integration guide



