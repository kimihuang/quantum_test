#!/bin/bash
"""
Run tests and generate report for Quantum project
"""

set -e

# 脚本目录
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
PROJECT_ROOT=$(dirname "$(dirname "$SCRIPT_DIR")")

# 输出目录
OUTPUT_DIR="$PROJECT_ROOT/out/quantum_qemu_debug"
TEST_RESULTS_DIR="$SCRIPT_DIR/results"
REPORT_DIR="$SCRIPT_DIR/reports"

# 创建目录
mkdir -p "$TEST_RESULTS_DIR"
mkdir -p "$REPORT_DIR"

# 检查构建产物
if [ ! -f "$OUTPUT_DIR/images/Image" ] || [ ! -f "$OUTPUT_DIR/images/rootfs.cpio" ]; then
    echo "错误: 构建产物不存在，请先构建项目"
    echo "请运行: source build/envsetup.sh && lunch quantum_qemu_debug && make"
    exit 1
fi

# 检查QEMU是否安装
if ! command -v qemu-system-aarch64 >/dev/null 2>&1; then
    echo "错误: qemu-system-aarch64 未安装"
    exit 1
fi

# 激活项目虚拟环境
if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    echo "激活项目虚拟环境..."
    source "$PROJECT_ROOT/.venv/bin/activate"
    echo "已激活虚拟环境: .venv"
else
    echo "警告: 虚拟环境不存在，创建新的虚拟环境..."
    python3 -m venv "$PROJECT_ROOT/.venv"
    source "$PROJECT_ROOT/.venv/bin/activate"
    echo "已创建并激活虚拟环境: .venv"
fi

# 检查并安装labgrid及其依赖项
echo "检查labgrid及其依赖项..."
pip install --upgrade pip
pip install labgrid pytest pytest-json

echo "labgrid及其依赖项安装完成"


# 运行测试
echo "========================================"
echo "运行 Quantum 测试"
echo "========================================"

# 运行测试并生成JSON结果
python3 "$SCRIPT_DIR/test_quantum.py" --json="$TEST_RESULTS_DIR/test_results.json"

# 生成测试报告
echo "========================================"
echo "生成测试报告"
echo "========================================"

python3 "$SCRIPT_DIR/generate_report.py" --results="$TEST_RESULTS_DIR/test_results.json" --output="$REPORT_DIR"

# 显示报告路径
echo "========================================"
echo "测试完成"
echo "========================================"
echo "HTML报告: $REPORT_DIR/test_report.html"
echo "JSON报告: $REPORT_DIR/test_report.json"
echo ""
echo "可以使用浏览器打开HTML报告查看详细结果"
