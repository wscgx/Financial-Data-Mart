"""
生成2个月连续测试数据（2026年5月1日 - 2026年6月30日）
用于测试 Delta Lake 查询和 ETL 流程
"""
import csv
import random
import datetime
import os

# Configuration
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'ods')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 数据量配置
NUM_CUSTOMERS = 1000
NUM_ACCOUNTS = 1200
NUM_PRODUCTS = 50
NUM_TRANSACTIONS_PER_DAY = 40  # 每天40笔交易
NUM_RISK_ASSESSMENTS = 800

# 日期范围
START_DATE = datetime.date(2026, 5, 1)
END_DATE = datetime.date(2026, 6, 30)
NUM_DAYS = (END_DATE - START_DATE).days + 1  # 61天

# Helper functions
def random_date(start, end):
    delta = end - start
    random_days = random.randint(0, delta.days)
    return start + datetime.timedelta(days=random_days)

def generate_customer_id():
    return f"CUST{random.randint(100000, 999999)}"

def generate_account_id():
    return f"ACCT{random.randint(1000000, 9999999)}"

def generate_product_id():
    return f"PROD{random.randint(1000, 9999)}"

def generate_transaction_id():
    return f"TXN{random.randint(10000000, 99999999)}"

def generate_holding_id():
    return f"HOLD{random.randint(1000000, 9999999)}"

# ── 1. 客户数据 ──────────────────────────────────────────────
print("生成客户数据...")
customers = []
first_names = ["Wei", "Fang", "Jun", "Lei", "Yan", "Ming", "Hua", "Jie", "Xin", "Lan",
               "Tao", "Qiang", "Ning", "Xiao", "Chen", "Long", "Hao", "Ran", "Bin", "Ting"]
last_names = ["Wang", "Li", "Zhang", "Liu", "Chen", "Yang", "Huang", "Zhao", "Wu", "Zhou",
              "Sun", "Ma", "Zhu", "Hu", "Guo", "Lin", "He", "Gao", "Luo", "Zheng"]
cities = ["Beijing", "Shanghai", "Guangzhou", "Shenzhen", "Hangzhou", 
          "Nanjing", "Chengdu", "Wuhan", "Xian", "Qingdao"]

for i in range(NUM_CUSTOMERS):
    cust_id = generate_customer_id()
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    gender = random.choice(["M", "F"])
    birth_date = random_date(datetime.date(1960, 1, 1), datetime.date(2000, 12, 31)).isoformat()
    city = random.choice(cities)
    phone = f"1{random.randint(3, 9)}{random.randint(100000000, 999999999)}"
    email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@example.com"
    # 70%的客户在2026年5-6月注册
    if random.random() < 0.7:
        reg_date = random_date(START_DATE, END_DATE).isoformat()
    else:
        reg_date = random_date(datetime.date(2018, 1, 1), datetime.date(2026, 4, 30)).isoformat()
    status = random.choices(["active", "inactive", "suspended"], weights=[0.8, 0.15, 0.05])[0]
    
    customers.append([cust_id, first_name, last_name, gender, birth_date, city, phone, email, reg_date, status])

# 去重检查
seen_ids = set()
unique_customers = []
for c in customers:
    if c[0] not in seen_ids:
        seen_ids.add(c[0])
        unique_customers.append(c)
customers = unique_customers[:NUM_CUSTOMERS]

with open(os.path.join(OUTPUT_DIR, 'ods_customer.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['customer_id', 'first_name', 'last_name', 'gender', 'birth_date', 
                     'city', 'phone', 'email', 'registration_date', 'status'])
    writer.writerows(customers)
print(f"  - ods_customer.csv: {len(customers)} 条记录")

# ── 2. 账户数据 ──────────────────────────────────────────────
print("生成账户数据...")
accounts = []
account_types = ["savings", "checking", "investment", "wealth_management"]
currencies = ["CNY", "USD", "EUR", "HKD"]
branches = ["Branch_A", "Branch_B", "Branch_C", "Branch_D", "Branch_E"]

for i in range(NUM_ACCOUNTS):
    acct_id = generate_account_id()
    cust_id = random.choice(customers)[0]
    acct_type = random.choice(account_types)
    currency = random.choices(currencies, weights=[0.7, 0.15, 0.1, 0.05])[0]
    # 60%的账户在2026年5-6月开户
    if random.random() < 0.6:
        open_date = random_date(START_DATE, END_DATE).isoformat()
    else:
        open_date = random_date(datetime.date(2018, 1, 1), datetime.date(2026, 4, 30)).isoformat()
    status = random.choices(["active", "closed", "frozen"], weights=[0.85, 0.1, 0.05])[0]
    branch = random.choice(branches)
    
    accounts.append([acct_id, cust_id, acct_type, currency, open_date, status, branch])

# 去重检查
seen_ids = set()
unique_accounts = []
for a in accounts:
    if a[0] not in seen_ids:
        seen_ids.add(a[0])
        unique_accounts.append(a)
accounts = unique_accounts[:NUM_ACCOUNTS]

with open(os.path.join(OUTPUT_DIR, 'ods_account.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['account_id', 'customer_id', 'account_type', 'currency', 
                     'open_date', 'status', 'branch'])
    writer.writerows(accounts)
print(f"  - ods_account.csv: {len(accounts)} 条记录")

# ── 3. 产品数据 ──────────────────────────────────────────────
print("生成产品数据...")
products = []
product_types = ["fund", "wealth_product", "bond", "stock", "insurance"]
risk_levels = ["low", "medium_low", "medium", "medium_high", "high"]
managers = ["Manager_X", "Manager_Y", "Manager_Z"]

for i in range(NUM_PRODUCTS):
    prod_id = f"PROD{1000 + i}"
    prod_name = f"Product_{random.choice(['Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon'])}_{i+1}"
    prod_type = random.choice(product_types)
    risk_level = random.choice(risk_levels)
    min_investment = random.choice([1000, 5000, 10000, 50000, 100000])
    expected_return = round(random.uniform(0.02, 0.15), 4)
    launch_date = random_date(datetime.date(2020, 1, 1), datetime.date(2026, 6, 30)).isoformat()
    maturity_date = random_date(datetime.date(2027, 1, 1), datetime.date(2030, 12, 31)).isoformat()
    status = random.choices(["active", "pending", "matured", "cancelled"], weights=[0.7, 0.15, 0.1, 0.05])[0]
    manager = random.choice(managers)
    
    products.append([prod_id, prod_name, prod_type, risk_level, min_investment, 
                    expected_return, launch_date, maturity_date, status, manager])

with open(os.path.join(OUTPUT_DIR, 'ods_product.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['product_id', 'product_name', 'product_type', 'risk_level', 
                     'min_investment', 'expected_return', 'launch_date', 'maturity_date', 
                     'status', 'manager'])
    writer.writerows(products)
print(f"  - ods_product.csv: {len(products)} 条记录")

# ── 4. 交易数据（连续2个月，每天40笔）─────────────────────────
print("生成交易数据...")
transactions = []
txn_types = ["purchase", "redemption", "transfer_in", "transfer_out", "dividend"]
txn_weights = [0.4, 0.25, 0.15, 0.15, 0.05]  # 申购最多

# 活跃账户（用于生成交易）
active_accounts = [a for a in accounts if a[5] == "active"]
active_products = [p for p in products if p[8] == "active"]

for day_offset in range(NUM_DAYS):
    current_date = START_DATE + datetime.timedelta(days=day_offset)
    
    # 工作日交易更多，周末更少
    is_weekday = current_date.weekday() < 5
    num_txns = NUM_TRANSACTIONS_PER_DAY if is_weekday else NUM_TRANSACTIONS_PER_DAY // 2
    
    for _ in range(num_txns):
        txn_id = generate_transaction_id()
        acct_id = random.choice(active_accounts)[0]
        prod_id = random.choice(active_products)[0]
        txn_type = random.choices(txn_types, weights=txn_weights)[0]
        
        # 根据交易类型调整金额范围
        if txn_type == "purchase":
            amount = round(random.uniform(5000, 200000), 2)
        elif txn_type == "redemption":
            amount = round(random.uniform(1000, 100000), 2)
        elif txn_type in ["transfer_in", "transfer_out"]:
            amount = round(random.uniform(10000, 500000), 2)
        else:  # dividend
            amount = round(random.uniform(100, 10000), 2)
        
        price = round(random.uniform(1.0, 10.0), 4)
        quantity = round(amount / price, 2)
        
        # 交易时间随机分布
        hour = random.randint(9, 15)
        minute = random.randint(0, 59)
        txn_date = f"{current_date.isoformat()} {hour:02d}:{minute:02d}:00"
        
        fee = round(amount * random.uniform(0.001, 0.003), 2)
        status = random.choices(["completed", "pending", "failed"], weights=[0.9, 0.08, 0.02])[0]
        
        transactions.append([txn_id, acct_id, prod_id, txn_type, amount, price, 
                           quantity, txn_date, fee, status])

# 去重检查
seen_ids = set()
unique_transactions = []
for t in transactions:
    if t[0] not in seen_ids:
        seen_ids.add(t[0])
        unique_transactions.append(t)
transactions = unique_transactions

with open(os.path.join(OUTPUT_DIR, 'ods_transaction.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['transaction_id', 'account_id', 'product_id', 'transaction_type', 
                     'amount', 'price', 'quantity', 'transaction_date', 'fee', 'status'])
    writer.writerows(transactions)
print(f"  - ods_transaction.csv: {len(transactions)} 条记录")

# ── 5. 持仓数据（每日快照，连续2个月）─────────────────────────
print("生成持仓数据（每日快照）...")
holdings = []

# 为每个活跃账户生成每日持仓快照
for acct in active_accounts:
    acct_id = acct[0]
    # 每个账户持有1-3个产品
    num_products = random.randint(1, 3)
    held_products = random.sample(active_products, min(num_products, len(active_products)))
    
    # 初始持仓（5月1日）
    initial_quantity = round(random.uniform(100, 5000), 2)
    initial_avg_cost = round(random.uniform(1.0, 8.0), 4)
    
    for prod in held_products:
        prod_id = prod[0]
        quantity = initial_quantity
        avg_cost = initial_avg_cost
        
        for day_offset in range(NUM_DAYS):
            current_date = START_DATE + datetime.timedelta(days=day_offset)
            
            # 模拟市值波动（每日±2%）
            price_change = random.uniform(0.98, 1.02)
            market_value = round(quantity * avg_cost * price_change * random.uniform(0.9, 1.1), 2)
            profit_loss = round(market_value - (quantity * avg_cost), 2)
            
            holding_id = generate_holding_id()
            as_of_date = current_date.isoformat()
            
            holdings.append([holding_id, acct_id, prod_id, quantity, avg_cost, 
                           market_value, profit_loss, as_of_date])
            
            # 偶尔调整持仓数量（模拟申赎）
            if random.random() < 0.05:  # 5%概率调整
                quantity = round(quantity * random.uniform(0.9, 1.1), 2)

with open(os.path.join(OUTPUT_DIR, 'ods_holding.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['holding_id', 'account_id', 'product_id', 'quantity', 'avg_cost', 
                     'market_value', 'profit_loss', 'as_of_date'])
    writer.writerows(holdings)
print(f"  - ods_holding.csv: {len(holdings)} 条记录")

# ── 6. 风险测评数据 ──────────────────────────────────────────
print("生成风险测评数据...")
risk_assessments = []
risk_categories = ["conservative", "cautious", "balanced", "growth", "aggressive"]

for i in range(NUM_RISK_ASSESSMENTS):
    cust_id = random.choice(customers)[0]
    # 60%的测评在2026年5-6月
    if random.random() < 0.6:
        assessment_date = random_date(START_DATE, END_DATE).isoformat()
    else:
        assessment_date = random_date(datetime.date(2024, 1, 1), datetime.date(2026, 4, 30)).isoformat()
    
    risk_category = random.choice(risk_categories)
    score = random.randint(1, 100)
    questionnaire_version = f"v{random.randint(1, 5)}.{random.randint(0, 9)}"
    valid_until = random_date(datetime.date(2026, 7, 1), datetime.date(2028, 12, 31)).isoformat()
    status = random.choices(["valid", "expired", "pending_review"], weights=[0.7, 0.2, 0.1])[0]
    
    risk_assessments.append([cust_id, assessment_date, risk_category, score, 
                           questionnaire_version, valid_until, status])

with open(os.path.join(OUTPUT_DIR, 'ods_risk_assessment.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['customer_id', 'assessment_date', 'risk_category', 'score', 
                     'questionnaire_version', 'valid_until', 'status'])
    writer.writerows(risk_assessments)
print(f"  - ods_risk_assessment.csv: {len(risk_assessments)} 条记录")

# ── 汇总 ─────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("2个月连续测试数据生成完成！")
print("=" * 60)
print(f"数据日期范围: {START_DATE} 至 {END_DATE} ({NUM_DAYS}天)")
print(f"\n生成的文件:")
print(f"  - ods_customer.csv:          {len(customers):>6} 条")
print(f"  - ods_account.csv:           {len(accounts):>6} 条")
print(f"  - ods_product.csv:           {len(products):>6} 条")
print(f"  - ods_transaction.csv:       {len(transactions):>6} 条 (每天约{len(transactions)//NUM_DAYS}笔)")
print(f"  - ods_holding.csv:           {len(holdings):>6} 条 (每日快照)")
print(f"  - ods_risk_assessment.csv:   {len(risk_assessments):>6} 条")
print(f"\n输出目录: {OUTPUT_DIR}")
print("=" * 60)
