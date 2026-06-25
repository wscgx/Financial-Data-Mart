import csv
import random
import datetime
import os

# Configuration
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'ods')
os.makedirs(OUTPUT_DIR, exist_ok=True)

NUM_CUSTOMERS = 1000
NUM_ACCOUNTS = 1200
NUM_PRODUCTS = 50
NUM_TRANSACTIONS = 5000
NUM_HOLDINGS = 2000
NUM_RISK_ASSESSMENTS = 800

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

# Customer data
customers = []
first_names = ["Wei", "Fang", "Jun", "Lei", "Yan", "Ming", "Hua", "Jie", "Xin", "Lan"]
last_names = ["Wang", "Li", "Zhang", "Liu", "Chen", "Yang", "Huang", "Zhao", "Wu", "Zhou"]
cities = ["Beijing", "Shanghai", "Guangzhou", "Shenzhen", "Hangzhou", "Nanjing", "Chengdu", "Wuhan", "Xian", "Qingdao"]

for i in range(NUM_CUSTOMERS):
    cust_id = generate_customer_id()
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    gender = random.choice(["M", "F"])
    birth_date = random_date(datetime.date(1960, 1, 1), datetime.date(2000, 12, 31)).isoformat()
    city = random.choice(cities)
    phone = f"1{random.randint(3, 9)}{random.randint(100000000, 999999999)}"
    email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 99)}@example.com"
    reg_date = random_date(datetime.date(2018, 1, 1), datetime.date(2026, 5, 31)).isoformat()
    status = random.choice(["active", "inactive", "suspended"])
    
    customers.append([cust_id, first_name, last_name, gender, birth_date, city, phone, email, reg_date, status])

with open(os.path.join(OUTPUT_DIR, 'ods_customer.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['customer_id', 'first_name', 'last_name', 'gender', 'birth_date', 'city', 'phone', 'email', 'registration_date', 'status'])
    writer.writerows(customers)

# Account data
accounts = []
account_types = ["savings", "checking", "investment", "wealth_management"]
currencies = ["CNY", "USD", "EUR", "HKD"]

for i in range(NUM_ACCOUNTS):
    acct_id = generate_account_id()
    cust_id = random.choice(customers)[0]
    acct_type = random.choice(account_types)
    currency = random.choice(currencies)
    open_date = random_date(datetime.date(2018, 1, 1), datetime.date(2026, 5, 31)).isoformat()
    status = random.choice(["active", "closed", "frozen"])
    branch = random.choice(["Branch_A", "Branch_B", "Branch_C", "Branch_D", "Branch_E"])
    
    accounts.append([acct_id, cust_id, acct_type, currency, open_date, status, branch])

with open(os.path.join(OUTPUT_DIR, 'ods_account.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['account_id', 'customer_id', 'account_type', 'currency', 'open_date', 'status', 'branch'])
    writer.writerows(accounts)

# Product data
products = []
product_types = ["fund", "wealth_product", "bond", "stock", "insurance"]
risk_levels = ["low", "medium_low", "medium", "medium_high", "high"]

for i in range(NUM_PRODUCTS):
    prod_id = generate_product_id()
    prod_name = f"Product_{random.choice(['Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon'])}_{i+1}"
    prod_type = random.choice(product_types)
    risk_level = random.choice(risk_levels)
    min_investment = random.choice([1000, 5000, 10000, 50000, 100000])
    expected_return = round(random.uniform(0.02, 0.15), 4)
    launch_date = random_date(datetime.date(2020, 1, 1), datetime.date(2026, 5, 31)).isoformat()
    maturity_date = random_date(datetime.date(2026, 6, 1), datetime.date(2030, 12, 31)).isoformat()
    status = random.choice(["active", "pending", "matured", "cancelled"])
    manager = random.choice(["Manager_X", "Manager_Y", "Manager_Z"])
    
    products.append([prod_id, prod_name, prod_type, risk_level, min_investment, expected_return, launch_date, maturity_date, status, manager])

with open(os.path.join(OUTPUT_DIR, 'ods_product.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['product_id', 'product_name', 'product_type', 'risk_level', 'min_investment', 'expected_return', 'launch_date', 'maturity_date', 'status', 'manager'])
    writer.writerows(products)

# Transaction data
transactions = []
txn_types = ["purchase", "redemption", "transfer_in", "transfer_out", "dividend"]

start_date = datetime.date(2025, 1, 1)
end_date = datetime.date(2026, 5, 31)

for i in range(NUM_TRANSACTIONS):
    txn_id = generate_transaction_id()
    acct_id = random.choice(accounts)[0]
    prod_id = random.choice(products)[0]
    txn_type = random.choice(txn_types)
    amount = round(random.uniform(1000, 500000), 2)
    price = round(random.uniform(1.0, 10.0), 4)
    quantity = round(amount / price, 2)
    txn_date = random_date(start_date, end_date).isoformat()
    fee = round(amount * random.uniform(0.001, 0.005), 2)
    status = random.choice(["completed", "pending", "failed"])
    
    transactions.append([txn_id, acct_id, prod_id, txn_type, amount, price, quantity, txn_date, fee, status])

with open(os.path.join(OUTPUT_DIR, 'ods_transaction.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['transaction_id', 'account_id', 'product_id', 'transaction_type', 'amount', 'price', 'quantity', 'transaction_date', 'fee', 'status'])
    writer.writerows(transactions)

# Holding data
holdings = []

for i in range(NUM_HOLDINGS):
    acct_id = random.choice(accounts)[0]
    prod_id = random.choice(products)[0]
    quantity = round(random.uniform(10, 10000), 2)
    avg_cost = round(random.uniform(1.0, 10.0), 4)
    market_value = round(quantity * avg_cost * random.uniform(0.8, 1.2), 2)
    profit_loss = round(market_value - (quantity * avg_cost), 2)
    as_of_date = datetime.date(2026, 5, 31).isoformat()
    
    holdings.append([acct_id, prod_id, quantity, avg_cost, market_value, profit_loss, as_of_date])

with open(os.path.join(OUTPUT_DIR, 'ods_holding.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['account_id', 'product_id', 'quantity', 'avg_cost', 'market_value', 'profit_loss', 'as_of_date'])
    writer.writerows(holdings)

# Risk assessment data
risk_assessments = []
risk_categories = ["conservative", "cautious", "balanced", "growth", "aggressive"]

for i in range(NUM_RISK_ASSESSMENTS):
    cust_id = random.choice(customers)[0]
    assessment_date = random_date(datetime.date(2024, 1, 1), datetime.date(2026, 5, 31)).isoformat()
    risk_category = random.choice(risk_categories)
    score = random.randint(1, 100)
    questionnaire_version = f"v{random.randint(1, 5)}.{random.randint(0, 9)}"
    valid_until = random_date(datetime.date(2026, 6, 1), datetime.date(2027, 12, 31)).isoformat()
    status = random.choice(["valid", "expired", "pending_review"])
    
    risk_assessments.append([cust_id, assessment_date, risk_category, score, questionnaire_version, valid_until, status])

with open(os.path.join(OUTPUT_DIR, 'ods_risk_assessment.csv'), 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['customer_id', 'assessment_date', 'risk_category', 'score', 'questionnaire_version', 'valid_until', 'status'])
    writer.writerows(risk_assessments)

print(f"Mock ODS data generated successfully in {OUTPUT_DIR}")
print(f"- ods_customer.csv: {len(customers)} records")
print(f"- ods_account.csv: {len(accounts)} records")
print(f"- ods_product.csv: {len(products)} records")
print(f"- ods_transaction.csv: {len(transactions)} records")
print(f"- ods_holding.csv: {len(holdings)} records")
print(f"- ods_risk_assessment.csv: {len(risk_assessments)} records")
