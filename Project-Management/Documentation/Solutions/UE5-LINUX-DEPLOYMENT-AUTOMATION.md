# Unreal Engine Linux Deployment & Automated Updates
**Date**: 2025-01-29  
**Status**: Solution Design - Ready for Implementation  
**UE Version**: 5.6.1 → 5.7+ (Automated Updates)

---

## EXECUTIVE SUMMARY

**Goal**: Deploy UE5 on Linux servers with automated version updates and integrate UE version capabilities into the Storyteller system.

**Key Benefits**:
- ✅ Scalable headless asset generation
- ✅ Automated UE version updates (5.6.1 → 5.7 → 5.8+)
- ✅ Storyteller aware of UE capabilities per version
- ✅ CI/CD integration for continuous updates
- ✅ Cost-effective AWS deployment

---

## LINUX SUPPORT CONFIRMED

**Unreal Engine 5 runs on Linux**:
- ✅ **Development**: Ubuntu 22.04+ recommended
- ✅ **Deployment**: Headless server support
- ✅ **Rendering**: Vulkan backend
- ✅ **Requirements**: Quad-core CPU, 32GB RAM, GPU (optional for headless)

**Cross-Compilation**: Build Linux binaries from Windows development environment

---

## ARCHITECTURE OVERVIEW

### 1. Linux Server Infrastructure

```
┌─────────────────────────────────────────────────┐
│           AWS EC2 Linux Server (Ubuntu 22.04)     │
├─────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────┐  │
│  │  UE5 Engine (Version X.Y.Z)                │  │
│  │  - Headless mode                           │  │
│  │  - Python API enabled                      │  │
│  │  - Asset generation scripts                 │  │
│  └────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────┐  │
│  │  Update Automation Service                 │  │
│  │  - Version monitoring                     │  │
│  │  - Automated builds                       │  │
│  │  - Rollback capability                    │  │
│  └────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────┐  │
│  │  Capability Registry Service                │  │
│  │  - Version → Features mapping              │  │
│  │  - API for Storyteller queries              │  │
│  └────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

### 2. Update Automation Flow

```
GitHub UE Repository
    ↓ (Monitor releases)
Update Detection Service
    ↓ (Trigger build)
Automated Build Pipeline
    ↓ (Test & Validate)
Deployment Service
    ↓ (Rollout)
UE5 Server (New Version)
    ↓ (Update Registry)
Capability Registry
    ↓ (Notify)
Storyteller Service
```

---

## IMPLEMENTATION PLAN

### Phase 1: Linux Server Setup (Week 1)

#### 1.1 AWS EC2 Instance Setup
- **Instance Type**: `g4dn.xlarge` (4 vCPU, 16GB RAM, GPU optional)
- **OS**: Ubuntu 22.04 LTS
- **Storage**: 200GB SSD (for UE5 engine + projects)
- **Security**: VPC, Security Groups, IAM roles

#### 1.2 UE5 Source Build on Linux
```bash
# Clone UE5 source from GitHub
git clone https://github.com/EpicGames/UnrealEngine.git
cd UnrealEngine

# Checkout specific version (5.6.1 initially)
git checkout 5.6.1-release

# Setup dependencies
./Setup.sh
./GenerateProjectFiles.sh

# Build engine (Development Editor)
./Engine/Build/BatchFiles/Linux/Build.sh \
    Linux Development \
    -Project="$PROJECT_PATH" \
    -TargetType=Editor \
    -Progress
```

#### 1.3 Docker Container (Optional)
```dockerfile
FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    clang \
    cmake \
    git \
    python3 \
    python3-pip \
    vulkan-tools \
    libvulkan-dev

# Install UE5
COPY UnrealEngine /opt/UnrealEngine
WORKDIR /opt/UnrealEngine

# Build UE5
RUN ./Setup.sh && \
    ./GenerateProjectFiles.sh && \
    ./Engine/Build/BatchFiles/Linux/Build.sh Linux Development

CMD ["/opt/UnrealEngine/Engine/Binaries/Linux/UnrealEditor"]
```

---

### Phase 2: Automated Update System (Week 2)

#### 2.1 Version Monitoring Service

**Service**: `ue-version-monitor`

**Responsibilities**:
- Monitor Epic Games GitHub releases
- Detect new UE5 versions (5.7, 5.8, etc.)
- Trigger update pipeline
- Notify admin dashboard

**Implementation**:
```python
# services/ue-version-monitor/main.py
import requests
import json
from datetime import datetime
from typing import Optional

class UEVersionMonitor:
    def __init__(self):
        self.github_api = "https://api.github.com/repos/EpicGames/UnrealEngine"
        self.current_version = "5.6.1"
        
    def check_for_updates(self) -> Optional[str]:
        """Check GitHub for new UE5 releases"""
        tags_url = f"{self.github_api}/tags"
        response = requests.get(tags_url)
        
        if response.status_code == 200:
            tags = response.json()
            # Filter UE5 tags (5.x.x-release format)
            ue5_tags = [t for t in tags if t['name'].startswith('5.')]
            
            # Get latest version
            if ue5_tags:
                latest_tag = ue5_tags[0]['name']
                latest_version = latest_tag.replace('-release', '')
                
                if self.is_newer_version(latest_version, self.current_version):
                    return latest_version
        return None
    
    def is_newer_version(self, new: str, current: str) -> bool:
        """Compare version strings (e.g., '5.7.0' > '5.6.1')"""
        new_parts = [int(x) for x in new.split('.')]
        current_parts = [int(x) for x in current.split('.')]
        
        for i in range(max(len(new_parts), len(current_parts))):
            new_val = new_parts[i] if i < len(new_parts) else 0
            current_val = current_parts[i] if i < len(current_parts) else 0
            
            if new_val > current_val:
                return True
            elif new_val < current_val:
                return False
        return False
```

#### 2.2 Automated Build Pipeline

**Service**: `ue-build-automation`

**Responsibilities**:
- Clone new UE5 version
- Build engine from source
- Run test suite
- Deploy to production

**Implementation**:
```bash
#!/bin/bash
# scripts/linux/update-ue-version.sh

set -e

NEW_VERSION=$1
CURRENT_VERSION="5.6.1"
UE_SOURCE_DIR="/opt/UnrealEngine"
PROJECT_PATH="/opt/BodyBroker"

echo "=== Updating UE5 from $CURRENT_VERSION to $NEW_VERSION ==="

# Backup current version
echo "Backing up current version..."
cp -r "$UE_SOURCE_DIR" "$UE_SOURCE_DIR.backup.$CURRENT_VERSION"

# Clone new version
echo "Cloning UE5 $NEW_VERSION..."
cd /tmp
git clone --branch "$NEW_VERSION-release" \
    https://github.com/EpicGames/UnrealEngine.git \
    "UnrealEngine-$NEW_VERSION"

# Setup dependencies
cd "UnrealEngine-$NEW_VERSION"
./Setup.sh
./GenerateProjectFiles.sh

# Build engine
echo "Building UE5 $NEW_VERSION..."
./Engine/Build/BatchFiles/Linux/Build.sh \
    Linux Development \
    -Project="$PROJECT_PATH" \
    -TargetType=Editor \
    -Progress

# Run test suite
echo "Running test suite..."
./Engine/Build/BatchFiles/Linux/RunTests.sh \
    -Project="$PROJECT_PATH" \
    -Test="*" \
    -Report="$PROJECT_PATH/TestResults"

# If tests pass, deploy
if [ $? -eq 0 ]; then
    echo "Tests passed. Deploying..."
    rm -rf "$UE_SOURCE_DIR"
    mv "UnrealEngine-$NEW_VERSION" "$UE_SOURCE_DIR"
    
    # Update capability registry
    python3 /opt/services/capability-registry/update_version.py \
        --version "$NEW_VERSION"
    
    echo "✅ UE5 updated to $NEW_VERSION"
else
    echo "❌ Tests failed. Rolling back..."
    rm -rf "UnrealEngine-$NEW_VERSION"
    # Restore backup if needed
    echo "Update failed. Current version maintained."
    exit 1
fi
```

#### 2.3 CI/CD Integration

**GitHub Actions Workflow**:
```yaml
# .github/workflows/ue-auto-update.yml
name: UE5 Auto-Update

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
  workflow_dispatch:

jobs:
  check-updates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Check for UE5 updates
        run: |
          python3 scripts/ue-version-monitor.py
          
      - name: Trigger build if update available
        if: steps.check-updates.outputs.update_available == 'true'
        run: |
          echo "New version detected: ${{ steps.check-updates.outputs.new_version }}"
          # Trigger build pipeline
```

---

### Phase 3: Capability Registry Service (Week 3)

#### 3.1 Version → Features Mapping

**Service**: `capability-registry`

**Purpose**: Store and serve UE5 version capabilities to Storyteller

**Database Schema**:
```sql
-- capability_registry.ue_versions
CREATE TABLE ue_versions (
    version VARCHAR(10) PRIMARY KEY,
    release_date DATE,
    is_preview BOOLEAN DEFAULT FALSE,
    is_stable BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- capability_registry.features
CREATE TABLE features (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    category VARCHAR(50),  -- 'rendering', 'audio', 'physics', 'ai', etc.
    created_at TIMESTAMP DEFAULT NOW()
);

-- capability_registry.version_features
CREATE TABLE version_features (
    version VARCHAR(10) REFERENCES ue_versions(version),
    feature_id INTEGER REFERENCES features(id),
    introduced_in VARCHAR(10),  -- First version with this feature
    deprecated_in VARCHAR(10),  -- NULL if still active
    config JSONB,  -- Feature-specific configuration
    PRIMARY KEY (version, feature_id)
);
```

#### 3.2 Feature Detection & Registration

**Automated Feature Extraction**:
```python
# services/capability-registry/extract_features.py
import json
import subprocess
from typing import List, Dict

class UEFeatureExtractor:
    def __init__(self, ue_path: str):
        self.ue_path = ue_path
        
    def extract_features(self, version: str) -> List[Dict]:
        """Extract features from UE5 source code"""
        features = []
        
        # Parse release notes
        release_notes = self.get_release_notes(version)
        features.extend(self.parse_release_notes(release_notes))
        
        # Parse source code for new APIs
        source_features = self.scan_source_code(version)
        features.extend(source_features)
        
        # Parse documentation
        doc_features = self.parse_documentation(version)
        features.extend(doc_features)
        
        return features
    
    def get_release_notes(self, version: str) -> str:
        """Fetch release notes from GitHub"""
        # Implementation: Fetch from GitHub releases API
        pass
    
    def parse_release_notes(self, notes: str) -> List[Dict]:
        """Parse release notes for feature mentions"""
        # Implementation: NLP parsing of release notes
        pass
    
    def scan_source_code(self, version: str) -> List[Dict]:
        """Scan UE5 source for new classes/functions"""
        # Implementation: Static analysis of C++ headers
        pass
```

#### 3.3 API for Storyteller

**REST API Endpoints**:
```python
# services/capability-registry/api.py
from fastapi import FastAPI, Query
from typing import List, Optional

app = FastAPI()

@app.get("/api/v1/capabilities")
async def get_capabilities(
    version: Optional[str] = Query(None, description="UE5 version"),
    category: Optional[str] = Query(None, description="Feature category")
):
    """Get available capabilities for UE5 version"""
    if version:
        return get_capabilities_for_version(version, category)
    else:
        return get_latest_capabilities(category)

@app.get("/api/v1/versions")
async def get_versions():
    """Get all available UE5 versions"""
    return get_all_versions()

@app.get("/api/v1/features/{feature_name}")
async def get_feature_details(feature_name: str):
    """Get detailed information about a specific feature"""
    return get_feature_info(feature_name)
```

---

### Phase 4: Storyteller Integration (Week 4)

#### 4.1 Storyteller Capability Awareness

**Integration Point**: Storyteller Service queries Capability Registry

**Implementation**:
```python
# services/storyteller/capability_integration.py
import httpx
from typing import List, Dict, Optional

class StorytellerCapabilityManager:
    def __init__(self, registry_api_url: str):
        self.registry_api = registry_api_url
        self.cached_capabilities = {}
        
    async def get_available_features(self, version: str) -> Dict:
        """Get available features for UE5 version"""
        if version not in self.cached_capabilities:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.registry_api}/api/v1/capabilities",
                    params={"version": version}
                )
                self.cached_capabilities[version] = response.json()
        return self.cached_capabilities[version]
    
    def enhance_story_prompt(self, base_prompt: str, version: str) -> str:
        """Enhance story prompt with UE5 capabilities"""
        capabilities = await self.get_available_features(version)
        
        feature_list = []
        for category, features in capabilities.items():
            feature_list.append(f"{category}: {', '.join(features)}")
        
        enhanced_prompt = f"""
{base_prompt}

AVAILABLE UE5 CAPABILITIES (Version {version}):
{chr(10).join(feature_list)}

You can use these features to enhance the player's world:
- Create more immersive environments
- Add dynamic weather effects
- Implement advanced AI behaviors
- Enhance audio experiences
- Create procedural content
"""
        return enhanced_prompt
```

#### 4.2 Dynamic Story Expansion

**Example**: Storyteller uses new UE5.7 features

```python
# Example: Storyteller uses new UE5.7 Nanite improvements
if "nanite_virtualized_geometry" in available_features:
    story_context = """
    The ancient ruins can now be rendered with unprecedented detail.
    Use Nanite virtualized geometry to create massive, detailed structures
    that were previously impossible due to polygon limits.
    """
    
# Example: Storyteller uses new UE5.7 Lumen improvements
if "lumen_global_illumination" in available_features:
    story_context = """
    The underground caverns can now have realistic global illumination
    with dynamic light bounces. Create atmospheric lighting that responds
    to player actions in real-time.
    """
```

---

## DEPLOYMENT SCRIPTS

### 1. Initial Linux Setup

```bash
#!/bin/bash
# scripts/linux/setup-ue5-server.sh

set -e

echo "=== Setting up UE5 Linux Server ==="

# Install dependencies
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    clang \
    cmake \
    git \
    python3 \
    python3-pip \
    vulkan-tools \
    libvulkan-dev \
    libx11-dev \
    libxrandr-dev \
    libxinerama-dev \
    libxcursor-dev \
    libxi-dev \
    libxext-dev

# Clone UE5 source
cd /opt
sudo git clone https://github.com/EpicGames/UnrealEngine.git
cd UnrealEngine
sudo git checkout 5.6.1-release

# Setup UE5
sudo ./Setup.sh
sudo ./GenerateProjectFiles.sh

# Build UE5
sudo ./Engine/Build/BatchFiles/Linux/Build.sh \
    Linux Development \
    -Project="/opt/BodyBroker" \
    -TargetType=Editor \
    -Progress

echo "✅ UE5 Linux server setup complete"
```

### 2. Automated Update Script

```bash
#!/bin/bash
# scripts/linux/auto-update-ue5.sh

set -e

VERSION_MONITOR_URL="http://localhost:8080/api/v1/check-updates"
UPDATE_SCRIPT="/opt/scripts/linux/update-ue-version.sh"

echo "=== Checking for UE5 updates ==="

# Check for new version
NEW_VERSION=$(curl -s "$VERSION_MONITOR_URL" | jq -r '.new_version')

if [ "$NEW_VERSION" != "null" ] && [ -n "$NEW_VERSION" ]; then
    echo "New version detected: $NEW_VERSION"
    echo "Starting update process..."
    
    # Run update script
    bash "$UPDATE_SCRIPT" "$NEW_VERSION"
    
    # Notify services
    curl -X POST "http://localhost:8080/api/v1/notify-update" \
        -H "Content-Type: application/json" \
        -d "{\"version\": \"$NEW_VERSION\"}"
else
    echo "No updates available"
fi
```

---

## MONITORING & ALERTS

### Health Checks

```python
# services/ue-health-monitor/main.py
import subprocess
import requests
from datetime import datetime

def check_ue5_health():
    """Check if UE5 server is healthy"""
    checks = {
        "engine_running": check_engine_process(),
        "python_api": check_python_api(),
        "asset_generation": check_asset_generation(),
        "version": get_current_version()
    }
    return checks

def check_engine_process():
    """Check if UE5 editor process is running"""
    result = subprocess.run(
        ["pgrep", "-f", "UnrealEditor"],
        capture_output=True
    )
    return result.returncode == 0
```

---

## COST ESTIMATION

### AWS EC2 Costs (Monthly)

- **g4dn.xlarge**: ~$0.50/hour × 730 hours = **$365/month**
- **Storage (200GB EBS)**: ~$20/month
- **Data Transfer**: ~$10/month
- **Total**: **~$395/month**

### Alternative: Spot Instances

- **g4dn.xlarge Spot**: ~$0.15/hour × 730 hours = **$110/month**
- **Total with Spot**: **~$140/month** (with interruption risk)

---

## NEXT STEPS

1. ✅ **Week 1**: Set up AWS EC2 Linux server
2. ✅ **Week 2**: Build UE5 5.6.1 from source
3. ✅ **Week 3**: Implement update automation
4. ✅ **Week 4**: Create capability registry
5. ✅ **Week 5**: Integrate with Storyteller
6. ✅ **Week 6**: Test & deploy

---

## REFERENCES

- [UE5 Linux Development Requirements](https://dev.epicgames.com/documentation/unreal-engine/linux-development-requirements-for-unreal-engine)
- [UE5 GitHub Repository](https://github.com/EpicGames/UnrealEngine)
- [UE5 Release Notes](https://www.unrealengine.com/en-US/blog)

---

**Status**: ✅ **SOLUTION DESIGNED** - **READY FOR IMPLEMENTATION**

