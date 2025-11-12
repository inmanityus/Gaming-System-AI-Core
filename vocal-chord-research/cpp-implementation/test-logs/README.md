# Vocal Synthesis Test Logs

This directory contains test execution logs for the vocal synthesis C++ library.

## Running Tests

```bash
cd vocal-chord-research/cpp-implementation/build
ctest --verbose --output-log test-results-$(Get-Date -Format 'yyyy-MM-dd').log
```

## Test Output Format

- Test name
- Execution time
- Pass/Fail status
- Performance metrics (for benchmarks)

## Latest Results

Check the most recent .log file in this directory.
