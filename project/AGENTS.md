# AI智能财富分析平台 - 开发规范

## 需求理解规范（强制）

### 核心原则：以产品经理思维理解需求

用户的表述可能不使用技术专业术语，而是用**业务语言、口语化描述、甚至模糊的需求方向**。AI 必须主动将用户需求翻译为技术方案，而非要求用户用技术语言描述。

### 需求理解流程

```
用户原始表述 → 业务意图提取 → 技术方案设计 → 确认后执行
```

### 示例对照表

| 用户原始表述 | 业务意图理解 | 技术实现 |
|---|---|---|
| "数据量大时会卡" | 前端查询性能优化 | 将 `SELECT *` 改为精确列查询 |
| "这个不合理，需要优化" | 架构设计不符合规范 | 分析问题根因，提出改进方案 |
| "落地到本地" | 执行 ETL 并写入本地 MySQL | 运行建表+数据加载脚本 |
| "所有东西塞一个文件里" | 代码可维护性差 | 拆分为模块化结构 |
| "帮我查一下" | 查询数据库获取结果 | 编写 SQL 并返回数据 |
| "加个筛选" | 前端增加交互筛选条件 | 在侧边栏添加 selectbox 组件 |
| "跑不通" | 代码执行报错 | 排查错误原因并修复 |
| "数据不对" | ETL 逻辑或数据质量问题 | 校验数据完整性+正确性 |
| "换个展示方式" | 调整前端图表类型或布局 | 修改 Plotly 图表配置 |

### 强制要求

1. **不反问用户技术细节**：用户说"数据量大时会卡"，不要问"你是说 SELECT * 导致的吗？"，而是直接分析并给出方案
2. **主动补全隐含需求**：用户说"优化一下"，主动分析可优化的点并提出建议
3. **用业务语言确认**：提出方案时用通俗语言描述，而非直接甩技术方案
4. **多想一步**：用户说"加个字段"，主动思考是否需要同步更新 DDL、ETL、前端展示、Mapping 文档

### 确认机制

当需求存在多种理解方式时，用简洁的业务语言向用户确认，而非直接执行：

```
理解为：优化 DWS 层的数据来源，不再直接读 ODS 表，而是通过 DWD 层加工。
是否正确？
```

## 数仓表命名规范

### 层级前缀
- `ods_` - 操作数据层（原始数据）
- `dwd_` - 数据仓库明细层（清洗后的明细数据）
- `dws_` - 数据仓库汇总层（轻度汇总宽表）
- `ads_` - 应用数据层（面向应用的指标表）

### 命名格式
- 格式：`{层级前缀}_{主题域}_{业务含义}_{粒度/频率}`
- 示例：`dwd_customer_asset_daily`（客户资产日快照表）

## 强制要求：中文注释

### 所有新建表必须包含中文注释（DDL文件 + MySQL数据库）

#### 1. DDL文件中的注释
- 在DDL文件顶部添加中文注释，说明表的业务含义
- 格式：`-- {层级} Layer: {table_name}`
- 格式：`-- {中文表名}`
- 每个字段后必须添加行内注释：`字段名 数据类型, -- {中文注释}`

#### 2. MySQL 原生 COMMENT 语法（强制）
- **所有落地到 MySQL 的表，必须使用 MySQL 原生 COMMENT 语法**
- 表级注释：`CREATE TABLE ... COMMENT='中文表名'`
- 字段级注释：每个字段后必须使用 `COMMENT '中文注释'`
- 示例：
  ```sql
  CREATE TABLE IF NOT EXISTS dwd_product_sales_daily (
      stat_date VARCHAR(20) COMMENT '统计日期',
      product_id VARCHAR(50) COMMENT '产品ID',
      ...
      PRIMARY KEY (stat_date, product_id)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='产品销售日汇总表';
  ```

#### 3. 元数据表注释
- 所有表和字段的中文注释必须同步写入 `table_comment_metadata` 元数据表
- 使用 `add_table_comments.py` 脚本或直接在ETL中插入

#### 4. MySQL 注释验证
- ETL 加载到 MySQL 后，必须验证表和字段的注释已正确写入
- 验证 SQL：`SHOW FULL COLUMNS FROM {table_name}` 检查 Comment 列
- 验证 SQL：`SHOW TABLE STATUS WHERE Name = '{table_name}'` 检查 Comment 列

## DDL生成规范

### 目标数据库
- 所有DDL建表语句必须使用 **MySQL** 语法
- 禁止生成 SQLite 兼容的建表语句

### 数据类型映射
- 字符串类型使用 `VARCHAR(n)` 或 `TEXT`
- 数值类型使用 `DECIMAL(m,n)` 或 `DOUBLE`
- 日期时间类型使用 `DATETIME` 或 `DATE`
- 整数类型使用 `INT` 或 `BIGINT`

### 表选项
- 必须指定字符集：`DEFAULT CHARSET=utf8mb4`
- 必须指定存储引擎：`ENGINE=InnoDB`
- 必须包含表注释：`COMMENT='中文表名'`

### 来源信息字段（强制）
- **所有 DWD/DWS/ADS 层新建表，必须包含 `dm_src_info` 字段**
- **用途**：记录该表的主要数据来源表（主表）
- **位置**：放在业务字段之后、`etl_load_time` 之前
- **数据类型**：`VARCHAR(100)`
- **示例值**：`ods_transaction`、`dwd_customer_asset_daily` 等
- **说明**：如果数据来自多张表，填写最主要的主表表名；如果是多表JOIN后的结果，填写驱动表或核心事实表

### 字段注释
- 每个字段后必须使用 `COMMENT '中文注释'` 语法

### 示例DDL

```sql
-- DWD Layer: dwd_customer_asset_daily
-- 客户资产日快照表

CREATE TABLE IF NOT EXISTS dwd_customer_asset_daily (
    stat_date VARCHAR(10) COMMENT '统计日期',
    customer_id VARCHAR(50) COMMENT '客户ID',
    account_id VARCHAR(50) COMMENT '账户ID',
    holding_market_value DECIMAL(18,2) COMMENT '持仓市值',
    purchase_amount DECIMAL(18,2) COMMENT '申购金额',
    redemption_amount DECIMAL(18,2) COMMENT '赎回金额',
    profit_loss DECIMAL(18,2) COMMENT '盈亏',
    net_asset_change DECIMAL(18,2) COMMENT '资产净变动',
    dm_src_info VARCHAR(100) COMMENT '数据来源表',
    etl_load_time DATETIME COMMENT 'ETL加载时间',
    PRIMARY KEY (stat_date, customer_id, account_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='客户资产日快照表';
```

### 元数据插入示例

```sql
INSERT INTO table_comment_metadata (table_name, column_name, comment_type, comment_text) VALUES
('dwd_customer_asset_daily', '', 'table', '客户资产日快照表'),
('dwd_customer_asset_daily', 'stat_date', 'column', '统计日期'),
('dwd_customer_asset_daily', 'customer_id', 'column', '客户ID'),
...
```

## ETL脚本规范

- 文件命名：`etl_{目标表名}.sql`
- 文件位置：`project/etl/`
- 脚本顶部必须包含注释说明数据来源和目标表

## 数据分层依赖规范（强制）

### 核心原则：事实数据必须逐层加工，禁止跨层引用

```
ODS 事实表 → DWD 明细层 → DWS 汇总层 → ADS 应用层
    ↓              ↓              ↓
ODS 维度表 ──────→ JOIN ────────→ JOIN（维度查找，允许）
```

### DWS 层数据来源规范

- **DWS 层的事实数据（交易金额、交易笔数、持仓市值、AUM 等）必须来自 DWD 层**
- **禁止 DWS 层 ETL 直接从 ODS 事实表（如 `ods_transaction`、`ods_holding`）读取事实数据**
- **ODS 维度表（如 `ods_customer`、`ods_product`）可以在 DWS 层作为维度查找使用**（取姓名、城市、产品名、产品风险等级等属性）

### 判断标准

| 引用类型 | 示例 | DWS 层是否允许 |
|---------|------|---------------|
| ODS 事实表 | `ods_transaction`、`ods_holding` | 禁止 |
| ODS 维度表 | `ods_customer`（取姓名）、`ods_product`（取产品名/风险等级） | 允许 |
| DWD 层 | `dwd_customer_activity_daily`、`dwd_customer_asset_daily` | 必须 |

### 违规示例

```sql
-- 错误：DWS 层直接从 ODS 事实表聚合交易数据
SELECT SUM(t.amount) FROM ods_transaction t ...  -- 跨层！
```

### 正确示例

```sql
-- 正确：DWS 层从 DWD 层聚合，同时 JOIN ODS 维度表获取客户姓名
SELECT
    SUM(d.purchase_amount) AS total_purchase,  -- 来自 DWD
    c.customer_name                             -- 来自 ODS 维度表
FROM dwd_customer_activity_daily d
JOIN ods_customer c ON d.customer_id = c.customer_id
```

### 补充说明

- 若某类数据没有对应的 DWD 层表，**必须先创建 DWD 层表**，再在 DWS 层引用
- `dm_src_info` 字段必须填写直接来源表名，用于追溯数据血缘
- ADS 层同理：事实数据优先来自 DWS/DWD 层，维度查找可引用 ODS

## 数据落地规范

- 所有需求必须将数据实际写入 MySQL 数据库才算完成
- DDL 执行后需验证表结构已创建
- ETL 执行后需验证目标表有数据写入
- 提供数据查询结果作为完成凭证

## Mapping 文档规范

### 强制要求
- **每次落地到 MySQL 的表，必须同步生成两类 Mapping 文档**
- **按需求选项分文件夹存放**，每个选项一个独立文件夹

### 文件夹结构
```
project/docs/mapping/
├── option_a/                          # 选项A：客户资产价值分析体系
│   ├── mapping_option_a.md            # 需求概览文档
│   ├── mapping_dwd_customer_asset_daily.csv
│   ├── mapping_dws_customer_value_profile.csv
│   └── mapping_ads_*.csv              # 各ADS层表的CSV
├── option_b/                          # 选项B：产品销售与业绩分析
│   ├── mapping_option_b.md
│   ├── mapping_dwd_product_sales_daily.csv
│   └── ...
└── option_{x}/                        # 后续选项按此结构
    └── ...
```

### 类型1：需求概览文档（MD格式）
- **用途**：查看整个需求的整体情况（数据流向、涉及表清单、整体加工逻辑）
- **文件命名**：`mapping_{需求标识}.md`
- **文件位置**：`project/docs/mapping/{需求标识}/`
- **示例**：`project/docs/mapping/option_b/mapping_option_b.md`

#### MD文档必须包含的内容
1. **基本信息**：需求名称、需求标识、创建日期、最后更新
2. **数据流向图**：使用文本箭头表示 `ODS → DWD → DWS → ADS` 的数据流向
3. **涉及表清单**：列出所有源表和目标表
4. **加工逻辑概览**：每张目标表的核心加工逻辑摘要
5. **ETL脚本清单**：所有相关ETL脚本文件列表

### 类型2：表级映射文档（CSV格式）
- **用途**：单表的详细字段映射和加工逻辑（可供Excel打开）
- **文件命名**：`mapping_{表名}.csv`
- **文件位置**：`project/docs/mapping/{需求标识}/`
- **示例**：`project/docs/mapping/option_b/mapping_dwd_product_sales_daily.csv`
- **按照表的粒度落地，一张表一个CSV文件**

#### CSV 文件结构（每张表一个CSV）

##### 第1部分：表基本信息（前7行）
```
字段,值
需求名称,产品销售与业绩分析
需求标识,option_b
表名,dwd_product_sales_daily
中文表名,产品销售日汇总表
层级,DWD
创建日期,2026-06-10
```

##### 第2部分：表结构（空一行后）
```
字段名,数据类型,中文注释,是否主键,是否可空,默认值,计算逻辑
stat_date,VARCHAR(20),统计日期,是,否,,
product_id,VARCHAR(50),产品ID,是,否,,
...
```

##### 第3部分：加工逻辑（空一行后）
```
加工逻辑项,说明
数据来源,"ods_transaction, ods_product, ods_account"
关联条件,ods_transaction.product_id = ods_product.product_id
过滤条件,transaction_type IN ('purchase', 'redemption') AND is_current = 1
聚合粒度,transaction_date + product_id
更新策略,"全量刷新，日频"
ETL脚本,etl/etl_dwd_product_sales_daily.sql
```

### CSV 编码
- 使用 UTF-8-BOM 编码，确保 Excel 正确显示中文

## 数据质量校验

- 所有ETL完成后必须运行数据质量校验
- 校验脚本位置：`project/sql/data_quality_validation.sql`
- 执行脚本：`project/scripts/run_quality_validation.py`

### 校验结果落地规范
- 校验结果必须保存为 CSV 文件到 `project/data/quality_reports/` 目录
- 文件命名格式：`quality_report_YYYYMMDD_HHMMSS.csv`
- 同时生成最新报告软链接：`quality_report_latest.csv`
- CSV 文件使用 UTF-8-BOM 编码，确保 Excel 正确显示中文
- 校验结果字段：`check_name`, `description`, `failed_records`, `status`, `check_time`

## 前端展示规范

### 强制要求：前端展示字段必须使用中文
- **所有前端页面展示的字段名、表头、标签、提示信息等，必须使用中文**
- **禁止在前端页面中直接展示英文字段名**（如 `stat_date`、`customer_id`、`total_aum` 等）
- 字段中文名来源：对应数据库字段的 `COMMENT` 注释
- 示例：
  - ❌ 错误：表格列头显示 `stat_date`、`total_aum`、`customer_count`
  - ✅ 正确：表格列头显示 `统计日期`、`平台总AUM`、`客户数`

### 实现方式
- 前端开发时，必须从数据库字段注释或 Mapping 文档中获取中文名称
- 如使用 Echarts 等可视化库，图表的 xAxis、yAxis、legend、tooltip 等均需使用中文
- BI 看板（如 SmartBI）中的指标名称、维度名称必须配置为中文

### 例外情况
- 仅在技术调试日志、开发者控制台输出中可保留英文字段名
- 面向业务用户、管理层的所有展示界面必须100%中文化

## 编码规范

- 数据库使用 UTF-8MB4 编码
- 所有DDL必须指定 `DEFAULT CHARSET=utf8mb4`
- 使用 Python 脚本处理中文数据插入
