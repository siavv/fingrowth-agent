import pandas as pd
import random
import os

random.seed(42)
cities = ['北京', '上海', '深圳', '杭州', '成都', '广州', '南京', '武汉']
notes = ['关注指数定投', '关注稳健理财', '咨询过黄金', '想了解保险', '没有明显偏好', '之前咨询过未购买', '关注养老规划']

rows = []
for i in range(1, 51):
    age = random.randint(24, 58)
    if age < 30:
        occupation = random.choice(['互联网运营', '工程师', '销售', '产品经理'])
        annual_income = random.choice([80000, 120000, 180000, 220000])
    elif age < 45:
        occupation = random.choice(['企业主', '金融从业者', '医生', '工程师', '公务员'])
        annual_income = random.choice([200000, 300000, 400000, 500000])
    else:
        occupation = random.choice(['企业主', '教师', '医生', '公务员', '个体经营'])
        annual_income = random.choice([150000, 250000, 400000, 800000])

    if annual_income >= 400000:
        investable_assets = random.choice([1000000, 1500000, 3000000, 5000000])
    elif annual_income >= 200000:
        investable_assets = random.choice([300000, 500000, 800000, 1000000])
    else:
        investable_assets = random.choice([50000, 100000, 150000, 300000])

    if age > 50:
        risk = random.choice(['低', '中'])
    elif age < 35:
        risk = random.choice(['中', '中高'])
    else:
        risk = random.choice(['低', '中', '中高'])

    customer_note = random.choice(notes) if random.random() > 0.1 else ""

    rows.append({
        'customer_id': f'C{i:03d}', 'age': age, 'city': random.choice(cities),
        'occupation': occupation, 'annual_income': annual_income,
        'investable_assets': investable_assets, 'risk_preference': risk,
        'marital_status': random.choice(['已婚', '未婚']), 'has_mortgage': random.choice(['是', '否']),
        'recent_30d_consult': '是' if random.random() > 0.5 else '否',
        'recent_30d_fund_view': '是' if random.random() > 0.5 else '否',
        'recent_30d_deposit_view': '是' if random.random() > 0.6 else '否',
        'has_credit_card': random.choice(['是', '否']),
        'owned_product_type': random.choice(['存款', '基金', '股票/基金', '保险', '存款,基金', '无']),
        'last_interaction_days': random.randint(1, 90), 'customer_note': customer_note
    })

os.makedirs('data', exist_ok=True)
pd.DataFrame(rows).to_csv('data/customers.csv', index=False, encoding='utf-8-sig')
print('已生成50条具备业务相关性的模拟客户数据，保存在 data/customers.csv')