#!/bin/bash
# QEMU 测试报告生成
# 使用 allure-pytest + allure CLI 生成看板报告
# source 此文件后可使用 labgrid_test 函数

# 显示帮助信息
_labgrid_test_help() {
    echo "Usage: labgrid_test <command> [--no-report]"
    echo ""
    echo "Commands:"
    echo "  all           运行所有测试"
    echo "  <test_py>     指定运行某个测试文件 (如 test_system, test_slt)"
    echo "  help          显示此帮助信息"
    echo ""
    echo "Options:"
    echo "  --no-report   跳过 allure 报告生成"
    echo ""
    echo "Available tests:"
    local labgrid_dir="$PROJECT_ROOT/labgrid_test/labgrid_qemu"
    for f in "${labgrid_dir}"/test_*.py; do
        echo "  $(basename "$f" .py)"
    done
}

# 运行 labgrid QEMU 测试并生成 allure 报告
# Usage: labgrid_test <command> [--no-report]
#   无参数时显示帮助
#   all       运行所有测试
#   <test_py> 指定运行某个测试 (如 test_system)
#   --no-report 跳过 allure 报告生成
labgrid_test() {
    local labgrid_dir="$PROJECT_ROOT/labgrid_test/labgrid_qemu"
    local venv_pytest="$PROJECT_ROOT/.venv/bin/pytest"
    local allure_bin="${labgrid_dir}/tools/allure-2.29.0/bin/allure"
    local env_file="labgrid-env.yaml"
    local allure_dir="${BOARD_OUT_DIR}/allure/results"
    local allure_report="${BOARD_OUT_DIR}/allure/report"

    # 解析参数
    local skip_report=0
    local test_target=""

    while [ $# -gt 0 ]; do
        case "$1" in
            --no-report)
                skip_report=1
                shift
                ;;
            help|--help|-h)
                _labgrid_test_help
                return 0
                ;;
            all)
                test_target="all"
                shift
                ;;
            test_*)
                test_target="$1"
                shift
                ;;
            *)
                echo "Error: unknown argument '$1'"
                _labgrid_test_help
                return 1
                ;;
        esac
    done

    # 无参数时显示帮助
    if [ -z "${test_target}" ]; then
        _labgrid_test_help
        return 0
    fi

    # 校验指定的测试文件是否存在
    if [ "${test_target}" != "all" ]; then
        if [ ! -f "${labgrid_dir}/${test_target}.py" ]; then
            echo "Error: test file '${test_target}.py' not found in ${labgrid_dir}"
            _labgrid_test_help
            return 1
        fi
    fi

    # 安装 allure CLI（如果不存在且需要生成报告）
    if [ $skip_report -eq 0 ]; then
        if [ ! -x "${allure_bin}" ]; then
            local tar="/tmp/allure-2.29.0.tgz"
            if [ ! -f "${tar}" ] || [ "$(wc -c < "${tar}")" -lt 10000000 ]; then
                echo "Downloading allure CLI..."
                curl -L --connect-timeout 10 --max-time 600 \
                    "https://github.com/allure-framework/allure2/releases/download/2.29.0/allure-2.29.0.tgz" \
                    -o "${tar}"
            fi
            mkdir -p "${labgrid_dir}/tools"
            tar -xzf "${tar}" -C "${labgrid_dir}/tools/"
            chmod +x "${allure_bin}"
            echo "Allure CLI installed to ${allure_bin}"
        fi
    fi

    # 清理旧数据
    rm -rf "${allure_dir}" "${allure_report}"
    mkdir -p "${allure_dir}"

    # 构建 pytest 目标
    local pytest_target=""
    if [ "${test_target}" = "all" ]; then
        pytest_target=""
        echo "========================================"
        echo "  Running ALL labgrid QEMU tests..."
        echo "========================================"
    else
        pytest_target="${test_target}.py"
        echo "========================================"
        echo "  Running labgrid QEMU test: ${test_target}"
        echo "========================================"
    fi

    local saved_pwd="$(pwd)"
    cd "${labgrid_dir}"

    ${venv_pytest} \
        ${pytest_target} \
        -v \
        --lg-env "${env_file}" \
        --alluredir="${allure_dir}" \
        --clean-alluredir \
        --tb=short \
        -s \
        2>&1 | tee "${allure_dir}/console.log"

    local exit_code=${PIPESTATUS[0]}

    echo ""
    echo "========================================"
    if [ ${exit_code} -eq 0 ]; then
        echo "  ALL TESTS PASSED"
    else
        echo "  SOME TESTS FAILED (exit code: ${exit_code})"
    fi
    echo "========================================"
    echo ""

    # 生成 allure 报告
    if [ $skip_report -eq 0 ]; then
        echo "Generating allure report..."
        "${allure_bin}" generate "${allure_dir}" -o "${allure_report}" --clean

        echo ""
        echo "========================================"
        echo "  Report: file://${allure_report}/index.html"
        echo "========================================"
    fi

    cd "${saved_pwd}"
    return ${exit_code}
}

export -f labgrid_test
export -f _labgrid_test_help
