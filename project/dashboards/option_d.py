import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dashboards.common import load_data, COLUMN_MAP


def render_option_d():
    st.title("📈 AI智能财富分析平台 - 客户交易行为看板")

    st.sidebar.header("🔍 筛选条件")

    date_list = load_data("SELECT DISTINCT DATE(stat_date) AS stat_date FROM dwd_customer_activity_daily ORDER BY stat_date DESC")
    selected_date = st.sidebar.selectbox("📅 数据日期", list(date_list['stat_date']))

    churn_levels = load_data("SELECT DISTINCT churn_risk_level FROM dws_customer_behavior_profile ORDER BY churn_risk_level")
    selected_churn = st.sidebar.selectbox("流失风险等级", ["全部"] + list(churn_levels['churn_risk_level']))

    asset_trends = load_data("SELECT DISTINCT asset_trend FROM dws_customer_behavior_profile ORDER BY asset_trend")
    selected_trend = st.sidebar.selectbox("资产趋势", ["全部"] + list(asset_trends['asset_trend']))

    activity = load_data("SELECT stat_date, customer_id, transaction_count, purchase_amount, redemption_amount FROM dwd_customer_activity_daily WHERE DATE(stat_date) = '{}'".format(selected_date))
    behavior = load_data("SELECT stat_date, customer_id, customer_name, city, branch, total_transaction_count, total_purchase_amount, total_redemption_amount, transaction_frequency, days_inactive, churn_risk_level, asset_trend, large_transaction_count, large_transaction_amount FROM dws_customer_behavior_profile WHERE DATE(stat_date) = '{}'".format(selected_date))
    churn = load_data("SELECT stat_date, warning_id, customer_name, city, branch, days_inactive, churn_risk_level, churn_risk_score, asset_trend, warning_reason FROM ads_customer_churn_warning WHERE DATE(stat_date) = '{}'".format(selected_date))

    st.info(f"📊 当前查看日期: **{selected_date}**")

    if selected_churn != "全部":
        behavior = behavior[behavior['churn_risk_level'] == selected_churn]
        churn = churn[churn['churn_risk_level'] == selected_churn]

    if selected_trend != "全部":
        behavior = behavior[behavior['asset_trend'] == selected_trend]
        churn = churn[churn['asset_trend'] == selected_trend]

    latest_date = activity['stat_date'].max() if not activity.empty else None
    latest_behavior = behavior[behavior['stat_date'] == latest_date] if latest_date else pd.DataFrame()
    latest_churn = churn[churn['stat_date'] == latest_date] if latest_date else pd.DataFrame()

    st.subheader("📌 核心交易指标")
    col1, col2, col3, col4 = st.columns(4)

    active_cust = activity[activity['stat_date'] == latest_date]['customer_id'].nunique() if latest_date else 0
    total_txn = activity['transaction_count'].sum()
    high_churn = behavior[behavior['churn_risk_level'] == 'high']['customer_id'].nunique()
    churn_warning = latest_churn['warning_id'].count() if not latest_churn.empty else 0

    col1.metric("活跃客户数", f"{active_cust:,}")
    col2.metric("总交易笔数", f"{total_txn:,}")
    col3.metric("高流失风险客户", f"{high_churn:,}", delta="↑需关注" if high_churn > 100 else "正常")
    col4.metric("流失预警数", f"{churn_warning:,}", delta="↑严重" if churn_warning > 500 else "正常")

    st.markdown("---")

    row1_col1, row1_col2 = st.columns([1, 1])

    with row1_col1:
        st.subheader("🥧 流失风险分布")
        if not behavior.empty:
            churn_dist = behavior.groupby('churn_risk_level')['customer_id'].count().reset_index()
            churn_dist.columns = ['churn_risk_level', 'customer_count']
            fig_churn = px.pie(churn_dist, values='customer_count', names='churn_risk_level', hole=0.4,
                               labels={'customer_count': '客户数', 'churn_risk_level': '流失风险'},
                               color_discrete_map={'none': '#4ECDC4', 'low': '#95A5A6', 'medium': '#FFC107', 'high': '#FF6B6B'})
            fig_churn.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_churn, use_container_width=True)
        else:
            st.info("暂无流失风险数据")

    with row1_col2:
        st.subheader("📊 资产趋势分布")
        if not behavior.empty:
            trend_dist = behavior.groupby('asset_trend')['customer_id'].count().reset_index()
            trend_dist.columns = ['asset_trend', 'customer_count']
            fig_trend = px.pie(trend_dist, values='customer_count', names='asset_trend', hole=0.4,
                               labels={'customer_count': '客户数', 'asset_trend': '资产趋势'},
                               color_discrete_map={'increasing': '#4ECDC4', 'stable': '#FFC107', 'decreasing': '#FF6B6B'})
            fig_trend.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("暂无资产趋势数据")

    row2_col1, row2_col2 = st.columns([1, 1])

    with row2_col1:
        st.subheader("📈 交易活跃度趋势")
        if not activity.empty:
            daily_txn = activity.groupby('stat_date')['transaction_count'].sum().reset_index()
            daily_txn = daily_txn.sort_values('stat_date')
            fig_daily = px.line(daily_txn, x='stat_date', y='transaction_count', markers=True,
                                labels={'transaction_count': '交易笔数', 'stat_date': '统计日期'})
            fig_daily.update_layout(hovermode='x unified')
            st.plotly_chart(fig_daily, use_container_width=True)
        else:
            st.info("暂无交易趋势数据")

    with row2_col2:
        st.subheader("💰 申购赎回趋势")
        if not activity.empty:
            daily_amount = activity.groupby('stat_date')[['purchase_amount', 'redemption_amount']].sum().reset_index()
            daily_amount = daily_amount.sort_values('stat_date')
            fig_amount = go.Figure()
            fig_amount.add_trace(go.Scatter(x=daily_amount['stat_date'], y=daily_amount['purchase_amount'], mode='lines+markers', name='申购金额', line=dict(color='#4ECDC4')))
            fig_amount.add_trace(go.Scatter(x=daily_amount['stat_date'], y=daily_amount['redemption_amount'], mode='lines+markers', name='赎回金额', line=dict(color='#FF6B6B')))
            fig_amount.update_layout(xaxis_title='统计日期', yaxis_title='金额', hovermode='x unified')
            st.plotly_chart(fig_amount, use_container_width=True)
        else:
            st.info("暂无金额趋势数据")

    row3_col1, row3_col2 = st.columns([1, 1])

    with row3_col1:
        st.subheader("⚠️ 流失预警 TOP 10")
        if not churn.empty:
            top_churn = churn.sort_values('churn_risk_score', ascending=False).head(10)
            fig_top = px.bar(top_churn, x='churn_risk_score', y='customer_name', orientation='h', text='days_inactive',
                             labels={'churn_risk_score': '风险评分', 'customer_name': '客户姓名'},
                             color='churn_risk_score', color_continuous_scale='Reds')
            fig_top.update_layout(yaxis={'categoryorder':'total ascending'})
            fig_top.update_traces(texttemplate='%{text}天未交易', textposition='outside')
            st.plotly_chart(fig_top, use_container_width=True)
        else:
            st.info("暂无流失预警数据")

    with row3_col2:
        st.subheader("📊 大额交易分布")
        if not behavior.empty:
            large_txn = behavior[behavior['large_transaction_count'] > 0].sort_values('large_transaction_amount', ascending=False).head(10)
            if not large_txn.empty:
                fig_large = px.bar(large_txn, x='large_transaction_amount', y='customer_name', orientation='h', text='large_transaction_count',
                                   labels={'large_transaction_amount': '大额交易总额', 'customer_name': '客户姓名'},
                                   color='large_transaction_amount', color_continuous_scale='Viridis')
                fig_large.update_layout(yaxis={'categoryorder':'total ascending'})
                fig_large.update_traces(texttemplate='%{text}笔', textposition='outside')
                st.plotly_chart(fig_large, use_container_width=True)
            else:
                st.info("暂无大额交易数据")
        else:
            st.info("暂无大额交易数据")

    st.markdown("---")
    st.subheader("📋 流失预警清单 (前50条)")
    if not churn.empty:
        display_churn = churn.sort_values('churn_risk_score', ascending=False).head(50)
        display_cols = ['stat_date', 'customer_name', 'city', 'branch', 'days_inactive', 'churn_risk_level',
                        'churn_risk_score', 'asset_trend', 'warning_reason']
        display_churn = display_churn[[c for c in display_cols if c in display_churn.columns]].rename(columns=COLUMN_MAP)
        st.dataframe(display_churn, use_container_width=True)
    else:
        st.info("暂无流失预警数据")

    st.markdown("---")
    st.subheader("📋 客户行为明细 (前50条)")
    if not behavior.empty:
        display_behavior = behavior.sort_values('days_inactive', ascending=False).head(50)
        display_cols = ['stat_date', 'customer_name', 'city', 'branch', 'total_transaction_count',
                        'total_purchase_amount', 'total_redemption_amount', 'transaction_frequency',
                        'days_inactive', 'churn_risk_level', 'asset_trend']
        display_behavior = display_behavior[[c for c in display_cols if c in display_behavior.columns]].rename(columns=COLUMN_MAP)
        st.dataframe(display_behavior, use_container_width=True)
    else:
        st.info("暂无客户行为数据")
