# 🩸 The Body Broker - Complete System Reference

**Last Updated**: 2025-11-09  
**Status**: All foundation complete, training in progress

---

## System Architecture

### Backend Services (Python):
1. **Archetype System** (peer-reviewed)
2. **Harvesting System**
3. **Negotiation System**
4. **Drug Economy**
5. **Client Families**
6. **Morality Tracking**
7. **Broker's Book**
8. **Death System**
9. **Weaver's Loom**
10. **3-Tier Memory**
11. **Integration Orchestrator**
12. **API Layer**

### Frontend (Unreal Engine 5.6.1):
1. **BrokerBookWidget** - Living grimoire UI
2. **HarvestingMinigame** - Extraction mechanics
3. **NegotiationSystem** - Dialogue/haggling
4. **DeathSystemComponent** - Soul-Echo, Corpse-Tender
5. **VeilSightComponent** - Dual-world rendering
6. **BodyBrokerGameMode** - Main game controller

### Database (PostgreSQL):
- 8 tables with complete schema
- All indexes created
- Transaction logging
- Morality tracking

### Infrastructure:
- GPU: g5.2xlarge (i-05a16e074a5d79473)
- S3: body-broker-training-9728
- Docker: Complete compose file
- CI/CD: GitHub Actions

---

## API Endpoints

Base URL: `http://localhost:4100/body-broker`

- `POST /harvest` - Extract body parts
- `POST /negotiate` - Haggle with clients
- `POST /kill` - Record kill for morality
- `POST /death` - Trigger death sequence
- `POST /book/witness` - Record creature sighting
- `GET /morality` - Get Surgeon/Butcher status
- `GET /families` - List unlocked Dark families
- `GET /book/drugs/{id}` - Query drug info
- `GET /stats` - Comprehensive system stats

---

## Training Data

- **Vampire**: 1,785 examples (255 per adapter task)
- **Zombie**: 686 examples (98 per adapter task)
- **Source**: 22 narrative documents
- **Format**: JSON by adapter task

---

## Git Repository

**Commits This Session**: 34  
**Total Commits**: 203  
**Branch**: master  
**Ahead of origin**: 169 commits

---

## AWS Resources (Updated CSV)

File: `Project-Management/aws-resources.csv`

New resources:
- EC2: i-05a16e074a5d79473 (Body Broker training)
- S3: body-broker-training-9728
- IAM: gaming-system-ssm-role

---

## Monitoring

```powershell
# Real-time training monitor
pwsh .\scripts\monitor-all-training.ps1

# Check specific job
aws ssm get-command-invocation --instance-id i-05a16e074a5d79473 --command-id [ID]

# System validation
pwsh .\scripts\validate-all-systems.ps1
```

---

**Reference**: Complete system documentation in 20+ markdown files

