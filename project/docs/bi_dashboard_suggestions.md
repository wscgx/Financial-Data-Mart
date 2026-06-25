# BI 展示方案建议 - 客户资产价值分析体系

## 1. 仪表板布局

### 1.1 核心指标卡片区
- **总 AUM**: 显示平台管理总资产
- **高净值客户数**: AUM ≥ 100万的客户数量
- **中端客户数**: AUM 10万-100万的客户数量
- **普通客户数**: AUM < 10万的客户数量
- **日均 AUM**: 近30日平均AUM
- **资产净变动**: 当日申购-赎回+盈亏

### 1.2 图表区域

#### A. 客户价值分布饼图
- 数据源: `dws_customer_value_profile`
- 维度: `customer_value_level`
- 指标: `COUNT(DISTINCT customer_id)`
- 展示: 高净值/中端/普通客户占比

#### B. 客户 AUM 排名 TOP 20
- 数据源: `ads_customer_aum_ranking`
- 维度: `customer_name`, `city`
- 指标: `total_aum`, `ranking`
- 展示: 横向柱状图

#### C. AUM 趋势折线图
- 数据源: `dwd_customer_asset_daily`
- 维度: `stat_date`
- 指标: `SUM(holding_market_value)`
- 展示: 日/周/月 AUM 变化趋势

#### D. 地区 AUM 分布地图
- 数据源: `dws_customer_value_profile`
- 维度: `city`
- 指标: `SUM(total_aum)`
- 展示: 地理热力图

#### E. 资产变动归因堆叠柱状图
- 数据源: `dwd_customer_asset_daily`
- 维度: `stat_date`
- 指标: `SUM(purchase_amount)`, `SUM(redemption_amount)`, `SUM(profit_loss)`
- 展示: 申购/赎回/盈亏堆叠

#### F. 客户资产等级迁移桑基图
- 数据源: `dws_customer_value_profile` (对比不同stat_date)
- 维度: 上期等级 -> 本期等级
- 展示: 客户等级流动

## 2. 推荐 BI 工具

### 选项 A: Apache Superset (开源)
- 优点: 免费、支持多种数据源、图表类型丰富
- 适用: 技术团队有Python/SQL能力

### 选项 B: Metabase (开源)
- 优点: 界面简洁、易于上手、支持SQL查询
- 适用: 业务人员自助分析

### 选项 C: Tableau / Power BI (商业)
- 优点: 功能强大、交互体验好、企业级支持
- 适用: 预算充足、需要高级分析功能

## 3. 更新频率建议

| 报表类型 | 更新频率 | 数据源 |
|----------|----------|--------|
| 实时看板 | 每小时 | dwd_customer_asset_daily |
| 日报 | 每日T+1 | dws_customer_value_profile |
| 周报 | 每周一 | dws_customer_value_profile |
| 月报 | 每月初 | dws_customer_value_profile |
| 排名榜单 | 每日 | ads_customer_aum_ranking |

## 4. 交互功能建议

1. **时间筛选器**: 支持选择日期范围
2. **客户等级筛选**: 按高净值/中端/普通筛选
3. **地区筛选**: 按城市筛选
4. **钻取功能**: 从汇总数据钻取到客户明细
5. **导出功能**: 支持Excel/PDF导出
6. **预警功能**: AUM变动超过阈值时自动提醒

## 5. 移动端适配

- 核心指标卡片优先展示
- 图表支持手势缩放
- 排名列表支持滑动浏览
- 关键指标推送通知
