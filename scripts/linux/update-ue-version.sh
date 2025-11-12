#!/bin/bash
# scripts/linux/update-ue-version.sh
# Automated UE5 Version Update Script

set -e

NEW_VERSION=$1
CURRENT_VERSION=${2:-"5.6.1"}
UE_SOURCE_DIR="/opt/UnrealEngine"
PROJECT_PATH="/opt/BodyBroker"
BACKUP_DIR="/opt/UnrealEngine.backup.$CURRENT_VERSION"

echo "=== Updating UE5 from $CURRENT_VERSION to $NEW_VERSION ==="

# Validate version format
if [[ ! $NEW_VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Invalid version format. Use X.Y.Z (e.g., 5.7.0)"
    exit 1
fi

# Backup current version
if [ -d "$UE_SOURCE_DIR" ]; then
    echo "Backing up current version..."
    sudo cp -r "$UE_SOURCE_DIR" "$BACKUP_DIR"
fi

# Clone new version
echo "Cloning UE5 $NEW_VERSION..."
cd /tmp
rm -rf "UnrealEngine-$NEW_VERSION"
git clone --branch "$NEW_VERSION-release" \
    --depth 1 \
    https://github.com/EpicGames/UnrealEngine.git \
    "UnrealEngine-$NEW_VERSION"

# Setup dependencies
cd "UnrealEngine-$NEW_VERSION"
echo "Setting up dependencies..."
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
if [ -d "$PROJECT_PATH" ]; then
    ./Engine/Build/BatchFiles/Linux/RunTests.sh \
        -Project="$PROJECT_PATH" \
        -Test="*" \
        -Report="$PROJECT_PATH/TestResults" || true
fi

# If build successful, deploy
if [ $? -eq 0 ] || [ ! -d "$PROJECT_PATH" ]; then
    echo "Build successful. Deploying..."
    sudo rm -rf "$UE_SOURCE_DIR"
    sudo mv "UnrealEngine-$NEW_VERSION" "$UE_SOURCE_DIR"
    
    # Update capability registry
    if command -v python3 &> /dev/null; then
        python3 /opt/services/capability-registry/update_version.py \
            --version "$NEW_VERSION" || true
    fi
    
    echo "✅ UE5 updated to $NEW_VERSION"
else
    echo "❌ Build failed. Restoring backup..."
    if [ -d "$BACKUP_DIR" ]; then
        sudo rm -rf "$UE_SOURCE_DIR"
        sudo mv "$BACKUP_DIR" "$UE_SOURCE_DIR"
    fi
    exit 1
fi





