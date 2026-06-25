# 选项C：客户风险匹配度分析 - 指标定义

## 基本信息
| 字段 | 值 |
|------|------|
| 需求名称 | 客户风险匹配度分析 |
| 需求标识 | option_c |
| 创建日期 | 2026-06-11 |
| 最后更新 | 2026-06-11 |

## 指标清单

### 1. 风险错配客户数
- **指标名称**: risk_mismatch_customer_count
- **计算逻辑**: COUNT(DISTINCT customer_id) WHERE risk_match_flag = 'mismatch'
- **数据来源**: dwd_customer_risk_match
- **更新频率**: 日
- **业务含义**: 统计持有风险等级高于自身风险承受能力的产品的客户数量

### 2. 测评过期率
- **指标名称**: assessment_expired_rate
- **计算逻辑**: COUNT(DISTINCT customer_id WHERE is_assessment_expired = 'yes') / COUNT(DISTINCT customer_id)
- **数据来源**: dws_risk_compliance_summary
- **更新频率**: 月
- **业务含义**: 风险测评已过期的客户占总客户的比例

### 3. 高风险产品持有率
- **指标名称**: high_risk_product_holding_rate
- **计算逻辑**: COUNT(DISTINCT customer_id WHERE product_risk_level IN ('growth', 'aggressive')) / COUNT(DISTINCT customer_id)
- **数据来源**: dwd_customer_risk_match
- **更新频率**: 月
- **业务含义**: 持有高风险产品（成长型/激进型）的客户占总客户的比例

### 4. 风险错配持仓数
- **指标名称**: risk_mismatch_holding_count
- **计算逻辑**: COUNT(holding_id) WHERE risk_match_flag = 'mismatch'
- **数据来源**: dwd_customer_risk_match
- **更新频率**: 日
- **业务含义**: 风险错配的持仓产品数量

### 5. 风险错配持仓市值
- **指标名称**: risk_mismatch_holding_market_value
- **计算逻辑**: SUM(holding_market_value) WHERE risk_match_flag = 'mismatch'
- **数据来源**: dwd_customer_risk_match
- **更新频率**: 日
- **业务含义**: 风险错配持仓的总市值

### 6. 合规客户占比
- **指标名称**: compliance_customer_rate
- **计算逻辑**: COUNT(DISTINCT customer_id WHERE compliance_status = 'compliant') / COUNT(DISTINCT customer_id)
- **数据来源**: dws_risk_compliance_summary
- **更新频率**: 日
- **业务含义**: 完全合规（无风险错配）的客户占比

### 7. 预警客户数
- **指标名称**: warning_customer_count
- **计算逻辑**: COUNT(DISTINCT customer_id WHERE compliance_status = 'warning')
- **数据来源**: dws_risk_compliance_summary
- **更新频率**: 日
- **业务含义**: 存在轻微风险错配（风险差距=1）的客户数量

### 8. 违规客户数
- **指标名称**: violation_customer_count
- **计算逻辑**: COUNT(DISTINCT customer_id WHERE compliance_status = 'violation')
- **数据来源**: dws_risk_compliance_summary
- **更新频率**: 日
- **业务含义**: 存在严重风险错配（风险差距>=2）的客户数量

### 9. 平均风险差距
- **指标名称**: avg_risk_gap
- **计算逻辑**: AVG(risk_gap) WHERE risk_match_flag = 'mismatch'
- **数据来源**: dwd_customer_risk_match
- **更新频率**: 日
- **业务含义**: 风险错配客户的平均风险等级差距

### 10. 高风险预警数
- **指标名称**: high_alert_count
- **计算逻辑**: COUNT(alert_id) WHERE alert_level = 'high'
- **数据来源**: ads_risk_mismatch_alert
- **更新频率**: 日
- **业务含义**: 高风险级别的预警数量
