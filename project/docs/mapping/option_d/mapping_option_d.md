# Mapping 文档：客户交易行为分析（选项D）

## 基本信息
| 字段 | 值 |
|------|------|
| 需求名称 | 客户交易行为分析 |
| 需求标识 | option_d |
| 创建日期 | 2026-06-11 |
| 最后更新 | 2026-06-11 |

## 数据流向
```
ODS 层                    DWD 层                        DWS 层                    ADS 层
─────────────────────────────────────────────────────────────────────────────────────────────
ods_transaction   ────→   dwd_customer_activity_daily  ──→  dws_customer_behavior_profile  ──→  ads_customer_churn_warning
ods_account                 (客户活跃度日表)              (客户行为画像宽表)            (客户流失预警表)
ods_customer      ─────┘
```

## 涉及表清单

### 源表（ODS层）
| 表名 | 中文表名 | 用途 |
|------|----------|------|
| ods_transaction | 交易流水表 | 提供交易明细、金额、类型等数据 |
| ods_account | 客户账户表 | 提供账户与客户关联、网点信息 |
| ods_customer | 客户信息表 | 提供客户姓名、城市等基础信息 |
| ods_product | 理财产品表 | 提供产品类型信息 |

### 目标表
| 层级 | 表名 | 中文表名 | Mapping CSV |
|------|------|----------|-------------|
| DWD | dwd_customer_activity_daily | 客户活跃度日表 | mapping_dwd_customer_activity_daily.csv |
| DWS | dws_customer_behavior_profile | 客户行为画像宽表 | mapping_dws_customer_behavior_profile.csv |
| ADS | ads_customer_churn_warning | 客户流失预警表 | mapping_ads_customer_churn_warning.csv |

## 加工逻辑概览

### dwd_customer_activity_daily（客户活跃度日表）
- **数据来源**：ods_transaction JOIN ods_account JOIN ods_customer JOIN ods_product
- **核心逻辑**：按交易日期+客户+账户聚合，统计申购/赎回笔数、金额、手续费、交易产品数等
- **聚合粒度**：日级 + 客户级 + 账户级
- **详细映射**：见 `mapping_dwd_customer_activity_daily.csv`

### dws_customer_behavior_profile（客户行为画像宽表）
- **数据来源**：dwd_customer_activity_daily JOIN ods_customer
- **核心逻辑**：按客户聚合交易行为，计算交易频率、偏好产品类型、大额交易、流失风险等级、资产趋势
- **聚合粒度**：日级 + 客户级
- **详细映射**：见 `mapping_dws_customer_behavior_profile.csv`

### ads_customer_churn_warning（客户流失预警表）
- **数据来源**：dws_customer_behavior_profile
- **核心逻辑**：筛选未交易天数>30天的客户，计算流失风险评分，生成预警原因
- **聚合粒度**：日级 + 预警级
- **详细映射**：见 `mapping_ads_customer_churn_warning.csv`

## ETL脚本清单
| 脚本文件 | 说明 | 转换路径 |
|----------|------|----------|
| `etl/etl_dwd_customer_activity_daily.sql` | ODS → DWD ETL | ods_transaction → dwd_customer_activity_daily |
| `etl/etl_dws_customer_behavior_profile.sql` | DWD → DWS ETL | dwd_customer_activity_daily → dws_customer_behavior_profile |
| `etl/etl_ads_customer_churn_warning.sql` | DWS → ADS ETL | dws_customer_behavior_profile → ads_customer_churn_warning |
| `scripts/load_option_d_to_mysql.py` | MySQL 数据加载脚本 | - |

## 数据质量校验规则
| 校验项 | 校验逻辑 | 目标表 |
|--------|----------|--------|
| dwd_negative_amount | 交易金额不能为负数 | dwd_customer_activity_daily |
| dwd_null_customer_id | 客户ID不能为空 | dwd_customer_activity_daily |
| dwd_invalid_date | 统计日期不能大于当前日期 | dwd_customer_activity_daily |
| dws_negative_frequency | 交易频率不能为负数 | dws_customer_behavior_profile |
| dws_invalid_churn_level | 流失风险等级必须在枚举值内 | dws_customer_behavior_profile |
| dws_invalid_asset_trend | 资产趋势必须在枚举值内 | dws_customer_behavior_profile |
| ads_negative_risk_score | 风险评分不能为负数 | ads_customer_churn_warning |
| ads_invalid_churn_level | 流失风险等级必须在枚举值内 | ads_customer_churn_warning |
| dwd_dws_transaction_mismatch | DWD汇总与DWS交易笔数应一致 | dwd_customer_activity_daily, dws_customer_behavior_profile |
| missing_active_customer | 有交易的客户都应有活跃度数据 | ods_transaction, dwd_customer_activity_daily |
