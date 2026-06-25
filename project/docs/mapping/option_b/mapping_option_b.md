# Mapping 文档：产品销售与业绩分析（选项B）

## 基本信息
| 字段 | 值 |
|------|------|
| 需求名称 | 产品销售与业绩分析 |
| 需求标识 | option_b |
| 创建日期 | 2026-06-10 |
| 最后更新 | 2026-06-10 |

## 数据流向
```
ODS 层                    DWD 层                        DWS 层                    ADS 层
─────────────────────────────────────────────────────────────────────────────────────────────
ods_product     ──────→   dwd_product_sales_daily  ──→  dws_product_performance
ods_transaction           (产品销售日汇总表)            (产品业绩宽表)
ods_account     ──────┐
                      └─────────────────────────────────────────────────→  ads_branch_sales_ranking
                                                                           (网点销售排名表)
```

## 涉及表清单

### 源表（ODS层）
| 表名 | 中文表名 | 用途 |
|------|----------|------|
| ods_product | 理财产品表 | 提供产品基本信息（名称、类型、风险等级、预期收益率等） |
| ods_transaction | 交易流水表 | 提供申购/赎回交易明细 |
| ods_account | 客户账户表 | 提供账户与网点的关联关系 |

### 目标表
| 层级 | 表名 | 中文表名 | Mapping CSV |
|------|------|----------|-------------|
| DWD | dwd_product_sales_daily | 产品销售日汇总表 | mapping_dwd_product_sales_daily.csv |
| DWS | dws_product_performance | 产品业绩宽表 | mapping_dws_product_performance.csv |
| ADS | ads_branch_sales_ranking | 网点销售排名表 | mapping_ads_branch_sales_ranking.csv |

## 加工逻辑概览

### dwd_product_sales_daily（产品销售日汇总表）
- **数据来源**：ods_transaction JOIN ods_product JOIN ods_account
- **核心逻辑**：按交易日期+产品ID聚合，计算申购金额、赎回金额、净申购金额、交易笔数、交易客户数
- **聚合粒度**：日级 + 产品级
- **详细映射**：见 `mapping_dwd_product_sales_daily.csv`

### dws_product_performance（产品业绩宽表）
- **数据来源**：dwd_product_sales_daily JOIN ods_product
- **核心逻辑**：基于DWD层数据，使用窗口函数计算累计销售额、7日/30日滑动窗口销售额、日均销售额
- **聚合粒度**：日级 + 产品级
- **详细映射**：见 `mapping_dws_product_performance.csv`

### ads_branch_sales_ranking（网点销售排名表）
- **数据来源**：ods_transaction JOIN ods_account
- **核心逻辑**：按交易日期+网点聚合销售额，使用RANK()计算销售排名，计算各网点销售占比
- **聚合粒度**：日级 + 网点级
- **详细映射**：见 `mapping_ads_branch_sales_ranking.csv`

## ETL脚本清单
| 脚本文件 | 说明 | 转换路径 |
|----------|------|----------|
| `etl/etl_dwd_product_sales_daily.sql` | ODS → DWD ETL | ods_transaction → dwd_product_sales_daily |
| `etl/etl_dws_product_performance.sql` | DWD → DWS ETL | dwd_product_sales_daily → dws_product_performance |
| `etl/etl_ads_branch_sales_ranking.sql` | DWD+ODS → ADS ETL | ods_transaction → ads_branch_sales_ranking |
| `scripts/load_option_b_to_mysql.py` | MySQL 数据加载脚本 | - |

## 数据质量校验规则
| 校验项 | 校验逻辑 | 目标表 |
|--------|----------|--------|
| dwd_negative_sales_amount | 申购/赎回金额不能为负数 | dwd_product_sales_daily |
| dwd_null_product_id | 产品ID不能为空 | dwd_product_sales_daily |
| dwd_net_purchase_mismatch | 净申购金额 = 申购金额 - 赎回金额 | dwd_product_sales_daily |
| dws_decreasing_total_sales | 累计销售额不能递减 | dws_product_performance |
| ads_sales_share_sum_invalid | 销售占比总和应接近1 | ads_branch_sales_ranking |
| ads_branch_ranking_gap | 排名必须连续 | ads_branch_sales_ranking |
