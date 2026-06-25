# Mapping 文档：客户资产价值分析体系（选项A）

## 基本信息
| 字段 | 值 |
|------|------|
| 需求名称 | 客户资产价值分析体系 |
| 需求标识 | option_a |
| 创建日期 | 2026-06-10 |
| 最后更新 | 2026-06-10 |

## 数据流向
```
ODS 层                    DWD 层                        DWS 层                    ADS 层
─────────────────────────────────────────────────────────────────────────────────────────────
ods_holding     ──────→   dwd_customer_asset_daily  ──→  dws_customer_value_profile  ──→  ads_customer_aum_ranking
ods_account               (客户资产日快照表)            (客户价值画像宽表)            (客户AUM排名表)
ods_transaction ──────┐                                                        │
                      │                                                        └──→  ads_customer_value_level_dist
                      │                                                             (客户价值等级分布表)
                      └─────────────────────────────────────────────────→  ads_customer_aum_daily
                                                                           (客户AUM日指标表)
                                                                           ads_customer_net_asset_change
                                                                           (客户资产净变动指标表)
```

## 涉及表清单

### 源表（ODS层）
| 表名 | 中文表名 | 用途 |
|------|----------|------|
| ods_holding | 持仓信息表 | 提供客户持仓市值、盈亏等数据 |
| ods_account | 客户账户表 | 提供账户与客户的关联关系 |
| ods_transaction | 交易流水表 | 提供申购/赎回交易明细 |
| ods_customer | 客户信息表 | 提供客户姓名、城市等基础信息 |

### 目标表
| 层级 | 表名 | 中文表名 | Mapping CSV |
|------|------|----------|-------------|
| DWD | dwd_customer_asset_daily | 客户资产日快照表 | mapping_dwd_customer_asset_daily.csv |
| DWS | dws_customer_value_profile | 客户价值画像宽表 | mapping_dws_customer_value_profile.csv |
| ADS | ads_customer_aum_daily | 客户AUM日指标表 | mapping_ads_customer_aum_daily.csv |
| ADS | ads_customer_aum_ranking | 客户AUM排名表 | mapping_ads_customer_aum_ranking.csv |
| ADS | ads_customer_value_level_dist | 客户价值等级分布表 | mapping_ads_customer_value_level_dist.csv |
| ADS | ads_customer_net_asset_change | 客户资产净变动指标表 | mapping_ads_customer_net_asset_change.csv |

## 加工逻辑概览

### dwd_customer_asset_daily（客户资产日快照表）
- **数据来源**：ods_holding JOIN ods_account JOIN ods_transaction
- **核心逻辑**：按数据日期+客户ID+账户ID关联持仓和交易数据，计算持仓市值、申购金额、赎回金额、盈亏、资产净变动
- **聚合粒度**：日级 + 客户级 + 账户级
- **详细映射**：见 `mapping_dwd_customer_asset_daily.csv`

### dws_customer_value_profile（客户价值画像宽表）
- **数据来源**：dwd_customer_asset_daily JOIN ods_customer
- **核心逻辑**：按客户聚合AUM，计算客户价值等级（高净值/中端/普通），计算30日/90日日均AUM、30日AUM变动、总申购/赎回/盈亏
- **聚合粒度**：日级 + 客户级
- **详细映射**：见 `mapping_dws_customer_value_profile.csv`

### ads_customer_aum_daily（客户AUM日指标表）
- **数据来源**：dwd_customer_asset_daily JOIN ods_customer
- **核心逻辑**：取最新日期的客户AUM数据，拼接客户姓名，计算总资产（持仓市值+现金余额）
- **聚合粒度**：日级 + 客户级
- **详细映射**：见 `mapping_ads_customer_aum_daily.csv`

### ads_customer_aum_ranking（客户AUM排名表）
- **数据来源**：dws_customer_value_profile
- **核心逻辑**：取最新日期数据，按total_aum降序使用ROW_NUMBER()计算排名
- **聚合粒度**：日级 + 排名级
- **详细映射**：见 `mapping_ads_customer_aum_ranking.csv`

### ads_customer_value_level_dist（客户价值等级分布表）
- **数据来源**：dws_customer_value_profile
- **核心逻辑**：按客户价值等级分组，统计各等级客户数、总AUM、平均/最小/最大AUM、AUM占比、客户占比
- **聚合粒度**：日级 + 价值等级
- **详细映射**：见 `mapping_ads_customer_value_level_dist.csv`

### ads_customer_net_asset_change（客户资产净变动指标表）
- **数据来源**：dwd_customer_asset_daily JOIN ods_customer
- **核心逻辑**：取最新日期数据，计算申购金额、赎回金额、盈亏、资产净变动、变动率（净变动/持仓市值）
- **聚合粒度**：日级 + 客户级
- **详细映射**：见 `mapping_ads_customer_net_asset_change.csv`

## ETL脚本清单
| 脚本文件 | 说明 | 转换路径 |
|----------|------|----------|
| `etl/etl_dwd_customer_asset_daily.sql` | ODS → DWD ETL | ods_holding → dwd_customer_asset_daily |
| `etl/etl_dws_customer_value_profile.sql` | DWD → DWS ETL | dwd_customer_asset_daily → dws_customer_value_profile |
| `etl/etl_ads_customer_aum_daily.sql` | DWD → ADS ETL | dwd_customer_asset_daily → ads_customer_aum_daily |
| `etl/etl_ads_customer_aum_ranking.sql` | DWS → ADS ETL | dws_customer_value_profile → ads_customer_aum_ranking |
| `etl/etl_ads_customer_value_level_dist.sql` | DWS → ADS ETL | dws_customer_value_profile → ads_customer_value_level_dist |
| `etl/etl_ads_customer_net_asset_change.sql` | DWD → ADS ETL | dwd_customer_asset_daily → ads_customer_net_asset_change |
| `scripts/load_option_a_to_mysql.py` | MySQL 数据加载脚本 | - |

## 数据质量校验规则
| 校验项 | 校验逻辑 | 目标表 |
|--------|----------|--------|
| dwd_negative_aum | 持仓市值不能为负数 | dwd_customer_asset_daily |
| dwd_invalid_date | 统计日期不能大于当前日期 | dwd_customer_asset_daily |
| dwd_null_customer_id | 客户ID不能为空 | dwd_customer_asset_daily |
| dws_invalid_value_level | 客户价值等级必须在枚举值内 | dws_customer_value_profile |
| dws_aum_mismatch | total_aum与daily_aum应一致 | dws_customer_value_profile |
| ads_ranking_gap | 排名必须连续 | ads_customer_aum_ranking |
| dwd_dws_aum_mismatch | DWD汇总与DWS的AUM应一致 | dwd_customer_asset_daily, dws_customer_value_profile |
| missing_customer_aum | 当前客户都应有AUM数据 | ods_customer, dws_customer_value_profile |
