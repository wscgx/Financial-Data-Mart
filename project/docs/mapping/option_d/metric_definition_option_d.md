# 选项D：客户交易行为分析 - 指标定义

## 基本信息
| 字段 | 值 |
|------|------|
| 需求名称 | 客户交易行为分析 |
| 需求标识 | option_d |
| 创建日期 | 2026-06-11 |
| 最后更新 | 2026-06-11 |

## 指标清单

### 1. 活跃客户数
- **指标名称**: active_customer_count
- **计算逻辑**: COUNT(DISTINCT customer_id) WHERE transaction_count > 0
- **数据来源**: dwd_customer_activity_daily
- **更新频率**: 日
- **业务含义**: 统计当日有交易的客户数量

### 2. 客户交易频次
- **指标名称**: customer_transaction_frequency
- **计算逻辑**: SUM(transaction_count) / COUNT(DISTINCT customer_id)
- **数据来源**: dwd_customer_activity_daily
- **更新频率**: 月
- **业务含义**: 平均每位客户的交易笔数

### 3. 流失客户数
- **指标名称**: churn_customer_count
- **计算逻辑**: COUNT(DISTINCT customer_id) WHERE days_inactive > 90
- **数据来源**: dws_customer_behavior_profile
- **更新频率**: 月
- **业务含义**: 超过90天未交易的客户数量

### 4. 大额交易笔数
- **指标名称**: large_transaction_count
- **计算逻辑**: COUNT(transaction_id) WHERE amount > 50000
- **数据来源**: dwd_customer_activity_daily
- **更新频率**: 日
- **业务含义**: 单笔超过5万的交易笔数

### 5. 大额交易总额
- **指标名称**: large_transaction_amount
- **计算逻辑**: SUM(amount) WHERE amount > 50000
- **数据来源**: dwd_customer_activity_daily
- **更新频率**: 日
- **业务含义**: 大额交易的总金额

### 6. 平均交易金额
- **指标名称**: avg_transaction_amount
- **计算逻辑**: SUM(amount) / COUNT(transaction_id)
- **数据来源**: dwd_customer_activity_daily
- **更新频率**: 日
- **业务含义**: 平均每笔交易的金额

### 7. 偏好产品类型分布
- **指标名称**: preferred_product_type_dist
- **计算逻辑**: COUNT(DISTINCT customer_id) GROUP BY preferred_product_type
- **数据来源**: dws_customer_behavior_profile
- **更新频率**: 月
- **业务含义**: 各产品类型偏好的客户分布

### 8. 高风险流失客户数
- **指标名称**: high_churn_risk_count
- **计算逻辑**: COUNT(DISTINCT customer_id) WHERE churn_risk_level = 'high'
- **数据来源**: dws_customer_behavior_profile
- **更新频率**: 日
- **业务含义**: 高流失风险客户数量

### 9. 中风险流失客户数
- **指标名称**: medium_churn_risk_count
- **计算逻辑**: COUNT(DISTINCT customer_id) WHERE churn_risk_level = 'medium'
- **数据来源**: dws_customer_behavior_profile
- **更新频率**: 日
- **业务含义**: 中流失风险客户数量

### 10. 资产下降客户数
- **指标名称**: asset_decreasing_count
- **计算逻辑**: COUNT(DISTINCT customer_id) WHERE asset_trend = 'decreasing'
- **数据来源**: dws_customer_behavior_profile
- **更新频率**: 日
- **业务含义**: 资产持续下降的客户数量

### 11. 流失预警数
- **指标名称**: churn_warning_count
- **计算逻辑**: COUNT(warning_id)
- **数据来源**: ads_customer_churn_warning
- **更新频率**: 日
- **业务含义**: 流失预警记录总数

### 12. 高风险预警占比
- **指标名称**: high_risk_warning_rate
- **计算逻辑**: COUNT(DISTINCT customer_id WHERE churn_risk_level = 'high') / COUNT(DISTINCT customer_id)
- **数据来源**: ads_customer_churn_warning
- **更新频率**: 日
- **业务含义**: 高风险预警客户占比
