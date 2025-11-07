#!/bin/bash
# scripts/linux/setup-ue5-server.sh
# UE5 Linux Server Setup Script for AWS EC2 (Ubuntu 22.04)

set -euo pipefail

# Configuration
UE_VERSION="5.6.1-release"
INSTALL_DIR="/opt/UnrealEngine"
PROJECT_PATH="/opt/BodyBroker"
GITHUB_REPO="https://github.com/EpicGames/UnrealEngine.git"
LOG_FILE="/var/log/ue5-setup.log"

# Functions
log() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $message" | sudo tee -a "$LOG_FILE"
}

check_prerequisites() {
    if [ "$EUID" -eq 0 ]; then
        log "ERROR: Do not run this script as root"
        exit 1
    fi
    
    check_disk_space
}

check_disk_space() {
    local required_space=50  # GB
    local available_space=$(df -BG /opt | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$available_space" -lt "$required_space" ]; then
        log "ERROR: Insufficient disk space. Need at least ${required_space}GB, have ${available_space}GB"
        exit 1
    fi
}

install_dependencies() {
    log "Installing dependencies..."
    if ! sudo apt-get update; then
        log "ERROR: Failed to update package lists"
        exit 1
    fi
    
    if ! sudo apt-get install -y \
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
        libxext-dev \
        curl \
        jq; then
        log "ERROR: Failed to install dependencies"
        exit 1
    fi
}

setup_directories() {
    log "Creating UE5 directory..."
    if ! sudo mkdir -p "$INSTALL_DIR"; then
        log "ERROR: Failed to create installation directory"
        exit 1
    fi
    sudo chown "$USER:$USER" "$INSTALL_DIR"
}

clone_repository() {
    log "Cloning UE5 source..."
    cd /opt
    if [ ! -d "UnrealEngine" ]; then
        if ! git clone "$GITHUB_REPO"; then
            log "ERROR: Failed to clone repository"
            exit 1
        fi
        cd UnrealEngine
        if ! git verify-commit HEAD; then
            log "WARNING: Could not verify commit signature"
        fi
    else
        cd UnrealEngine
    fi
}

checkout_version() {
    log "Checking out UE5 $UE_VERSION..."
    if ! git checkout "$UE_VERSION"; then
        log "ERROR: Failed to checkout version $UE_VERSION"
        exit 1
    fi
}

setup_ue5() {
    log "Setting up UE5..."
    if ! ./Setup.sh; then
        log "ERROR: Setup.sh failed"
        exit 1
    fi
    
    if ! ./GenerateProjectFiles.sh; then
        log "ERROR: GenerateProjectFiles.sh failed"
        exit 1
    fi
}

build_engine() {
    log "Building UE5..."
    if ! ./Engine/Build/BatchFiles/Linux/Build.sh \
        Linux Development \
        -Project="$PROJECT_PATH" \
        -TargetType=Editor \
        -Progress; then
        log "ERROR: Build failed"
        exit 1
    fi
}

cleanup() {
    if [ $? -ne 0 ]; then
        log "ERROR: An error occurred during setup"
    fi
}

# Main execution
trap cleanup EXIT

log "=== Starting UE5 Linux Server Setup ==="
check_prerequisites
install_dependencies
setup_directories
clone_repository
checkout_version
setup_ue5
build_engine
log "✅ UE5 Linux server setup complete"

