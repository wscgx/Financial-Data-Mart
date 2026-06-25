import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from dashboards.common import load_data, COLUMN_MAP


def render_option_b():
    st.title("📊 AI智能财富分析平台 - 产品销售与业绩看板")

    st.sidebar.header("🔍 筛选条件")

    date_list = load_data("SELECT DISTINCT DATE(stat_date) AS stat_date FROM ads_branch_sales_ranking ORDER BY stat_date DESC")
    selected_date = st.sidebar.selectbox("📅 数据日期", list(date_list['stat_date']))

    products = load_data("SELECT DISTINCT product_name FROM dws_product_performance ORDER BY product_name")
    selected_product = st.sidebar.selectbox("选择产品", ["全部"] + list(products['product_name']))

    branches = load_data("SELECT DISTINCT branch FROM ads_branch_sales_ranking ORDER BY branch")
    selected_branch = st.sidebar.selectbox("选择网点", ["全部"] + list(branches['branch']))

    branch_ranking = load_data("SELECT stat_date, branch, total_sales_amount, total_redemption_amount, net_sales_amount, transaction_count, customer_count, sales_ranking, sales_share FROM ads_branch_sales_ranking WHERE DATE(stat_date) = '{}' ORDER BY sales_ranking".format(selected_date))
    product_perf = load_data("SELECT stat_date, product_name, product_type, total_sales_amount, total_redemption_amount, net_sales_amount, total_customer_count, expected_return FROM dws_product_performance WHERE DATE(stat_date) = '{}'".format(selected_date))
    product_daily = load_data("SELECT stat_date, product_name, purchase_amount, redemption_amount FROM dwd_product_sales_daily WHERE DATE(stat_date) = '{}'".format(selected_date))

    st.info(f"📊 当前查看日期: **{selected_date}**")

    if selected_product != "全部":
        product_perf = product_perf[product_perf['product_name'] == selected_product]
        product_daily = product_daily[product_daily['product_name'] == selected_product]

    if selected_branch != "全部":
        branch_ranking = branch_ranking[branch_ranking['branch'] == selected_branch]

    latest_date = branch_ranking['stat_date'].max() if not branch_ranking.empty else None
    latest_date_perf = product_perf['stat_date'].max() if not product_perf.empty else None

    st.subheader("📌 核心指标")
    col1, col2, col3, col4 = st.columns(4)

    if latest_date:
        day_sales = branch_ranking[branch_ranking['stat_date'] == latest_date]['total_sales_amount'].sum()
        day_redemption = branch_ranking[branch_ranking['stat_date'] == latest_date]['total_redemption_amount'].sum()
        day_net = branch_ranking[branch_ranking['stat_date'] == latest_date]['net_sales_amount'].sum()
        day_txn = branch_ranking[branch_ranking['stat_date'] == latest_date]['transaction_count'].sum()
    else:
        day_sales = day_redemption = day_net = day_txn = 0

    col1.metric("当日销售总额", f"¥{day_sales:,.2f}")
    col2.metric("当日赎回总额", f"¥{day_redemption:,.2f}")
    col3.metric("当日净销售额", f"¥{day_net:,.2f}", delta="↑" if day_net > 0 else "↓")
    col4.metric("当日交易笔数", f"{day_txn:,}")

    st.markdown("---")

    row1_col1, row1_col2 = st.columns([1, 1])

    with row1_col1:
        st.subheader("🏆 网点销售排名")
        latest_branch = branch_ranking[branch_ranking['stat_date'] == latest_date].sort_values('sales_ranking').head(10)
        if not latest_branch.empty:
            fig_branch = px.bar(latest_branch, x='total_sales_amount', y='branch', orientation='h', text='total_sales_amount',
                                labels={'total_sales_amount': '销售总额', 'branch': '网点'},
                                color='total_sales_amount', color_continuous_scale='Viridis')
            fig_branch.update_layout(yaxis={'categoryorder':'total ascending'})
            fig_branch.update_traces(texttemplate='¥%{text:,.0f}', textposition='outside')
            st.plotly_chart(fig_branch, use_container_width=True)
        else:
            st.info("暂无网点销售数据")

    with row1_col2:
        st.subheader("📊 产品销售 TOP 10")
        if latest_date_perf and not product_perf.empty:
            latest_prod = product_perf[product_perf['stat_date'] == latest_date_perf].sort_values('total_sales_amount', ascending=False).head(10)
            fig_prod = px.bar(latest_prod, x='total_sales_amount', y='product_name', orientation='h', text='total_sales_amount',
                              labels={'total_sales_amount': '累计销售额', 'product_name': '产品名称'},
                              color='total_sales_amount', color_continuous_scale='Plasma')
            fig_prod.update_layout(yaxis={'categoryorder':'total ascending'})
            fig_prod.update_traces(texttemplate='¥%{text:,.0f}', textposition='outside')
            st.plotly_chart(fig_prod, use_container_width=True)
        else:
            st.info("暂无产品销售数据")

    row2_col1, row2_col2 = st.columns([1, 1])

    with row2_col1:
        st.subheader("📈 销售趋势（近30日）")
        if not product_daily.empty:
            trend = product_daily.groupby('stat_date')[['purchase_amount', 'redemption_amount']].sum().reset_index()
            trend = trend.sort_values('stat_date').tail(30)
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(x=trend['stat_date'], y=trend['purchase_amount'], mode='lines+markers', name='申购金额', line=dict(color='#4ECDC4')))
            fig_trend.add_trace(go.Scatter(x=trend['stat_date'], y=trend['redemption_amount'], mode='lines+markers', name='赎回金额', line=dict(color='#FF6B6B')))
            fig_trend.update_layout(xaxis_title='统计日期', yaxis_title='金额', hovermode='x unified')
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("暂无趋势数据")

    with row2_col2:
        st.subheader("🥧 网点销售占比")
        if latest_date and not branch_ranking.empty:
            share_data = branch_ranking[branch_ranking['stat_date'] == latest_date]
            fig_share = px.pie(share_data, values='sales_share', names='branch', hole=0.4,
                               labels={'sales_share': '销售占比', 'branch': '网点'})
            fig_share.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_share, use_container_width=True)
        else:
            st.info("暂无占比数据")

    row3_col1, row3_col2 = st.columns([1, 1])

    with row3_col1:
        st.subheader("📊 产品类型销售分布")
        if latest_date_perf and not product_perf.empty:
            type_sales = product_perf[product_perf['stat_date'] == latest_date_perf].groupby('product_type')['total_sales_amount'].sum().reset_index()
            fig_type = px.pie(type_sales, values='total_sales_amount', names='product_type', hole=0.4,
                              labels={'total_sales_amount': '累计销售额', 'product_type': '产品类型'})
            fig_type.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_type, use_container_width=True)
        else:
            st.info("暂无类型分布数据")

    with row3_col2:
        st.subheader("📋 产品业绩明细 (前20)")
        if latest_date_perf and not product_perf.empty:
            top20 = product_perf[product_perf['stat_date'] == latest_date_perf].sort_values('total_sales_amount', ascending=False).head(20)
            display_cols = ['product_name', 'product_type', 'total_sales_amount', 'total_redemption_amount', 'net_sales_amount', 'total_customer_count', 'expected_return']
            display_df = top20[[c for c in display_cols if c in top20.columns]].rename(columns=COLUMN_MAP)
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("暂无产品业绩数据")

    st.markdown("---")
    st.subheader("📋 网点销售明细")
    if not branch_ranking.empty:
        display_branch = branch_ranking.sort_values(['stat_date', 'sales_ranking'])[['stat_date', 'branch', 'total_sales_amount', 'total_redemption_amount', 'net_sales_amount', 'transaction_count', 'customer_count', 'sales_ranking', 'sales_share']].rename(columns=COLUMN_MAP)
        st.dataframe(display_branch, use_container_width=True)
    else:
        st.info("暂无网点销售明细数据")
