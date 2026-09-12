def calculate_score(row):
    score = 0
    assets = row['investable_assets']
    if assets >= 1000000: score += 40
    elif assets >= 500000: score += 30
    elif assets >= 100000: score += 20
    else: score += 10
    if row['recent_30d_consult'] == '是': score += 15
    if row['recent_30d_fund_view'] == '是': score += 8
    if row['recent_30d_deposit_view'] == '是': score += 5
    d = row['last_interaction_days']
    if d <= 7: score += 10
    elif d <= 30: score += 5
    elif d > 60: score -= 5
    income = row['annual_income']
    if income >= 500000: score += 15
    elif income >= 200000: score += 10
    else: score += 5
    if row['owned_product_type'] != '无': score += 5
    return max(score, 0)

def get_segment(row, score):
    has_intent = (row['recent_30d_consult'] == '是') or (row['recent_30d_fund_view'] == '是')
    high_value = (row['investable_assets'] >= 500000) or (row['annual_income'] >= 400000)
    if score >= 70 and has_intent: return '高价值高意向'
    if high_value and not has_intent: return '高价值低意向'
    if score >= 40: return '潜力客户'
    return '维护客户'