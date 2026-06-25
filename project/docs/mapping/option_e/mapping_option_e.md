# Mapping 文档：综合财富管理驾驶舱（选项E）

## 基本信息
| 字段 | 值 |
|------|------|
| 需求名称 | 综合财富管理驾驶舱 |
| 需求标识 | option_e |
| 创建日期 | 2026-06-11 |
| 最后更新 | 2026-06-11 |

## 数据流向
```
ODS/DWD 层                DWS 层                        ADS 层
────────────────────────────────────────────────────────────────────────────
ods_transaction     ──→   dws_platform_daily_summary  ──→  ads_executive_dashboard
ods_product                                          ──→  ads_multi_dimension_analysis
ods_customer                                         ──→  ads_anomaly_detection
dwd_customer_asset_daily ──┘
```

## 涉及表清单

### 源表（ODS/DWD层）
| 表名 | 中文表名 | 用途 |
|------|----------|------|
| ods_transaction | 交易流水表 | 提供交易金额、类型等数据 |
| ods_product | 理财产品表 | 提供产品信息 |
| ods_customer | 客户信息表 | 提供客户基础信息 |
| dwd_customer_asset_daily | 客户资产日快照表 | 提供客户AUM数据 |

### 目标表
| 层级 | 表名 | 中文表名 | Mapping CSV |
|------|------|----------|-------------|
| DWS | dws_platform_daily_summary | 平台日汇总宽表 | mapping_dws_platform_daily_summary.csv |
| ADS | ads_executive_dashboard | 高管驾驶舱 | mapping_ads_executive_dashboard.csv |
| ADS | ads_multi_dimension_analysis | 多维度交叉分析表 | mapping_ads_multi_dimension_analysis.csv |
| ADS | ads_anomaly_detection | 异常检测预警表 | mapping_ads_anomaly_detection.csv |

## 加工逻辑概览

### dws_platform_daily_summary（平台日汇总宽表）
- **数据来源**：dwd_customer_asset_daily, ods_transaction, ods_product
- **核心逻辑**：按日期聚合平台级指标，包括客户数、AUM、交易额、产品数、覆盖率、客户增长等
- **聚合粒度**：日级
- **详细映射**：见 `mapping_dws_platform_daily_summary.csv`

### ads_executive_dashboard（高管驾驶舱）
- **数据来源**：dws_platform_daily_summary
- **核心逻辑**：计算环比/同比增长率、交易转化率、目标达成率等管理层指标，支持日报/周报/月报
- **聚合粒度**：日级 + 报告类型
- **详细映射**：见 `mapping_ads_executive_dashboard.csv`

### ads_multi_dimension_analysis（多维度交叉分析表）
- **数据来源**：dwd_customer_asset_daily, ods_transaction, ods_customer, ods_product
- **核心逻辑**：按地区、产品类型、风险等级、客户等级等维度交叉分析AUM和交易数据
- **聚合粒度**：日级 + 维度类型 + 维度值
- **详细映射**：见 `mapping_ads_multi_dimension_analysis.csv`

### ads_anomaly_detection（异常检测预警表）
- **数据来源**：dws_platform_daily_summary
- **核心逻辑**：基于历史均值和标准差检测AUM波动、交易量异常、客户流失异常
- **聚合粒度**：日级 + 异常类型
- **详细映射**：见 `mapping_ads_anomaly_detection.csv`

## ETL脚本清单
| 脚本文件 | 说明 | 转换路径 |
|----------|------|----------|
| `etl/etl_dws_platform_daily_summary.sql` | ODS/DWD → DWS ETL | 多表 → dws_platform_daily_summary |
| `etl/etl_ads_executive_dashboard.sql` | DWS → ADS ETL | dws_platform_daily_summary → ads_executive_dashboard |
| `etl/etl_ads_multi_dimension_analysis.sql` | ODS/DWD → ADS ETL | 多表 → ads_multi_dimension_analysis |
| `etl/etl_ads_anomaly_detection.sql` | DWS → ADS ETL | dws_platform_daily_summary → ads_anomaly_detection |
| `scripts/load_option_e_to_mysql.py` | MySQL 数据加载脚本 | - |

## 数据质量校验规则
| 校验项 | 校验逻辑 | 目标表 |
|--------|----------|--------|
| dws_total_aum_negative | 平台总AUM不能为负数 | dws_platform_daily_summary |
| dws_customer_count_mismatch | 总客户数应≥活跃客户数 | dws_platform_daily_summary |
| dws_coverage_rate_range | 产品覆盖率应在0-1之间 | dws_platform_daily_summary |
| ads_growth_rate_range | 增长率应在合理范围内(-1~10) | ads_executive_dashboard |
| ads_conversion_rate_range | 转化率应在0-1之间 | ads_executive_dashboard |
| multi_aum_consistency | 各维度AUM总和应与平台总AUM一致 | ads_multi_dimension_analysis |
| anomaly_level_valid | 异常级别必须在枚举值内 | ads_anomaly_detection |
| anomaly_deviation_calc | 偏差率计算应正确 | ads_anomaly_detection |
| dws_ods_customer_mismatch | DWS汇总与ODS客户数应一致 | dws_platform_daily_summary |
