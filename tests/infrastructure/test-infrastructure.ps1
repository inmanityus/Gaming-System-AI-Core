#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Runs comprehensive infrastructure tests for AWS setup
.DESCRIPTION
    Executes all test suites for TASK-001 (AWS Organizations) and TASK-002 (Network Foundation)
    Includes setup validation, test execution, and comprehensive reporting
#>

param(
    [Parameter(Mandatory=$false)]
    [switch]$InstallDependencies,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipCredentialCheck,
    
    [Parameter(Mandatory=$false)]
    [string]$TestSuite = "all"
)

$ErrorActionPreference = "Stop"

# Colors
$GREEN = "`e[32m"
$YELLOW = "`e[33m"
$RED = "`e[31m"
$BLUE = "`e[34m"
$NC = "`e[0m"

Write-Host "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
Write-Host "${BLUE}║      AWS Infrastructure Comprehensive Test Suite             ║${NC}"
Write-Host "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
Write-Host ""

# Function to check Python and dependencies
function Test-PythonEnvironment {
    Write-Host "${YELLOW}Checking Python environment...${NC}"
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "${GREEN}✓ Python found: $pythonVersion${NC}"
    }
    catch {
        Write-Host "${RED}✗ Python not found. Please install Python 3.8+${NC}"
        exit 1
    }
    
    # Check required packages
    $requiredPackages = @('pytest', 'boto3', 'pytest-json-report')
    $missingPackages = @()
    
    foreach ($package in $requiredPackages) {
        $installed = pip show $package 2>&1
        if ($LASTEXITCODE -ne 0) {
            $missingPackages += $package
        }
    }
    
    if ($missingPackages.Count -gt 0) {
        Write-Host "${YELLOW}Missing packages: $($missingPackages -join ', ')${NC}"
        
        if ($InstallDependencies) {
            Write-Host "${YELLOW}Installing missing packages...${NC}"
            pip install $missingPackages
            Write-Host "${GREEN}✓ Dependencies installed${NC}"
        }
        else {
            Write-Host "${RED}Run with -InstallDependencies to install missing packages${NC}"
            exit 1
        }
    }
    else {
        Write-Host "${GREEN}✓ All dependencies installed${NC}"
    }
}

# Function to check AWS credentials
function Test-AWSCredentials {
    if ($SkipCredentialCheck) {
        Write-Host "${YELLOW}Skipping AWS credential check${NC}"
        return
    }
    
    Write-Host "${YELLOW}Checking AWS credentials...${NC}"
    
    try {
        $identity = aws sts get-caller-identity --output json | ConvertFrom-Json
        Write-Host "${GREEN}✓ AWS Account: $($identity.Account)${NC}"
        Write-Host "${GREEN}✓ User ARN: $($identity.Arn)${NC}"
    }
    catch {
        Write-Host "${RED}✗ AWS credentials not configured${NC}"
        Write-Host "Please configure AWS CLI with: aws configure"
        exit 1
    }
}

# Function to validate test files exist
function Test-TestFiles {
    Write-Host "${YELLOW}Checking test files...${NC}"
    
    $testFiles = @(
        "test_aws_organizations.py",
        "test_network_foundation.py",
        "run_infrastructure_tests.py"
    )
    
    $missingFiles = @()
    foreach ($file in $testFiles) {
        if (-not (Test-Path $file)) {
            $missingFiles += $file
        }
    }
    
    if ($missingFiles.Count -gt 0) {
        Write-Host "${RED}✗ Missing test files: $($missingFiles -join ', ')${NC}"
        exit 1
    }
    else {
        Write-Host "${GREEN}✓ All test files present${NC}"
    }
}

# Function to run specific test suite
function Invoke-TestSuite {
    param([string]$Suite)
    
    Write-Host "`n${YELLOW}Running test suite: $Suite${NC}"
    Write-Host "="*60
    
    switch ($Suite) {
        "organizations" {
            python test_aws_organizations.py
        }
        "network" {
            python test_network_foundation.py
        }
        "all" {
            python run_infrastructure_tests.py
        }
        default {
            Write-Host "${RED}Unknown test suite: $Suite${NC}"
            exit 1
        }
    }
}

# Main execution
try {
    # Change to test directory
    Push-Location $PSScriptRoot
    
    # Run checks
    Test-PythonEnvironment
    Test-AWSCredentials
    Test-TestFiles
    
    Write-Host "`n${YELLOW}Starting test execution...${NC}"
    Write-Host "="*80
    
    # Run tests
    Invoke-TestSuite -Suite $TestSuite
    
    # Check for test reports
    $reports = Get-ChildItem -Filter "test_report_*.json" | Sort-Object LastWriteTime -Descending
    if ($reports.Count -gt 0) {
        Write-Host "`n${GREEN}Test reports generated:${NC}"
        foreach ($report in $reports) {
            Write-Host "  - $($report.Name)"
        }
    }
    
    Write-Host "`n${GREEN}Test execution completed!${NC}"
}
catch {
    Write-Host "`n${RED}Test execution failed: $_${NC}"
    exit 1
}
finally {
    Pop-Location
}
