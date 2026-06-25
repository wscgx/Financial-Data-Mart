import streamlit as st
import subprocess
import sys
import os
import io

from dashboards.option_a import render_option_a
from dashboards.option_b import render_option_b
from dashboards.option_c import render_option_c
from dashboards.option_d import render_option_d
from dashboards.option_e import render_option_e

st.set_page_config(page_title="AI智能财富分析平台", page_icon="📊", layout="wide")

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), 'scripts')
TESTS_DIR = os.path.join(os.path.dirname(__file__), 'tests')

# ── 侧边栏 ──────────────────────────────────────────────────
st.sidebar.header("📊 看板选择")
dashboard = st.sidebar.radio("选择看板", [
    "选项A: 客户资产价值",
    "选项B: 产品销售与业绩",
    "选项C: 客户风险匹配度",
    "选项D: 客户交易行为",
    "选项E: 综合财富管理驾驶舱",
    "运维工具",
])


def run_cmd(cmd, cwd=None):
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    result = subprocess.run(
        cmd, capture_output=True, cwd=cwd, env=env,
    )
    stdout = result.stdout.decode('utf-8', errors='replace')
    stderr = result.stderr.decode('utf-8', errors='replace')
    return result.returncode, stdout, stderr


# ── 主内容 ───────────────────────────────────────────────────
if dashboard == "选项A: 客户资产价值":
    render_option_a()
elif dashboard == "选项B: 产品销售与业绩":
    render_option_b()
elif dashboard == "选项C: 客户风险匹配度":
    render_option_c()
elif dashboard == "选项D: 客户交易行为":
    render_option_d()
elif dashboard == "选项E: 综合财富管理驾驶舱":
    render_option_e()

elif dashboard == "运维工具":
    st.title("🔧 运维工具")

    # ── Docker 服务管理 ──────────────────────────────────────
    st.subheader("🐳 Docker 大数据服务")
    st.caption("一键启动/停止 Spark、MinIO、Airflow、Kafka、Flink、Grafana 等服务")

    DOCKER_DIR = os.path.join(os.path.dirname(__file__), 'docker')

    def find_docker_compose():
        """检测 docker compose 命令，兼容新旧版本"""
        # 优先尝试 docker compose (V2)
        code, _, _ = run_cmd(["docker", "compose", "version"])
        if code == 0:
            return ["docker", "compose"]
        # 回退到 docker-compose (V1)
        code, _, _ = run_cmd(["docker-compose", "version"])
        if code == 0:
            return ["docker-compose"]
        return None

    docker_bin = find_docker_compose()

    if docker_bin is None:
        st.warning("Docker 未安装或不在 PATH 中，请先安装 Docker Desktop")
        st.markdown("""
        **安装步骤:**
        1. 下载 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
        2. 安装并启动 Docker Desktop
        3. 确认 `docker --version` 能正常输出
        4. 重启本应用
        """)
    else:
        def docker_cmd(action):
            cmd = docker_bin + [action]
            code, stdout, stderr = run_cmd(cmd, cwd=DOCKER_DIR)
            return code, stdout, stderr

        def get_docker_status():
            code, stdout, _ = run_cmd(docker_bin + ["ps", "--format", "{{.Names}}|{{.Status}}"], cwd=DOCKER_DIR)
            services = []
            if code == 0 and stdout.strip():
                for line in stdout.strip().split('\n'):
                    if '|' in line:
                        parts = line.split('|', 1)
                        if len(parts) == 2:
                            services.append({
                                "name": parts[0].strip(),
                                "status": parts[1].strip(),
                            })
            return services

        svc_col1, svc_col2, svc_col3, svc_col4 = st.columns(4)

        with svc_col1:
            if st.button("▶ 启动全部服务", type="primary", key='docker_up'):
                with st.spinner("正在启动 Docker 服务..."):
                    code, stdout, stderr = docker_cmd("up -d")
                if code == 0:
                    st.success("服务启动成功!")
                else:
                    st.error(f"启动失败: {stderr[:300]}")
                st.rerun()

        with svc_col2:
            if st.button("⏹ 停止全部服务", key='docker_down'):
                with st.spinner("正在停止 Docker 服务..."):
                    code, stdout, stderr = docker_cmd("down")
                if code == 0:
                    st.success("服务已停止")
                else:
                    st.error(f"停止失败: {stderr[:300]}")
                st.rerun()

        with svc_col3:
            if st.button("🔄 重启全部服务", key='docker_restart'):
                with st.spinner("正在重启 Docker 服务..."):
                    code, stdout, stderr = docker_cmd("restart")
                if code == 0:
                    st.success("服务已重启")
                else:
                    st.error(f"重启失败: {stderr[:300]}")
                st.rerun()

        with svc_col4:
            if st.button("📋 刷新状态", key='docker_status'):
                st.rerun()

        # 显示服务状态
        services = get_docker_status()
        if services:
            st.markdown("**服务状态说明:**")
            st.caption("🟢 绿色 = 运行中 (Up)  |  🔴 红色 = 已停止 (Exited)  |  🟡 黄色 = 启动中 (Starting)")
            st.markdown("")
            
            # 使用表格显示服务状态
            st.markdown("**服务列表:**")
            
            # 定义服务端口映射
            service_ports = {
                "fin_mysql": "3307",
                "fin_minio": "9000/9001",
                "fin_kafka": "9092",
                "fin_grafana": "3000",
                "fin_prometheus": "9090",
                "fin_postgres": "5432",
                "fin_zookeeper": "2181",
                "fin_flink_jobmanager": "8081",
                "fin_flink_taskmanager": "-",
                "fin_schema_registry": "8081",
                "fin_airflow_webserver": "8080",
                "fin_airflow_scheduler": "-",
                "fin_airflow_init": "-",
            }
            
            for svc in services:
                name = svc.get("name", "")
                status = svc.get("status", "")
                is_running = "Up" in status
                is_starting = "Starting" in status or "created" in status.lower()
                port = service_ports.get(name, "-")
                
                # 显示状态
                if is_running:
                    st.success(f"**{name}** - 运行中 | 端口: {port} | {status}")
                elif is_starting:
                    st.warning(f"**{name}** - 启动中 | 端口: {port} | {status}")
                else:
                    st.error(f"**{name}** - 已停止 | 端口: {port} | {status}")
        else:
            st.info("暂无运行中的 Docker 服务，点击「启动全部服务」开始")

        # 服务访问链接
        st.markdown("---")
        st.markdown("**🔗 服务访问地址（点击跳转）:**")

        # 定义所有可访问的服务
        service_links = [
            {"name": "Grafana 监控", "url": "http://localhost:3000", "port": "3000", "icon": "📊"},
            {"name": "Prometheus 指标", "url": "http://localhost:9090", "port": "9090", "icon": "📈"},
            {"name": "MinIO 控制台", "url": "http://localhost:9001", "port": "9001", "icon": "🪣"},
            {"name": "MinIO API", "url": "http://localhost:9000", "port": "9000", "icon": "🔗"},
            {"name": "MySQL 数据库", "url": "localhost:3307", "port": "3307", "icon": "🗄️"},
            {"name": "Kafka Broker", "url": "localhost:9092", "port": "9092", "icon": "📨"},
            {"name": "Flink Web UI", "url": "http://localhost:8082", "port": "8082", "icon": "⚡"},
            {"name": "Airflow Webserver", "url": "http://localhost:8180", "port": "8180", "icon": "🌊"},
        ]

        # 使用 st.columns 布局，每行4个
        for i in range(0, len(service_links), 4):
            row = service_links[i:i+4]
            cols = st.columns(4)
            for j, svc in enumerate(row):
                with cols[j]:
                    # 检查服务是否在运行
                    running_names = [s.get("name", "") for s in services if "Up" in s.get("status", "")]
                    is_running = any(svc["port"] in service_ports.get(name, "") for name in running_names)

                    status_dot = "🟢" if is_running else "🔴"
                    st.markdown(
                        f'{status_dot} **{svc["icon"]} {svc["name"]}**  \n'
                        f'端口: {svc["port"]}  \n'
                        f'[{svc["url"]}]({svc["url"]})',
                        unsafe_allow_html=True
                    )

    st.divider()

    # ── ETL 执行 ─────────────────────────────────────────────
    st.subheader("ETL 数据加工")
    etl_col1, etl_col2 = st.columns([1, 1])

    with etl_col1:
        etl_option = st.multiselect(
            "选择业务选项",
            ['a', 'b', 'c', 'd', 'e'],
            default=['a', 'b', 'c', 'd', 'e'],
            key='etl_option',
        )
    with etl_col2:
        skip_ddl = st.checkbox("跳过 DDL 建表", key='skip_ddl')

    if st.button("▶ 执行全量 ETL", type="primary", key='run_etl'):
        with st.spinner("ETL 执行中，请稍候..."):
            cmd = [sys.executable, os.path.join(SCRIPTS_DIR, 'run_all_etl.py')]
            if etl_option:
                cmd += ['--option'] + etl_option
            if skip_ddl:
                cmd += ['--skip-ddl']
            code, stdout, stderr = run_cmd(cmd)
        if code == 0:
            st.success("ETL 执行完成")
        else:
            st.error(f"ETL 执行失败 (exit {code})")
        with st.expander("执行日志", expanded=code != 0):
            st.code(stdout + stderr, language='text')

    st.divider()

    # ── 质量校验 ─────────────────────────────────────────────
    st.subheader("数据质量校验")
    if st.button("▶ 执行质量校验", key='run_quality'):
        with st.spinner("质量校验中..."):
            cmd = [sys.executable, os.path.join(SCRIPTS_DIR, 'run_quality_validation.py')]
            code, stdout, stderr = run_cmd(cmd)
        if code == 0:
            st.success("质量校验完成")
        else:
            st.error(f"质量校验失败 (exit {code})")
        with st.expander("校验日志", expanded=code != 0):
            st.code(stdout + stderr, language='text')

    st.divider()

    # ── 单元测试 ─────────────────────────────────────────────
    st.subheader("单元测试")
    if st.button("▶ 运行测试", key='run_tests'):
        with st.spinner("测试执行中..."):
            cmd = [sys.executable, '-m', 'unittest', 'discover',
                   '-s', TESTS_DIR, '-v']
            code, stdout, stderr = run_cmd(cmd)
        if code == 0:
            st.success("全部测试通过")
        else:
            st.error(f"测试失败 (exit {code})")
        with st.expander("测试日志", expanded=code != 0):
            st.code(stdout + stderr, language='text')
