# 选项E：综合财富管理驾驶舱 - 指标定义

## 基本信息
| 字段 | 值 |
|------|------|
| 需求名称 | 综合财富管理驾驶舱 |
| 需求标识 | option_e |
| 创建日期 | 2026-06-11 |
| 最后更新 | 2026-06-11 |

## 指标清单

### 1. 平台总AUM
- **指标名称**: platform_total_aum
- **计算逻辑**: SUM(所有客户AUM)
- **数据来源**: dws_platform_daily_summary
- **更新频率**: 日
- **业务含义**: 平台管理的全部资产规模

### 2. 客户净增数
- **指标名称**: net_customer_growth
- **计算逻辑**: 新增客户数 - 流失客户数
- **数据来源**: dws_platform_daily_summary
- **更新频率**: 月
- **业务含义**: 客户净增长数量

### 3. 产品覆盖率
- **指标名称**: product_coverage_rate
- **计算逻辑**: 有持仓客户数 / 总客户数
- **数据来源**: dws_platform_daily_summary
- **更新频率**: 月
- **业务含义**: 客户中持有产品的比例

### 4. 交易转化率
- **指标名称**: transaction_conversion_rate
- **计算逻辑**: 有交易客户数 / 活跃客户数
- **数据来源**: ads_executive_dashboard
- **更新频率**: 月
- **业务含义**: 活跃客户中发生交易的比例

### 5. AUM增长率(环比)
- **指标名称**: aum_growth_rate_mom
- **计算逻辑**: (本期AUM - 上期AUM) / 上期AUM
- **数据来源**: ads_executive_dashboard
- **更新频率**: 月
- **业务含义**: AUM月度环比增长率

### 6. AUM同比增长率
- **指标名称**: aum_growth_rate_yoy
- **计算逻辑**: (本期AUM - 去年同期AUM) / 去年同期AUM
- **数据来源**: ads_executive_dashboard
- **更新频率**: 月
- **业务含义**: AUM年度同比增长率

### 7. 交易额增长率
- **指标名称**: transaction_growth_rate
- **计算逻辑**: (本期交易额 - 上期交易额) / 上期交易额
- **数据来源**: ads_executive_dashboard
- **更新频率**: 月
- **业务含义**: 交易额月度环比增长率

### 8. 目标达成率
- **指标名称**: target_achievement_rate
- **计算逻辑**: 实际AUM / 目标AUM
- **数据来源**: ads_executive_dashboard
- **更新频率**: 月
- **业务含义**: AUM目标完成进度

### 9. 异常检测数
- **指标名称**: anomaly_count
- **计算逻辑**: COUNT(anomaly_id) WHERE anomaly_level IN ('medium', 'high')
- **数据来源**: ads_anomaly_detection
- **更新频率**: 日
- **业务含义**: 检测到的异常事件数量

### 10. 多维度AUM分布
- **指标名称**: multi_dimension_aum
- **计算逻辑**: SUM(aum) GROUP BY dimension_type, dimension_value
- **数据来源**: ads_multi_dimension_analysis
- **更新频率**: 日
- **业务含义**: 各维度下的AUM分布情况
