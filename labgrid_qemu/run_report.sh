#!/bin/bash
# QEMU 测试报告生成
# 使用 allure-pytest + allure CLI 生成看板报告
# source 此文件后可使用 qemu_test 函数

# 运行 labgrid QEMU 测试并生成 allure 报告
# Usage: qemu_test [--no-report]
#   --no-report  跳过 allure 报告生成
qemu_test() {
    local labgrid_dir="$PROJECT_ROOT/labgrid_test/labgrid_qemu"
    local venv_pytest="$PROJECT_ROOT/.venv/bin/pytest"
    local allure_bin="${labgrid_dir}/tools/allure-2.29.0/bin/allure"
    local env_file="labgrid-env.yaml"
    local allure_dir="${labgrid_dir}/allure-results"
    local allure_report="${labgrid_dir}/allure-report"

    # 支持 --no-report 跳过报告生成
    local skip_report=0
    if [ "$1" = "--no-report" ]; then
        skip_report=1
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

    echo "========================================"
    echo "  Running labgrid QEMU tests..."
    echo "========================================"

    local saved_pwd="$(pwd)"
    cd "${labgrid_dir}"

    ${venv_pytest} \
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

export -f qemu_test
