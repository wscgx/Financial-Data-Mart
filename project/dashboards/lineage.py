import streamlit as st
import graphviz

# 数据血缘关系定义 (基于 dm_src_info 字段)
LINEAGE = {
    # ODS 层
    "ods_holding": {"layer": "ODS", "label": "持仓数据"},
    "ods_transaction": {"layer": "ODS", "label": "交易数据"},
    "ods_customer": {"layer": "ODS", "label": "客户数据"},
    "ods_product": {"layer": "ODS", "label": "产品数据"},
    "ods_account": {"layer": "ODS", "label": "账户数据"},
    "ods_risk_assessment": {"layer": "ODS", "label": "风险测评"},

    # DWD 层
    "dwd_customer_asset_daily": {"layer": "DWD", "label": "客户资产日快照", "sources": ["ods_holding"]},
    "dwd_customer_activity_daily": {"layer": "DWD", "label": "客户行为日明细", "sources": ["ods_transaction"]},
    "dwd_product_sales_daily": {"layer": "DWD", "label": "产品销售日汇总", "sources": ["ods_transaction"]},
    "dwd_customer_risk_match": {"layer": "DWD", "label": "客户风险匹配", "sources": ["ods_holding"]},

    # DWS 层
    "dws_customer_value_profile": {"layer": "DWS", "label": "客户价值画像", "sources": ["dwd_customer_asset_daily"]},
    "dws_product_performance": {"layer": "DWS", "label": "产品业绩汇总", "sources": ["dwd_product_sales_daily"]},
    "dws_risk_compliance_summary": {"layer": "DWS", "label": "风险合规汇总", "sources": ["dwd_customer_risk_match"]},
    "dws_customer_behavior_profile": {"layer": "DWS", "label": "客户行为画像", "sources": ["dwd_customer_activity_daily"]},
    "dws_platform_daily_summary": {"layer": "DWS", "label": "平台日汇总", "sources": ["dwd_customer_asset_daily"]},

    # ADS 层
    "ads_executive_dashboard": {"layer": "ADS", "label": "高管驾驶舱", "sources": ["dws_platform_daily_summary"]},
    "ads_customer_aum_daily": {"layer": "ADS", "label": "客户AUM日榜", "sources": ["dwd_customer_asset_daily"]},
    "ads_customer_aum_ranking": {"layer": "ADS", "label": "客户AUM排名", "sources": ["dws_customer_value_profile"]},
    "ads_customer_net_asset_change": {"layer": "ADS", "label": "客户净资产变动", "sources": ["dwd_customer_asset_daily"]},
    "ads_customer_value_level_dist": {"layer": "ADS", "label": "客户价值分布", "sources": ["dws_customer_value_profile"]},
    "ads_customer_churn_warning": {"layer": "ADS", "label": "客户流失预警", "sources": ["dws_customer_behavior_profile"]},
    "ads_branch_sales_ranking": {"layer": "ADS", "label": "网点销售排名", "sources": ["ods_transaction"]},
    "ads_risk_mismatch_alert": {"layer": "ADS", "label": "风险错配预警", "sources": ["dwd_customer_risk_match"]},
    "ads_risk_metrics_daily": {"layer": "ADS", "label": "风险指标日报", "sources": ["dwd_customer_risk_match", "dws_risk_compliance_summary"]},
    "ads_anomaly_detection": {"layer": "ADS", "label": "异常检测", "sources": ["dws_platform_daily_summary", "ods_transaction", "dwd_customer_asset_daily"]},
    "ads_multi_dimension_analysis": {"layer": "ADS", "label": "多维分析", "sources": ["ods_customer", "ods_product", "ods_risk_assessment", "dwd_customer_asset_daily"]},
}

LAYER_COLORS = {
    "ODS": "#4A90D9",
    "DWD": "#50C878",
    "DWS": "#FFA500",
    "ADS": "#FF6B6B",
}

LAYER_ORDER = ["ODS", "DWD", "DWS", "ADS"]


def build_full_lineage_graph():
    dot = graphviz.Digraph(comment="数据血缘图")
    dot.attr(rankdir="LR", splines="ortho", nodesep="0.8", ranksep="1.2")
    dot.attr("node", shape="box", style="filled,rounded", fontname="Microsoft YaHei", fontsize="11")
    dot.attr("edge", color="#666666", arrowsize="0.8")

    for layer in LAYER_ORDER:
        with dot.subgraph(name=f"cluster_{layer}") as c:
            c.attr(label=layer, style="dashed", color=LAYER_COLORS[layer], fontcolor=LAYER_COLORS[layer], fontsize="14")
            for table, info in LINEAGE.items():
                if info["layer"] == layer:
                    c.node(table, f"{info['label']}\n({table})", fillcolor=LAYER_COLORS[layer], fontcolor="white")

    for table, info in LINEAGE.items():
        for src in info.get("sources", []):
            dot.edge(src, table)

    return dot


def build_table_lineage_graph(table_name):
    if table_name not in LINEAGE:
        return None

    dot = graphviz.Digraph(comment=f"{table_name} 血缘图")
    dot.attr(rankdir="LR", splines="ortho", nodesep="0.8", ranksep="1.2")
    dot.attr("node", shape="box", style="filled,rounded", fontname="Microsoft YaHei", fontsize="11")
    dot.attr("edge", color="#666666", arrowsize="0.8")

    visited = set()

    def add_upstream(t):
        if t in visited:
            return
        visited.add(t)
        info = LINEAGE.get(t, {})
        layer = info.get("layer", "ODS")
        color = LAYER_COLORS.get(layer, "#999999")
        dot.node(t, f"{info.get('label', t)}\n({t})", fillcolor=color, fontcolor="white")
        for src in info.get("sources", []):
            src_info = LINEAGE.get(src, {})
            src_layer = src_info.get("layer", "ODS")
            src_color = LAYER_COLORS.get(src_layer, "#999999")
            dot.node(src, f"{src_info.get('label', src)}\n({src})", fillcolor=src_color, fontcolor="white")
            dot.edge(src, t)
            add_upstream(src)

    def add_downstream(t):
        if t in visited:
            return
        visited.add(t)
        info = LINEAGE.get(t, {})
        layer = info.get("layer", "ODS")
        color = LAYER_COLORS.get(layer, "#999999")
        dot.node(t, f"{info.get('label', t)}\n({t})", fillcolor=color, fontcolor="white")
        for tbl, tbl_info in LINEAGE.items():
            if t in tbl_info.get("sources", []):
                tbl_layer = tbl_info.get("layer", "ADS")
                tbl_color = LAYER_COLORS.get(tbl_layer, "#999999")
                dot.node(tbl, f"{tbl_info.get('label', tbl)}\n({tbl})", fillcolor=tbl_color, fontcolor="white")
                dot.edge(t, tbl)
                add_downstream(tbl)

    add_upstream(table_name)
    visited.discard(table_name)
    add_downstream(table_name)

    return dot


def render_lineage():
    st.title("📊 数据血缘图")
    st.caption("基于 dm_src_info 字段构建，展示表间数据流转关系")

    tab1, tab2 = st.tabs(["全局血缘", "表级血缘"])

    with tab1:
        st.subheader("ODS → DWD → DWS → ADS 完整链路")
        dot = build_full_lineage_graph()
        st.graphviz_chart(dot, use_container_width=True)

        with st.expander("血缘关系明细"):
            for layer in LAYER_ORDER:
                st.markdown(f"**{layer} 层**")
                for table, info in LINEAGE.items():
                    if info["layer"] == layer:
                        sources = info.get("sources", [])
                        if sources:
                            st.write(f"  {info['label']} ({table}) ← {', '.join(sources)}")
                        else:
                            st.write(f"  {info['label']} ({table}) [源表]")
                st.write("")

    with tab2:
        st.subheader("查询指定表的血缘关系")
        all_tables = sorted(LINEAGE.keys())
        selected = st.selectbox("选择表", all_tables, format_func=lambda x: f"{LINEAGE[x]['label']} ({x})")

        if selected:
            col1, col2, col3 = st.columns(3)
            info = LINEAGE[selected]
            col1.metric("所属层级", info["layer"])
            col2.metric("中文名称", info["label"])
            col3.metric("上游表数", len(info.get("sources", [])))

            dot = build_table_lineage_graph(selected)
            if dot:
                st.graphviz_chart(dot, use_container_width=True)

            with st.expander("上游链路"):
                def trace_upstream(t, depth=0):
                    info = LINEAGE.get(t, {})
                    sources = info.get("sources", [])
                    prefix = "  " * depth
                    st.write(f"{prefix}← {info.get('label', t)} ({t})")
                    for s in sources:
                        trace_upstream(s, depth + 1)
                trace_upstream(selected)

            with st.expander("下游链路"):
                def trace_downstream(t, depth=0):
                    info = LINEAGE.get(t, {})
                    prefix = "  " * depth
                    st.write(f"{prefix}→ {info.get('label', t)} ({t})")
                    for tbl, tbl_info in LINEAGE.items():
                        if t in tbl_info.get("sources", []):
                            trace_downstream(tbl, depth + 1)
                trace_downstream(selected)
