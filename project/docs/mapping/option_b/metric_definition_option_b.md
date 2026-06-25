# 指标定义文档：产品销售与业绩分析（选项B）

## 基本信息
| 字段 | 值 |
|------|------|
| 需求名称 | 产品销售与业绩分析 |
| 需求标识 | option_b |
| 创建日期 | 2026-06-10 |
| 最后更新 | 2026-06-10 |

## 指标清单

### DWD层指标（产品销售日汇总表）

| 指标编码 | 指标名称 | 英文名 | 计算逻辑 | 更新频率 | 所属表 |
|----------|----------|--------|----------|----------|--------|
| M101 | 产品日申购金额 | product_daily_purchase_amount | SUM(CASE WHEN transaction_type = 'purchase' THEN amount ELSE 0 END) | 日 | dwd_product_sales_daily |
| M102 | 产品日赎回金额 | product_daily_redemption_amount | SUM(CASE WHEN transaction_type = 'redemption' THEN amount ELSE 0 END) | 日 | dwd_product_sales_daily |
| M103 | 产品日净申购金额 | product_daily_net_purchase_amount | 申购金额 - 赎回金额 | 日 | dwd_product_sales_daily |
| M104 | 产品日申购笔数 | product_daily_purchase_count | COUNT(purchase交易) | 日 | dwd_product_sales_daily |
| M105 | 产品日赎回笔数 | product_daily_redemption_count | COUNT(redemption交易) | 日 | dwd_product_sales_daily |
| M106 | 产品日交易客户数 | product_daily_customer_count | COUNT(DISTINCT customer_id) | 日 | dwd_product_sales_daily |
| M107 | 产品日总手续费 | product_daily_total_fee | SUM(fee) | 日 | dwd_product_sales_daily |

### DWS层指标（产品业绩宽表）

| 指标编码 | 指标名称 | 英文名 | 计算逻辑 | 更新频率 | 所属表 |
|----------|----------|--------|----------|----------|--------|
| M201 | 产品累计销售金额 | product_total_sales_amount | SUM(purchase_amount) OVER (PARTITION BY product_id ORDER BY stat_date) | 日 | dws_product_performance |
| M202 | 产品累计赎回金额 | product_total_redemption_amount | SUM(redemption_amount) OVER (PARTITION BY product_id ORDER BY stat_date) | 日 | dws_product_performance |
| M203 | 产品净销售金额 | product_net_sales_amount | 累计销售金额 - 累计赎回金额 | 日 | dws_product_performance |
| M204 | 产品累计交易客户数 | product_total_customer_count | SUM(customer_count) OVER (PARTITION BY product_id ORDER BY stat_date) | 日 | dws_product_performance |
| M205 | 产品日均销售额 | product_avg_daily_sales | AVG(purchase_amount) OVER (7日滑动窗口) | 日 | dws_product_performance |
| M206 | 产品周销售额 | product_weekly_sales_amount | SUM(purchase_amount) OVER (7日滑动窗口) | 周 | dws_product_performance |
| M207 | 产品月销售额 | product_monthly_sales_amount | SUM(purchase_amount) OVER (30日滑动窗口) | 月 | dws_product_performance |
| M208 | 产品预期收益率 | product_expected_return | 取自ods_product.expected_return | 日 | dws_product_performance |

### ADS层指标（网点销售排名表）

| 指标编码 | 指标名称 | 英文名 | 计算逻辑 | 更新频率 | 所属表 |
|----------|----------|--------|----------|----------|--------|
| M301 | 网点日销售总额 | branch_daily_sales_amount | SUM(CASE WHEN transaction_type = 'purchase' THEN amount ELSE 0 END) | 日 | ads_branch_sales_ranking |
| M302 | 网点日赎回总额 | branch_daily_redemption_amount | SUM(CASE WHEN transaction_type = 'redemption' THEN amount ELSE 0 END) | 日 | ads_branch_sales_ranking |
| M303 | 网点净销售额 | branch_net_sales_amount | 销售总额 - 赎回总额 | 日 | ads_branch_sales_ranking |
| M304 | 网点日交易笔数 | branch_daily_transaction_count | COUNT(transaction_id) | 日 | ads_branch_sales_ranking |
| M305 | 网点日交易客户数 | branch_daily_customer_count | COUNT(DISTINCT customer_id) | 日 | ads_branch_sales_ranking |
| M306 | 网点销售排名 | branch_sales_ranking | RANK() OVER (PARTITION BY stat_date ORDER BY total_sales_amount DESC) | 日 | ads_branch_sales_ranking |
| M307 | 网点销售占比 | branch_sales_share | 网点销售额 / 当日总销售额 | 日 | ads_branch_sales_ranking |

## 指标计算详细说明

### M101-M107：DWD层日级指标
- **数据来源**：ods_transaction（主表）、ods_product、ods_account
- **聚合粒度**：stat_date + product_id
- **过滤条件**：transaction_type IN ('purchase', 'redemption') AND is_current = 1
- **计算示例**：
  ```sql
  SELECT 
      transaction_date,
      product_id,
      SUM(CASE WHEN transaction_type = 'purchase' THEN amount ELSE 0 END) AS purchase_amount,
      SUM(CASE WHEN transaction_type = 'redemption' THEN amount ELSE 0 END) AS redemption_amount
  FROM ods_transaction
  WHERE transaction_type IN ('purchase', 'redemption')
  GROUP BY transaction_date, product_id;
  ```

### M201-M208：DWS层累计/趋势指标
- **数据来源**：dwd_product_sales_daily（主表）、ods_product
- **聚合粒度**：stat_date + product_id
- **窗口函数说明**：
  - 累计指标：`SUM() OVER (PARTITION BY product_id ORDER BY stat_date)`
  - 7日均值：`AVG() OVER (PARTITION BY product_id ORDER BY stat_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)`
  - 周销售额：`SUM() OVER (7日滑动窗口)`
  - 月销售额：`SUM() OVER (30日滑动窗口)`

### M301-M307：ADS层网点排名指标
- **数据来源**：ods_transaction（主表）、ods_account
- **聚合粒度**：stat_date + branch
- **排名计算**：`RANK() OVER (PARTITION BY stat_date ORDER BY total_sales_amount DESC)`
- **占比计算**：`total_sales_amount / SUM(total_sales_amount) OVER (PARTITION BY stat_date)`

## 指标血缘关系
```
ods_transaction ──→ M101-M107 (DWD日级指标)
                     │
                     └──→ M201-M208 (DWS累计/趋势指标)
                     
ods_transaction ──→ M301-M307 (ADS网点排名指标)
ods_account     ──┘
```

## 指标更新策略
| 层级 | 更新方式 | 更新频率 | 更新时间 |
|------|----------|----------|----------|
| DWD | 全量刷新 | 日 | 每日凌晨 |
| DWS | 全量刷新 | 日 | 每日凌晨（DWD完成后） |
| ADS | 全量刷新 | 日 | 每日凌晨（DWS完成后） |
