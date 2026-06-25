import streamlit as st
import pandas as pd
import plotly.express as px

from dashboards.common import load_data, COLUMN_MAP, RISK_METRIC_MAP


def render_option_c():
    st.title("🛡️ AI智能财富分析平台 - 客户风险匹配度看板")

    st.sidebar.header("🔍 筛选条件")

    date_list = load_data("SELECT DISTINCT stat_date FROM dwd_customer_risk_match ORDER BY stat_date DESC")
    selected_date = st.sidebar.selectbox("📅 数据日期", list(date_list['stat_date']))

    risk_levels = load_data("SELECT DISTINCT customer_risk_level FROM dwd_customer_risk_match WHERE customer_risk_level IS NOT NULL ORDER BY customer_risk_level")
    selected_risk = st.sidebar.selectbox("客户风险等级", ["全部"] + list(risk_levels['customer_risk_level']))

    compliance_status_list = load_data("SELECT DISTINCT compliance_status FROM dws_risk_compliance_summary ORDER BY compliance_status")
    selected_status = st.sidebar.selectbox("合规状态", ["全部"] + list(compliance_status_list['compliance_status']))

    alert_level_list = load_data("SELECT DISTINCT alert_level FROM ads_risk_mismatch_alert ORDER BY alert_level")
    selected_alert = st.sidebar.selectbox("预警级别", ["全部"] + list(alert_level_list['alert_level']))

    risk_match = load_data(f"SELECT stat_date, customer_id, customer_risk_level, product_risk_level FROM dwd_customer_risk_match WHERE stat_date = '{selected_date}'")
    compliance = load_data(f"SELECT stat_date, customer_id, customer_name, customer_risk_level, compliance_status, total_holding_count, mismatch_holding_count, mismatch_ratio, max_risk_gap FROM dws_risk_compliance_summary WHERE stat_date = '{selected_date}'")
    alerts = load_data(f"SELECT stat_date, customer_name, customer_risk_level, product_name, product_risk_level, risk_gap, holding_market_value, alert_level, alert_type, alert_message FROM ads_risk_mismatch_alert WHERE stat_date = '{selected_date}'")
    metrics = load_data(f"SELECT stat_date, metric_name, metric_value, metric_type FROM ads_risk_metrics_daily WHERE stat_date = '{selected_date}'")

    st.info(f"📊 当前查看日期: **{selected_date}**")

    if selected_risk != "全部":
        risk_match = risk_match[risk_match['customer_risk_level'] == selected_risk]
        compliance = compliance[compliance['customer_risk_level'] == selected_risk]
        alerts = alerts[alerts['customer_risk_level'] == selected_risk]

    if selected_status != "全部":
        compliance = compliance[compliance['compliance_status'] == selected_status]

    if selected_alert != "全部":
        alerts = alerts[alerts['alert_level'] == selected_alert]

    latest_date = risk_match['stat_date'].max() if not risk_match.empty else None
    latest_metrics = metrics[metrics['stat_date'] == latest_date] if latest_date else pd.DataFrame()

    def get_metric(name, default=0):
        row = latest_metrics[latest_metrics['metric_name'] == name]
        if not row.empty:
            return row.iloc[0]['metric_value']
        return default

    mismatch_cust = get_metric('risk_mismatch_customer_count')
    expired_rate = get_metric('assessment_expired_rate')
    compliance_rate = get_metric('compliance_customer_rate')
    high_alert = get_metric('high_alert_count')

    st.subheader("📌 核心风险指标")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("风险错配客户数", f"{mismatch_cust:,.0f}", delta="↑需关注" if mismatch_cust > 500 else "↓正常")
    col2.metric("测评过期率", f"{expired_rate:.2%}")
    col3.metric("合规客户占比", f"{compliance_rate:.2%}", delta="↓需关注" if compliance_rate < 0.5 else "↑健康")
    col4.metric("高风险预警数", f"{high_alert:,.0f}", delta="↑严重" if high_alert > 1000 else "正常")

    st.markdown("---")

    row1_col1, row1_col2 = st.columns([1, 1])

    with row1_col1:
        st.subheader("🥧 合规状态分布")
        status_counts = compliance.groupby('compliance_status')['customer_id'].count().reset_index()
        status_counts.columns = ['compliance_status', 'customer_count']
        if not status_counts.empty:
            fig_pie = px.pie(status_counts, values='customer_count', names='compliance_status', hole=0.4,
                             labels={'customer_count': '客户数', 'compliance_status': '合规状态'},
                             color_discrete_map={'compliant': '#4ECDC4', 'warning': '#FFC107', 'violation': '#FF6B6B'})
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("暂无合规状态数据")

    with row1_col2:
        st.subheader("🔥 风险错配矩阵热力图")
        if not risk_match.empty:
            matrix_data = risk_match.groupby(['customer_risk_level', 'product_risk_level'])['customer_id'].count().reset_index()
            matrix_data.columns = ['customer_risk_level', 'product_risk_level', 'count']
            pivot_matrix = matrix_data.pivot(index='customer_risk_level', columns='product_risk_level', values='count').fillna(0)
            fig_heatmap = px.imshow(pivot_matrix, labels=dict(x="产品风险等级", y="客户风险等级", color="持仓数"),
                                    x=pivot_matrix.columns, y=pivot_matrix.index, color_continuous_scale='YlOrRd',
                                    text_auto='.0f')
            fig_heatmap.update_layout(xaxis_side="top")
            st.plotly_chart(fig_heatmap, use_container_width=True)
        else:
            st.info("暂无错配矩阵数据")

    row2_col1, row2_col2 = st.columns([1, 1])

    with row2_col1:
        st.subheader("📊 风险指标总览")
        if not latest_metrics.empty:
            display_metrics = latest_metrics.copy()
            display_metrics['指标名称'] = display_metrics['metric_name'].map(RISK_METRIC_MAP)
            display_metrics = display_metrics.sort_values('metric_value', ascending=False)
            fig_metrics = px.bar(display_metrics.head(8), x='指标名称', y='metric_value', color='metric_type',
                                 labels={'metric_value': '指标值', '指标名称': '指标', 'metric_type': '类型'},
                                 color_discrete_map={'count': '#4ECDC4', 'rate': '#FFC107', 'amount': '#FF6B6B'})
            fig_metrics.update_layout(xaxis_title='', yaxis_title='值', xaxis_tickangle=-45)
            st.plotly_chart(fig_metrics, use_container_width=True)
        else:
            st.info("暂无指标数据")

    with row2_col2:
        st.subheader("📈 客户风险等级分布")
        if not risk_match.empty:
            risk_dist = risk_match.groupby('customer_risk_level')['customer_id'].nunique().reset_index()
            risk_dist.columns = ['customer_risk_level', 'customer_count']
            risk_dist = risk_dist.dropna(subset=['customer_risk_level'])
            fig_risk = px.bar(risk_dist, x='customer_risk_level', y='customer_count', color='customer_count',
                              labels={'customer_count': '客户数', 'customer_risk_level': '客户风险等级'},
                              color_continuous_scale='Viridis')
            fig_risk.update_traces(texttemplate='%{y:,}', textposition='outside')
            st.plotly_chart(fig_risk, use_container_width=True)
        else:
            st.info("暂无风险分布数据")

    row3_col1, row3_col2 = st.columns([1, 1])

    with row3_col1:
        st.subheader("⚠️ 预警级别分布")
        if not alerts.empty:
            alert_dist = alerts.groupby('alert_level').size().reset_index(name='count')
            fig_alert = px.pie(alert_dist, values='count', names='alert_level', hole=0.4,
                               labels={'count': '预警数', 'alert_level': '预警级别'},
                               color_discrete_map={'high': '#FF6B6B', 'medium': '#FFC107', 'low': '#4ECDC4'})
            fig_alert.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_alert, use_container_width=True)
        else:
            st.info("暂无预警数据")

    with row3_col2:
        st.subheader("📊 预警类型分布")
        if not alerts.empty:
            type_dist = alerts.groupby('alert_type').size().reset_index(name='count')
            fig_type = px.pie(type_dist, values='count', names='alert_type', hole=0.4,
                              labels={'count': '预警数', 'alert_type': '预警类型'},
                              color_discrete_map={'mismatch': '#FF6B6B', 'expired': '#FFC107', 'both': '#8B0000'})
            fig_type.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_type, use_container_width=True)
        else:
            st.info("暂无预警类型数据")

    st.markdown("---")
    st.subheader("📋 风险错配预警清单 (前50条)")
    if not alerts.empty:
        display_alerts = alerts.sort_values(
            by=['alert_level', 'risk_gap'],
            key=lambda x: x.map({'high': 0, 'medium': 1, 'low': 2}) if x.name == 'alert_level' else x,
            ascending=[True, False]
        ).head(50)
        display_cols = ['stat_date', 'customer_name', 'customer_risk_level', 'product_name', 'product_risk_level',
                        'risk_gap', 'holding_market_value', 'alert_level', 'alert_type', 'alert_message']
        display_alerts = display_alerts[[c for c in display_cols if c in display_alerts.columns]].rename(columns=COLUMN_MAP)
        st.dataframe(display_alerts, use_container_width=True)
    else:
        st.info("暂无预警数据")

    st.markdown("---")
    st.subheader("📋 客户合规状态明细 (前50条)")
    if not compliance.empty:
        display_compliance = compliance.sort_values('mismatch_ratio', ascending=False).head(50)
        display_cols = ['stat_date', 'customer_name', 'customer_risk_level', 'compliance_status',
                        'total_holding_count', 'mismatch_holding_count', 'mismatch_ratio', 'max_risk_gap']
        display_compliance = display_compliance[[c for c in display_cols if c in display_compliance.columns]].rename(columns=COLUMN_MAP)
        st.dataframe(display_compliance, use_container_width=True)
    else:
        st.info("暂无合规明细数据")
