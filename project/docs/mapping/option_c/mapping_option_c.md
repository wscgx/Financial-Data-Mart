# Mapping 文档：客户风险匹配度分析（选项C）

## 基本信息
| 字段 | 值 |
|------|------|
| 需求名称 | 客户风险匹配度分析 |
| 需求标识 | option_c |
| 创建日期 | 2026-06-11 |
| 最后更新 | 2026-06-11 (已落地MySQL) |

## 数据流向
```
ODS 层                    DWD 层                        DWS 层                    ADS 层
─────────────────────────────────────────────────────────────────────────────────────────────
ods_holding     ──────→   dwd_customer_risk_match   ──→  dws_risk_compliance_summary  ──→  ads_risk_mismatch_alert
ods_product               (客户风险匹配明细表)         (合规风险汇总表)             (风险错配预警清单表)
ods_risk_assessment ──┐
ods_account           ──┘
```

## 涉及表清单

### 源表（ODS层）
| 表名 | 中文表名 | 用途 |
|------|----------|------|
| ods_holding | 持仓信息表 | 提供客户持仓明细、市值等数据 |
| ods_product | 理财产品表 | 提供产品风险等级信息 |
| ods_risk_assessment | 客户风险测评表 | 提供客户风险等级、测评状态 |
| ods_account | 客户账户表 | 提供账户与客户关联关系 |
| ods_customer | 客户信息表 | 提供客户姓名等基础信息 |

### 目标表
| 层级 | 表名 | 中文表名 | Mapping CSV |
|------|------|----------|-------------|
| DWD | dwd_customer_risk_match | 客户风险匹配明细表 | mapping_dwd_customer_risk_match.csv |
| DWS | dws_risk_compliance_summary | 合规风险汇总表 | mapping_dws_risk_compliance_summary.csv |
| ADS | ads_risk_mismatch_alert | 风险错配预警清单表 | mapping_ads_risk_mismatch_alert.csv |
| ADS | ads_risk_metrics_daily | 风险指标日汇总表 | mapping_ads_risk_metrics_daily.csv |

## 加工逻辑概览

### dwd_customer_risk_match（客户风险匹配明细表）
- **数据来源**：ods_holding JOIN ods_account JOIN ods_product JOIN ods_risk_assessment
- **核心逻辑**：关联持仓、产品、风险测评数据，通过风险等级数值化比较判断是否错配，计算风险差距
- **聚合粒度**：日级 + 客户级 + 持仓级
- **详细映射**：见 `mapping_dwd_customer_risk_match.csv`

### dws_risk_compliance_summary（合规风险汇总表）
- **数据来源**：dwd_customer_risk_match JOIN ods_customer
- **核心逻辑**：按客户聚合风险匹配情况，计算错配持仓数、错配市值、错配比例、最大风险差距，判定合规状态
- **聚合粒度**：日级 + 客户级
- **详细映射**：见 `mapping_dws_risk_compliance_summary.csv`

### ads_risk_mismatch_alert（风险错配预警清单表）
- **数据来源**：dwd_customer_risk_match JOIN ods_customer
- **核心逻辑**：筛选风险错配或测评过期的记录，生成预警ID，判定预警类型和级别，生成预警信息
- **聚合粒度**：日级 + 预警级
- **详细映射**：见 `mapping_ads_risk_mismatch_alert.csv`

### ads_risk_metrics_daily（风险指标日汇总表）
- **数据来源**：dwd_customer_risk_match, dws_risk_compliance_summary, ads_risk_mismatch_alert
- **核心逻辑**：计算10个核心风险指标（错配客户数、过期率、持有率、合规占比等），统一存储在指标宽表中
- **聚合粒度**：日级 + 指标级
- **详细映射**：见 `mapping_ads_risk_metrics_daily.csv`

## ETL脚本清单
| 脚本文件 | 说明 | 转换路径 |
|----------|------|----------|
| `etl/etl_dwd_customer_risk_match.sql` | ODS → DWD ETL | ods_holding → dwd_customer_risk_match |
| `etl/etl_dws_risk_compliance_summary.sql` | DWD → DWS ETL | dwd_customer_risk_match → dws_risk_compliance_summary |
| `etl/etl_ads_risk_mismatch_alert.sql` | DWD → ADS ETL | dwd_customer_risk_match → ads_risk_mismatch_alert |
| `etl/etl_ads_risk_metrics_daily.sql` | 指标 ETL | 多表 → ads_risk_metrics_daily |
| `scripts/load_option_c_to_mysql.py` | MySQL 数据加载脚本 | - |

## 数据质量校验规则
| 校验项 | 校验逻辑 | 目标表 |
|--------|----------|--------|
| dwd_invalid_risk_match_flag | 风险匹配标志必须在枚举值内 | dwd_customer_risk_match |
| dwd_negative_risk_gap | 风险差距不能为负数 | dwd_customer_risk_match |
| dwd_invalid_risk_level | 风险等级必须在枚举值内 | dwd_customer_risk_match |
| dws_invalid_compliance_status | 合规状态必须在枚举值内 | dws_risk_compliance_summary |
| dws_mismatch_ratio_range | 错配比例必须在0-1之间 | dws_risk_compliance_summary |
| dws_holding_count_mismatch | 总持仓数应>=错配持仓数 | dws_risk_compliance_summary |
| ads_invalid_alert_level | 预警级别必须在枚举值内 | ads_risk_mismatch_alert |
| ads_invalid_alert_type | 预警类型必须在枚举值内 | ads_risk_mismatch_alert |
| dwd_dws_mismatch_count_mismatch | DWD汇总与DWS的错配持仓数应一致 | dwd_customer_risk_match, dws_risk_compliance_summary |
| missing_risk_match_data | 有持仓的客户都应有风险匹配数据 | ods_holding, dwd_customer_risk_match |
