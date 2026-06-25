# Contributing to Financial Data Mart

感谢你对本项目的关注！以下是参与贡献的指南。

## 如何提交 Issue

1. 在 GitHub Issues 页面点击 "New Issue"
2. 选择合适的模板 (Bug Report / Feature Request)
3. 清晰描述问题或建议，包括：
   - 问题复现步骤
   - 期望行为 vs 实际行为
   - 环境信息 (OS, Python 版本, Docker 版本)

## 如何提交 Pull Request

1. Fork 本仓库
2. 创建特性分支: `git checkout -b feature/your-feature`
3. 提交更改: `git commit -m 'Add some feature'`
4. 推送到分支: `git push origin feature/your-feature`
5. 创建 Pull Request

## 开发环境配置

### 前置要求
- Python 3.10+
- Docker & Docker Compose
- Git

### 本地开发

```bash
# 1. 克隆仓库
git clone https://github.com/wscgx/Financial-Data-Mart.git
cd Financial-Data-Mart/project

# 2. 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. 安装依赖
pip install -r requirements_bigdata.txt

# 4. 启动 Docker 服务
cd docker
docker compose up -d
```

## 代码规范

### Python
- 遵循 PEP 8 规范
- 使用 4 空格缩进
- 函数和类必须有文档字符串
- 中文注释用于业务逻辑说明

### SQL
- 关键字大写: `SELECT`, `FROM`, `WHERE`
- 表名和字段名使用下划线命名
- 必须包含中文注释

### 提交信息
- 使用中文描述
- 格式: `<type>: <description>`
- 类型: `feat`, `fix`, `docs`, `style`, `refactor`

## 项目结构

```
Financial Data Mart/
├── project/
│   ├── app.py              # Streamlit 入口
│   ├── etl/                # ETL 脚本
│   ├── sql/                # SQL 建表语句
│   ├── dashboards/         # 可视化看板
│   ├── scripts/            # 工具脚本
│   └── docker/             # Docker 配置
└── scripts/                # 启动脚本
```

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。
