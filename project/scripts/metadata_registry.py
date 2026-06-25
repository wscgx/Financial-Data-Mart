"""
元数据注册脚本 - 向 Atlas 注册表和血缘关系

用法:
    python metadata_registry.py [--action register|lineage]
"""
import json
import argparse
import requests

ATLAS_URL = "http://localhost:21000/api/v2"
ATLAS_USER = "admin"
ATLAS_PASSWORD = "admin"

# ── 金融数据仓库表定义 ─────────────────────────────────────
TABLE_DEFINITIONS = {
    "ods_customer": {
        "name": "ods_customer",
        "typeName": "hive_table",
        "attributes": {
            "qualifiedName": "ods_customer@financial_dw",
            "name": "ods_customer",
            "description": "客户信息表 (ODS层)",
            "owner": "data_team",
            "createTime": "2026-01-01",
            "parameters": {"layer": "ods", "domain": "customer"},
        },
    },
    "ods_transaction": {
        "name": "ods_transaction",
        "typeName": "hive_table",
        "attributes": {
            "qualifiedName": "ods_transaction@financial_dw",
            "name": "ods_transaction",
            "description": "交易流水表 (ODS层)",
            "owner": "data_team",
            "parameters": {"layer": "ods", "domain": "transaction"},
        },
    },
    "dwd_customer_asset_daily": {
        "name": "dwd_customer_asset_daily",
        "typeName": "hive_table",
        "attributes": {
            "qualifiedName": "dwd_customer_asset_daily@financial_dw",
            "name": "dwd_customer_asset_daily",
            "description": "客户资产日快照表 (DWD层)",
            "owner": "data_team",
            "parameters": {"layer": "dwd", "domain": "asset"},
        },
    },
    "dws_customer_value_profile": {
        "name": "dws_customer_value_profile",
        "typeName": "hive_table",
        "attributes": {
            "qualifiedName": "dws_customer_value_profile@financial_dw",
            "name": "dws_customer_value_profile",
            "description": "客户价值画像表 (DWS层)",
            "owner": "data_team",
            "parameters": {"layer": "dws", "domain": "customer"},
        },
    },
    "ads_executive_dashboard": {
        "name": "ads_executive_dashboard",
        "typeName": "hive_table",
        "attributes": {
            "qualifiedName": "ads_executive_dashboard@financial_dw",
            "name": "ads_executive_dashboard",
            "description": "高管驾驶舱 (ADS层)",
            "owner": "data_team",
            "parameters": {"layer": "ads", "domain": "executive"},
        },
    },
}

# ── 血缘关系定义 ─────────────────────────────────────────────
LINEAGE_DEFINITIONS = [
    {
        "description": "ODS → DWD 数据流向",
        "source": "ods_holding@financial_dw",
        "target": "dwd_customer_asset_daily@financial_dw",
    },
    {
        "description": "ODS → DWD 数据流向",
        "source": "ods_account@financial_dw",
        "target": "dwd_customer_asset_daily@financial_dw",
    },
    {
        "description": "ODS → DWD 数据流向",
        "source": "ods_customer@financial_dw",
        "target": "dwd_customer_asset_daily@financial_dw",
    },
    {
        "description": "ODS → DWD 数据流向",
        "source": "ods_transaction@financial_dw",
        "target": "dwd_customer_asset_daily@financial_dw",
    },
    {
        "description": "DWD → DWS 数据流向",
        "source": "dwd_customer_asset_daily@financial_dw",
        "target": "dws_customer_value_profile@financial_dw",
    },
    {
        "description": "DWS → ADS 数据流向",
        "source": "dws_customer_value_profile@financial_dw",
        "target": "ads_customer_value_level_dist@financial_dw",
    },
    {
        "description": "DWS → ADS 数据流向",
        "source": "dws_customer_value_profile@financial_dw",
        "target": "ads_customer_aum_ranking@financial_dw",
    },
]


def register_entities():
    """注册元数据实体"""
    print("注册元数据实体...")
    for name, entity in TABLE_DEFINITIONS.items():
        try:
            resp = requests.post(
                f"{ATLAS_URL}/entity",
                json=entity,
                auth=(ATLAS_USER, ATLAS_PASSWORD),
                timeout=30,
            )
            if resp.status_code in (200, 201):
                print(f"  ✓ {name} 注册成功")
            else:
                print(f"  ✗ {name} 注册失败: {resp.status_code} {resp.text[:200]}")
        except requests.ConnectionError:
            print(f"  ✗ 无法连接 Atlas (确保 Docker 中的 atlas 服务已启动)")
            return False
    return True


def register_lineage():
    """注册血缘关系"""
    print("注册血缘关系...")
    for rel in LINEAGE_DEFINITIONS:
        print(f"  {rel['source']} → {rel['target']}: {rel['description']}")
    print("  (血缘关系需要通过 Atlas API 的 lineage 端点注册)")
    return True


def main():
    parser = argparse.ArgumentParser(description="元数据注册脚本")
    parser.add_argument("--action", choices=["register", "lineage", "all"], default="all")
    args = parser.parse_args()

    print("=" * 60)
    print("  金融数据仓库 - 元数据注册")
    print("=" * 60)

    if args.action in ("register", "all"):
        register_entities()

    if args.action in ("lineage", "all"):
        register_lineage()

    print("=" * 60)
    print("  完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
