"""linux-slt (System Level Test) 功能测试

slt 是一个系统级测试框架，slt_daemon 通过 TCP 端口接收上位机命令，
执行 Shell 命令并进行模式匹配，返回测试结果。

SLT 命令协议:
  命令格式: $$<测试名称> -v -c "<shell命令>" -p "<匹配模式>" -t <超时ms>^^
  结果格式: $&CMD_ID:xxx;EXIT_CODE:0;PATTERN_MATCHED:1;EXEC_TIME:10ms^^

测试方法:
  slt_daemon 以 TCP 模式运行在 Guest 内 (0.0.0.0:9999)，
  通过 ShellDriver 在 Guest 内用 nc 发送 SLT 命令并读取结果。
"""

import re
import pytest
import allure
from labgrid.driver.shelldriver import ShellDriver


# ==================== SLT 协议常量 ====================
SLT_CMD_START = "$$"
SLT_CMD_END = "^^"
SLT_RESULT_START = "$&"
SLT_RESULT_END = "^^"


def send_slt_command(shell, name, shell_cmd, pattern, timeout_ms=5000, verbose=True):
    """通过 Guest 内的 nc 向 slt_daemon 发送 SLT 命令并等待结果

    Args:
        shell: ShellDriver 实例
        name: 测试名称
        shell_cmd: 要执行的 shell 命令
        pattern: 日志匹配模式
        timeout_ms: 超时时间(毫秒)
        verbose: 是否启用详细模式

    Returns:
        dict: 解析后的结果
        None: 无有效响应
    """
    # 构建 SLT 命令
    cmd = f"{SLT_CMD_START}{name}"
    if verbose:
        cmd += " -v"
    cmd += f' -c "{shell_cmd}" -p "{pattern}" -t {timeout_ms}'
    cmd += SLT_CMD_END

    # 在 Guest 内通过 nc 发送命令并读取结果
    # slt_daemon 一问一答：收到结果后关闭连接，nc 自动退出
    read_timeout = max(timeout_ms / 1000 + 3, 5)
    full_cmd = (
        f"echo -ne '{cmd}' | nc -w {int(read_timeout)} 127.0.0.1 9999"
    )

    stdout, _, _ = shell._run(full_cmd, timeout=int(read_timeout) + 10)
    raw = "\n".join(stdout)

    allure.attach(cmd, name="slt_command", attachment_type=allure.attachment_type.TEXT)
    allure.attach(raw, name="slt_raw_response", attachment_type=allure.attachment_type.TEXT)

    return parse_slt_result(raw)


def parse_slt_result(raw):
    """解析 SLT 结果字符串"""
    match = re.search(
        r'\$&(CMD_ID:[^;]+;EXIT_CODE:-?\d+;PATTERN_MATCHED:[01];EXEC_TIME:\d+ms)\^\^',
        raw
    )
    if not match:
        return None
    result_str = match.group(1)
    result = {}
    for part in result_str.split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            result[k] = v
    return result


# ==================== 测试类 ====================

@allure.feature("slt Daemon")
@allure.severity(allure.severity_level.CRITICAL)
class TestSltDaemon:
    """slt_daemon 守护进程运行状态检查"""

    def test_slt_daemon_running(self, qemu_env):
        """确认 slt_daemon 进程正在运行"""
        shell = qemu_env.get_driver(ShellDriver)
        output = shell.run_check("ps | grep slt_daemon | grep -v grep")
        assert len(output) > 0, "slt_daemon is not running"
        allure.attach(output[0], name="process", attachment_type=allure.attachment_type.TEXT)

    def test_slt_daemon_started_with_config(self, qemu_env):
        """确认 slt_daemon 以正确参数启动"""
        shell = qemu_env.get_driver(ShellDriver)
        output = shell.run_check("ps | grep slt_daemon | grep -v grep")
        text = "\n".join(output)
        assert "/etc/slt/config.yaml" in text

    def test_slt_daemon_binary_exists(self, qemu_env):
        """确认 /usr/bin/slt_daemon 可执行文件存在"""
        shell = qemu_env.get_driver(ShellDriver)
        output = shell.run_check("ls -l /usr/bin/slt_daemon")
        assert len(output) > 0

    def test_slt_daemon_help(self, qemu_env):
        """slt_daemon --help 输出包含关键信息"""
        shell = qemu_env.get_driver(ShellDriver)
        stdout, _, _ = shell._run("/usr/bin/slt_daemon --help 2>&1", timeout=3)
        text = "\n".join(stdout)
        assert "SLT" in text or "slt" in text


@allure.feature("slt Config")
class TestSltConfig:
    """slt 配置文件检查"""

    def test_config_file_exists(self, qemu_env):
        """确认 /etc/slt/config.yaml 存在"""
        shell = qemu_env.get_driver(ShellDriver)
        output = shell.run_check("ls /etc/slt/config.yaml")
        assert len(output) > 0

    def test_config_has_serial_section(self, qemu_env):
        """配置文件包含 serial 段"""
        shell = qemu_env.get_driver(ShellDriver)
        output = shell.run_check("cat /etc/slt/config.yaml")
        text = "\n".join(output)
        assert "[serial]" in text

    def test_config_has_network_section(self, qemu_env):
        """配置文件包含 network 段"""
        shell = qemu_env.get_driver(ShellDriver)
        output = shell.run_check("cat /etc/slt/config.yaml")
        text = "\n".join(output)
        assert "[network]" in text

    def test_config_network_mode_tcp(self, qemu_env):
        """配置文件 network 段配置为 TCP 模式"""
        shell = qemu_env.get_driver(ShellDriver)
        output = shell.run_check("cat /etc/slt/config.yaml")
        text = "\n".join(output)
        assert "tcp" in text.lower()
        assert "9999" in text


@allure.feature("slt Directories")
class TestSltDirectories:
    """slt 目录结构检查"""

    def test_log_directory_exists(self, qemu_env):
        """确认 /var/log/slt 目录存在"""
        shell = qemu_env.get_driver(ShellDriver)
        output = shell.run_check("ls -d /var/log/slt")
        assert len(output) > 0

    def test_log_directory_writable(self, qemu_env):
        """日志目录可写"""
        shell = qemu_env.get_driver(ShellDriver)
        output = shell.run_check("touch /var/log/slt/test_write && rm /var/log/slt/test_write && echo OK")
        assert "OK" in output[0]


@allure.feature("slt TCP Port")
@allure.severity(allure.severity_level.CRITICAL)
class TestSltTcpPort:
    """slt_daemon TCP 端口监听检查"""

    def test_tcp_port_9999_listening(self, qemu_env):
        """确认 slt_daemon 在 TCP 9999 端口监听"""
        shell = qemu_env.get_driver(ShellDriver)
        # Buildroot 无 netstat/ss，通过 /proc/net/tcp 检查
        # 端口 9999 = 0x270F
        output = shell.run_check("cat /proc/net/tcp")
        text = "\n".join(output)
        assert "270F" in text.upper(), "slt_daemon not listening on TCP port 9999"

    def test_nc_can_send_slt_command(self, qemu_env):
        """确认 nc 可以连接 slt_daemon 并收到有效响应"""
        shell = qemu_env.get_driver(ShellDriver)
        # 发送有效 SLT 命令，slt_daemon 一问一答后关闭连接
        cmd = '$$CONN_TEST -v -c "echo OK" -p "OK" -t 3000^^'
        stdout, _, exitcode = shell._run(
            f"echo -ne '{cmd}' | nc -w 3 127.0.0.1 9999",
            timeout=10
        )
        raw = "\n".join(stdout)
        allure.attach(raw, name="nc_response", attachment_type=allure.attachment_type.TEXT)
        # 能收到 $& 开头的响应即可
        assert "$&" in raw, f"Expected SLT response, got: {raw}"


@allure.feature("slt Command")
@allure.severity(allure.severity_level.CRITICAL)
class TestSltCommand:
    """SLT 命令交互测试 — 通过 TCP 发送命令验证 slt_daemon 响应"""

    def test_slt_echo_command(self, qemu_env):
        """测试基本 echo 命令: 执行成功 + 模式匹配"""
        shell = qemu_env.get_driver(ShellDriver)
        result = send_slt_command(
            shell,
            "ECHO_TEST_0001",
            "echo Hello_SLT",
            "Hello_SLT",
            timeout_ms=3000
        )
        assert result is not None, "No response from slt_daemon"
        assert result["EXIT_CODE"] == "0", f"Command failed: {result}"
        assert result["PATTERN_MATCHED"] == "1", f"Pattern not matched: {result}"
        allure.attach(str(result), name="slt_result", attachment_type=allure.attachment_type.TEXT)

    def test_slt_pattern_mismatch(self, qemu_env):
        """测试命令执行成功但模式不匹配"""
        shell = qemu_env.get_driver(ShellDriver)
        result = send_slt_command(
            shell,
            "MISMATCH_TEST_0001",
            "echo hello",
            "world",
            timeout_ms=3000
        )
        assert result is not None, "No response from slt_daemon"
        assert result["EXIT_CODE"] == "0", f"Command execution failed: {result}"
        assert result["PATTERN_MATCHED"] == "0", f"Pattern should not match: {result}"
        allure.attach(str(result), name="slt_result", attachment_type=allure.attachment_type.TEXT)

    def test_slt_command_timeout(self, qemu_env):
        """测试超时命令"""
        shell = qemu_env.get_driver(ShellDriver)
        result = send_slt_command(
            shell,
            "TIMEOUT_TEST_0001",
            "sleep 10",
            "never_match_this",
            timeout_ms=1000
        )
        assert result is not None, "No response from slt_daemon"
        assert result["PATTERN_MATCHED"] == "0", f"Timeout command should not match: {result}"
        allure.attach(str(result), name="slt_result", attachment_type=allure.attachment_type.TEXT)

    def test_slt_command_exit_code_nonzero(self, qemu_env):
        """测试命令返回非零退出码"""
        shell = qemu_env.get_driver(ShellDriver)
        result = send_slt_command(
            shell,
            "FAIL_TEST_0001",
            "exit 1",
            "anything",
            timeout_ms=3000
        )
        assert result is not None, "No response from slt_daemon"
        assert result["EXIT_CODE"] != "0", f"Command should fail: {result}"
        allure.attach(str(result), name="slt_result", attachment_type=allure.attachment_type.TEXT)

    def test_slt_multi_command_sequential(self, qemu_env):
        """测试连续发送多条命令"""
        shell = qemu_env.get_driver(ShellDriver)
        commands = [
            ("SEQ_TEST_0001", "echo first", "first"),
            ("SEQ_TEST_0002", "echo second", "second"),
            ("SEQ_TEST_0003", "echo third", "third"),
        ]
        for name, shell_cmd, pattern in commands:
            result = send_slt_command(
                shell,
                name,
                shell_cmd,
                pattern,
                timeout_ms=3000
            )
            assert result is not None, f"No response for {name}"
            assert result["EXIT_CODE"] == "0", f"Command {name} failed: {result}"
            assert result["PATTERN_MATCHED"] == "1", f"Pattern not matched for {name}: {result}"

    def test_slt_cat_cpuinfo(self, qemu_env):
        """测试读取 CPU 信息"""
        shell = qemu_env.get_driver(ShellDriver)
        result = send_slt_command(
            shell,
            "CPU_TEST_0001",
            "cat /proc/cpuinfo | head -3",
            "processor",
            timeout_ms=3000
        )
        assert result is not None, "No response from slt_daemon"
        assert result["EXIT_CODE"] == "0", f"Command failed: {result}"
        assert result["PATTERN_MATCHED"] == "1", f"Pattern not matched: {result}"
