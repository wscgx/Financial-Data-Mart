import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dashboards.common import load_data, COLUMN_MAP


def render_option_e():
    st.title("🎯 AI智能财富分析平台 - 综合财富管理驾驶舱")

    st.sidebar.header("🔍 筛选条件")

    date_list = load_data("SELECT DISTINCT stat_date FROM dws_platform_daily_summary ORDER BY stat_date DESC")
    selected_date = st.sidebar.selectbox("📅 数据日期", list(date_list['stat_date']))

    platform_summary = load_data(f"SELECT stat_date, total_customers, active_customers, total_aum, product_coverage_rate, total_purchase_amount, total_redemption_amount, net_purchase_amount FROM dws_platform_daily_summary WHERE stat_date = '{selected_date}'")
    executive = load_data(f"SELECT stat_date, report_type, total_customers, active_customers, total_aum, aum_growth_rate, net_purchase_amount, transaction_conversion_rate FROM ads_executive_dashboard WHERE stat_date = '{selected_date}'")
    multi_dim = load_data(f"SELECT stat_date, dimension_type, dimension_value, customer_count, aum, transaction_amount, avg_aum_per_customer FROM ads_multi_dimension_analysis WHERE stat_date = '{selected_date}'")
    anomaly = load_data(f"SELECT stat_date, anomaly_type, anomaly_level, current_value, deviation_rate FROM ads_anomaly_detection WHERE stat_date = '{selected_date}'")

    st.info(f"📊 当前查看日期: **{selected_date}**")

    latest_date = selected_date
    latest_summary = platform_summary
    latest_exec = executive

    st.subheader("📌 核心经营指标")
    col1, col2, col3, col4 = st.columns(4)

    total_aum = latest_summary['total_aum'].sum() if not latest_summary.empty else 0
    total_cust = latest_summary['total_customers'].sum() if not latest_summary.empty else 0
    active_cust = latest_summary['active_customers'].sum() if not latest_summary.empty else 0
    net_purchase = latest_summary['net_purchase_amount'].sum() if not latest_summary.empty else 0

    col1.metric("平台总AUM", f"¥{total_aum:,.2f}")
    col2.metric("总客户数 / 活跃", f"{total_cust:,} / {active_cust:,}")
    col3.metric("净申购金额", f"¥{net_purchase:,.2f}", delta="↑" if net_purchase > 0 else "↓")
    col4.metric("产品覆盖率", f"{latest_summary['product_coverage_rate'].sum()*100:.2f}%" if not latest_summary.empty else "0%")

    st.markdown("---")

    row1_col1, row1_col2 = st.columns([1, 1])

    with row1_col1:
        st.subheader("📊 多维度AUM分析 - 地区")
        region_data = multi_dim[multi_dim['dimension_type'] == 'region'].sort_values('aum', ascending=False)
        if not region_data.empty:
            fig_region = px.bar(region_data.head(10), x='aum', y='dimension_value', orientation='h', text='aum',
                                labels={'aum': 'AUM', 'dimension_value': '城市'},
                                color='aum', color_continuous_scale='Bluered')
            fig_region.update_layout(yaxis={'categoryorder':'total ascending'})
            fig_region.update_traces(texttemplate='¥%{text:,.0f}', textposition='outside')
            st.plotly_chart(fig_region, use_container_width=True)
        else:
            st.info("暂无地区AUM数据")

    with row1_col2:
        st.subheader("📊 多维度AUM分析 - 客户等级")
        level_data = multi_dim[multi_dim['dimension_type'] == 'customer_level']
        if not level_data.empty:
            fig_level = px.pie(level_data, values='aum', names='dimension_value', hole=0.4,
                               labels={'aum': 'AUM', 'dimension_value': '客户等级'},
                               color_discrete_map={'高净值': '#FF6B6B', '中端': '#4ECDC4', '普通': '#95A5A6'})
            fig_level.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_level, use_container_width=True)
        else:
            st.info("暂无客户等级数据")

    row2_col1, row2_col2 = st.columns([1, 1])

    with row2_col1:
        st.subheader("📈 AUM趋势")
        if not platform_summary.empty:
            aum_trend = platform_summary.sort_values('stat_date')
            fig_aum = px.line(aum_trend, x='stat_date', y='total_aum', markers=True,
                              labels={'total_aum': '总AUM', 'stat_date': '统计日期'})
            fig_aum.update_layout(hovermode='x unified')
            st.plotly_chart(fig_aum, use_container_width=True)
        else:
            st.info("暂无AUM趋势数据")

    with row2_col2:
        st.subheader("💰 申购赎回趋势")
        if not platform_summary.empty:
            txn_trend = platform_summary.sort_values('stat_date')
            fig_txn = go.Figure()
            fig_txn.add_trace(go.Scatter(x=txn_trend['stat_date'], y=txn_trend['total_purchase_amount'], mode='lines+markers', name='申购金额', line=dict(color='#4ECDC4')))
            fig_txn.add_trace(go.Scatter(x=txn_trend['stat_date'], y=txn_trend['total_redemption_amount'], mode='lines+markers', name='赎回金额', line=dict(color='#FF6B6B')))
            fig_txn.update_layout(xaxis_title='统计日期', yaxis_title='金额', hovermode='x unified')
            st.plotly_chart(fig_txn, use_container_width=True)
        else:
            st.info("暂无趋势数据")

    st.markdown("---")
    st.subheader("📋 多维度分析明细")
    if not multi_dim.empty:
        display_multi = multi_dim.sort_values(['stat_date', 'dimension_type', 'aum'], ascending=[False, True, False]).head(50)
        display_cols = ['stat_date', 'dimension_type', 'dimension_value', 'customer_count', 'aum',
                        'transaction_amount', 'avg_aum_per_customer']
        display_multi = display_multi[[c for c in display_cols if c in display_multi.columns]].rename(columns=COLUMN_MAP)
        st.dataframe(display_multi, use_container_width=True)
    else:
        st.info("暂无多维度分析数据")

    st.markdown("---")
    st.subheader("📋 高管驾驶舱指标")
    if not executive.empty:
        display_exec = executive.sort_values('stat_date', ascending=False).head(20)
        display_cols = ['stat_date', 'report_type', 'total_customers', 'active_customers', 'total_aum',
                        'aum_growth_rate', 'net_purchase_amount', 'transaction_conversion_rate']
        display_exec = display_exec[[c for c in display_cols if c in display_exec.columns]].rename(columns=COLUMN_MAP)
        st.dataframe(display_exec, use_container_width=True)
    else:
        st.info("暂无高管驾驶舱数据")
