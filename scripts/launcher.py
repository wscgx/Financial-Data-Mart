import os
import subprocess
import sys
import webbrowser
import time
import socket

# 切换到project目录
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.join(script_dir, "project")
os.chdir(project_dir)

# 创建streamlit配置
config_dir = os.path.expanduser("~/.streamlit")
os.makedirs(config_dir, exist_ok=True)
config_file = os.path.join(config_dir, "config.toml")

config_content = """[server]
headless = false
address = "localhost"
port = 8501

[browser]
gatherUsageStats = false
"""

need_write = True
if os.path.exists(config_file):
    with open(config_file, "r", encoding="utf-8") as f:
        existing = f.read()
    if "gatherUsageStats = false" in existing:
        need_write = False

if need_write:
    with open(config_file, "w", encoding="utf-8") as f:
        f.write(config_content)

print("=" * 50)
print("  AI智能财富分析平台 - 前端服务启动中...")
print("=" * 50)
print()
print("正在启动服务，请稍候...")
print("服务地址: http://localhost:8501")
print()
print("关闭此窗口可停止服务")
print("=" * 50)
print()

# 启动streamlit（禁止自动打开浏览器）
proc = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app.py", "--server.headless", "true"])

# 等待服务就绪
print("等待服务启动...")
for i in range(30):
    time.sleep(0.5)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(("localhost", 8501))
        sock.close()
        if result == 0:
            print("服务已就绪！")
            break
    except:
        pass
else:
    print("警告: 服务启动超时，但仍尝试打开浏览器...")

# 打开浏览器
try:
    webbrowser.open("http://localhost:8501")
    print("已自动打开浏览器...")
except:
    print("请手动打开浏览器访问: http://localhost:8501")

# 等待进程结束
proc.wait()
