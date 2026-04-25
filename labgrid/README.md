# Quantum Labgrid Test Framework

This directory contains the Labgrid test framework for the Quantum project.

## Overview

The Labgrid test framework provides automated testing for the Quantum project using QEMU. It includes:

- **Labgrid configuration** for QEMU target
- **Test scripts** for kernel boot and shell commands
- **Report generation** for test results

## Prerequisites

### Ubuntu Server Requirements

1. **Python 3** (3.7+)
2. **QEMU** (qemu-system-aarch64)
3. **Buildroot** build system
4. **Labgrid** and dependencies

### Install Dependencies

```bash
# Install QEMU
sudo apt-get install qemu-system-arm qemu-utils

# Install Python dependencies
pip3 install labgrid pytest pytest-json
```

## Buildroot Integration

The Labgrid package is integrated into the Buildroot build system. To enable it:

1. Run `make menuconfig` in the project root
2. Go to `Target packages` → `Interpreter languages and scripting` → `Python`
3. Select `labgrid` package
4. Save configuration and run `make`

## Running Tests

### 1. Build the Project

First, build the Quantum project:

```bash
# Load environment
source build/envsetup.sh

# Select board configuration
lunch quantum_qemu_debug

# Build the project
make
```

### 2. Run Tests

```bash
# Change to test directory
cd tests/labgrid

# Run tests
./run_tests.sh
```

### 3. View Test Reports

Test reports will be generated in the `reports` directory:

- **HTML report**: `reports/test_report.html`
- **JSON report**: `reports/test_report.json`

Open the HTML report in a browser to view detailed test results.

## Test Configuration

The test configuration is defined in `config.yaml`:

- **targets**: Defines the QEMU target and its resources
- **environment**: Sets environment variables for testing

## Test Cases

The test script `test_quantum.py` includes the following test cases:

1. **test_boot_kernel**: Tests kernel boot process
2. **test_shell_commands**: Tests basic shell commands
3. **test_memory_disk**: Tests memory disk functionality
4. **test_shutdown**: Tests system shutdown

## Adding New Tests

To add new test cases:

1. Edit `test_quantum.py` and add new test methods
2. Follow the existing test pattern
3. Run tests to verify

## Troubleshooting

### Common Issues

1. **QEMU not found**: Install QEMU with `sudo apt-get install qemu-system-arm`
2. **Labgrid not installed**: Run `pip3 install labgrid pytest pytest-json`
3. **Build artifacts missing**: Run `make` to build the project first

### Debugging

To run tests in debug mode:

```bash
python3 test_quantum.py -v
```

## CI/CD Integration

This test framework can be integrated into CI/CD pipelines. For GitHub Actions, use the existing `.github/workflows/ci.yml` file, which has been configured to use self-hosted runners.

## License

This test framework is part of the Quantum project and follows the same license.
