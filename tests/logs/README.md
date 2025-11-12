# Backend Test Logs

This directory contains test execution logs for Python/FastAPI backend services.

## Running Tests

```bash
cd tests
pytest security/ -v --cov=services/auth > logs/security-tests-$(Get-Date -Format 'yyyy-MM-dd').log 2>&1
```

## Latest Results

Check the most recent .log file in this directory.
