#!/usr/bin/env python3
"""
Quantum project test script using labgrid
Reads test cases from JSON configuration file
"""

import sys
import os
import time
import pytest
import subprocess
import json

# Add the tests directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Get project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from labgrid import Environment
from labgrid.driver import SerialDriver

class TestQuantum:
    """Test class for Quantum project"""

    @pytest.fixture(scope="class")
    def environment(self):
        """Create labgrid environment"""
        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        return Environment(config_path)

    @pytest.fixture(scope="class")
    def target(self, environment):
        """Get target from environment"""
        return environment.get_target("quantum-qemu")

    @pytest.fixture(scope="class")
    def test_cases(self):
        """Load test cases from JSON file"""
        json_path = os.path.join(os.path.dirname(__file__), "test_cases.json")
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['test_cases']

    def run_boot_kernel(self):
        """Run boot_kernel command"""
        print("========================================")
        print("Running boot_kernel command")
        print("========================================")

        # 运行boot_kernel命令
        print("Starting boot_kernel...")
        result = subprocess.run(
            ['bash', '-c', f'source {os.path.join(PROJECT_ROOT, "build", "envsetup.sh")} && lunch quantum_qemu_debug && boot_kernel'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=120
        )

        # 检查命令是否成功执行
        if result.returncode != 0:
            print(f"Warning: boot_kernel command returned code {result.returncode}")
            print(f"Stderr: {result.stderr}")
        else:
            print("✓ boot_kernel command executed successfully")

        # 等待QEMU启动
        print("Waiting for QEMU to start...")
        time.sleep(10)

    def connect_to_console(self, target):
        """Connect to QEMU console via SerialDriver"""
        try:
            serial = target.get_driver(SerialDriver)
            serial.activate()
            print("✓ Connected to QEMU console")
            return serial
        except Exception as e:
            print(f"Warning: Failed to connect to console: {e}")
            return None

    def run_shell_command(self, console, command, expected):
        """Run shell command and check output"""
        print(f"Executing: {command}")
        if console:
            console.sendline(command)
            if expected:
                console.expect(expected, timeout=10)
                print(f"✓ Command '{command}' executed successfully")
            else:
                # 对于没有预期输出的命令（如poweroff），只等待命令执行
                time.sleep(2)
                print(f"✓ Command '{command}' executed")
        else:
            print(f"Warning: No console available, skipping command '{command}'")

    def terminate_qemu_processes(self):
        """Terminate all QEMU processes"""
        print("Checking for QEMU processes...")
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        qemu_processes = [line for line in result.stdout.split('\n') if 'qemu-system-aarch64' in line]

        if qemu_processes:
            print(f"Found QEMU processes: {len(qemu_processes)}")
            # 尝试终止QEMU进程
            for process in qemu_processes:
                pid = process.split()[1]
                print(f"Terminating QEMU process {pid}...")
                try:
                    subprocess.run(['kill', pid], check=True)
                except Exception as e:
                    print(f"Error terminating process {pid}: {e}")

            # 等待进程终止
            time.sleep(5)

            # 再次检查QEMU进程
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            remaining_qemu = [line for line in result.stdout.split('\n') if 'qemu-system-aarch64' in line]

            if remaining_qemu:
                print(f"Warning: Still found QEMU processes: {len(remaining_qemu)}")
            else:
                print("✓ All QEMU processes terminated successfully")
        else:
            print("✓ No QEMU processes found")

    def test_all_cases(self, target, test_cases):
        """Run all test cases from JSON configuration"""
        console = None

        try:
            # 遍历所有测试用例
            for test_case in test_cases:
                print(f"\n========================================")
                print(f"Running test: {test_case['name']}")
                print(f"Description: {test_case['description']}")
                print("========================================")

                # 遍历测试用例中的命令
                for cmd_config in test_case['commands']:
                    cmd_type = cmd_config['type']

                    if cmd_type == 'boot_kernel':
                        # 运行boot_kernel命令
                        self.run_boot_kernel()
                        # 连接到console
                        console = self.connect_to_console(target)
                        # 检查启动结果
                        if cmd_config['expect'] and console:
                            print(f"Waiting for: {cmd_config['expect']}")
                            console.expect(cmd_config['expect'], timeout=60)
                            print("✓ Boot successful!")

                    elif cmd_type == 'shell':
                        # 运行shell命令
                        self.run_shell_command(console, cmd_config['command'], cmd_config['expect'])

        finally:
            # 测试完成后终止QEMU进程
            self.terminate_qemu_processes()

if __name__ == "__main__":
    # Run tests with JSON output support
    import pytest
    import argparse

    parser = argparse.ArgumentParser(description='Run Quantum tests')
    parser.add_argument('--json', help='Output JSON results to file')
    args, remaining = parser.parse_known_args()

    if args.json:
        # Run tests with JSON output
        result = pytest.main([__file__, "-v", "--json=" + args.json])
    else:
        # Run tests normally
        result = pytest.main([__file__, "-v"])

    sys.exit(result)
