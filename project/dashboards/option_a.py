import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from dashboards.common import load_data, COLUMN_MAP


def render_option_a():
    st.title("📊 AI智能财富分析平台 - 客户资产价值看板")

    st.sidebar.header("🔍 筛选条件")

    date_list = load_data("SELECT DISTINCT stat_date FROM ads_customer_aum_daily ORDER BY stat_date DESC")
    selected_date = st.sidebar.selectbox("📅 数据日期", list(date_list['stat_date']))

    cities = load_data("SELECT DISTINCT city FROM ads_customer_aum_daily ORDER BY city")
    selected_city = st.sidebar.selectbox("选择城市", ["全部"] + list(cities['city']))

    aum_daily = load_data(f"SELECT stat_date, customer_id, customer_name, city, total_aum, holding_market_value FROM ads_customer_aum_daily WHERE stat_date = '{selected_date}'")
    value_dist = load_data("SELECT level_name, customer_count FROM ads_customer_value_level_dist")
    aum_ranking = load_data(f"SELECT ranking, customer_name, city, total_aum FROM ads_customer_aum_ranking WHERE stat_date = '{selected_date}' ORDER BY ranking")
    net_change = load_data(f"SELECT stat_date, city, purchase_amount, redemption_amount, profit_loss, net_asset_change FROM ads_customer_net_asset_change WHERE stat_date = '{selected_date}'")

    st.info(f"📊 当前查看日期: **{selected_date}**")

    if selected_city != "全部":
        aum_daily = aum_daily[aum_daily['city'] == selected_city]
        aum_ranking = aum_ranking[aum_ranking['city'] == selected_city]
        net_change = net_change[net_change['city'] == selected_city]

    col1, col2, col3, col4 = st.columns(4)
    total_aum = aum_daily['total_aum'].sum()
    cust_count = aum_daily['customer_id'].nunique()
    mid_cust = value_dist[value_dist['level_name']=='中端客户']['customer_count'].sum() if not value_dist.empty else 0
    net_chg = net_change['net_asset_change'].sum()

    col1.metric("总资产(AUM)", f"¥{total_aum:,.2f}")
    col2.metric("客户总数", f"{cust_count:,}")
    col3.metric("中端及以上客户", f"{mid_cust:,}")
    col4.metric("资产净变动", f"¥{net_chg:,.2f}", delta="↑" if net_chg > 0 else "↓")

    st.markdown("---")

    row1_col1, row1_col2 = st.columns([1, 1])

    with row1_col1:
        st.subheader("🥧 客户价值等级分布")
        fig_pie = px.pie(value_dist, values='customer_count', names='level_name', hole=0.4,
                         labels={'customer_count': '客户数', 'level_name': '客户等级'},
                         color_discrete_map={'高净值客户': '#FF6B6B', '中端客户': '#4ECDC4', '普通客户': '#95A5A6'})
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

    with row1_col2:
        st.subheader("🏆 AUM 排名 TOP 10")
        top10 = aum_ranking.head(10)
        fig_bar = px.bar(top10, x='total_aum', y='customer_name', orientation='h', text='total_aum',
                         labels={'total_aum': '总资产(AUM)', 'customer_name': '客户姓名'},
                         color='total_aum', color_continuous_scale='Bluered')
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        fig_bar.update_traces(texttemplate='¥%{text:,.0f}', textposition='outside')
        st.plotly_chart(fig_bar, use_container_width=True)

    row2_col1, row2_col2 = st.columns([1, 1])

    with row2_col1:
        st.subheader("📈 资产变动归因")
        change_data = net_change.groupby('stat_date')[['purchase_amount', 'redemption_amount', 'profit_loss']].sum().reset_index()
        fig_stack = go.Figure()
        fig_stack.add_trace(go.Bar(x=change_data['stat_date'], y=change_data['purchase_amount'], name='申购金额'))
        fig_stack.add_trace(go.Bar(x=change_data['stat_date'], y=change_data['redemption_amount'], name='赎回金额'))
        fig_stack.add_trace(go.Bar(x=change_data['stat_date'], y=change_data['profit_loss'], name='盈亏'))
        fig_stack.update_layout(barmode='stack', xaxis_title='统计日期', yaxis_title='金额')
        st.plotly_chart(fig_stack, use_container_width=True)

    with row2_col2:
        st.subheader("📋 客户资产明细 (前50)")
        display_df = aum_daily.sort_values('total_aum', ascending=False).head(50)[['customer_name', 'city', 'total_aum', 'holding_market_value']].rename(columns=COLUMN_MAP)
        st.dataframe(display_df, use_container_width=True)
