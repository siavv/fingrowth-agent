import os
import re
import time
import pandas as pd
from datetime import datetime
from scoring import calculate_score, get_segment
from prompts import (PLANNER_PROMPT, ANALYST_PROMPT, COPYWRITER_PROMPT,
                     COMPLIANCE_PROMPT, REFLECT_FIX_PROMPT)
from llm_client import call_agent
from market import get_market_summary

API_KEY = os.environ.get("ZHIPU_API_KEY") or input("请粘贴智谱 API Key 后回车：")
BATCH_LIMIT = 5

def parse_verdict(text: str) -> str:
    m = re.search(r"结论\s*[:：]?\s*\**\s*(PASS|FAIL)", text, re.IGNORECASE)
    if m: return m.group(1).upper()
    upper = text.upper()
    if "FAIL" in upper: return "FAIL"
    if "PASS" in upper: return "PASS"
    return "FAIL"

def batch_process():
    print(f"🚀 开始批量处理，共 {BATCH_LIMIT} 个客户...")
    df = pd.read_csv("data/customers.csv")
    df["score"] = df.apply(calculate_score, axis=1)
    df["segment"] = df.apply(lambda r: get_segment(r, r["score"]), axis=1)
    df_batch = df.head(BATCH_LIMIT)
    market_summary = get_market_summary()
    results = []

    for index, customer in df_batch.iterrows():
        cid = customer["customer_id"]
        print(f"\n⏳ 正在处理 {cid} ...")
        customer_info = "；".join([f"{k}={v}" for k, v in customer.to_dict().items()])
        try:
            intent = call_agent(API_KEY, PLANNER_PROMPT, f"客户信息：{customer_info}\n客户分层：{customer['segment']}", temperature=0.1)
            insight = call_agent(API_KEY, ANALYST_PROMPT, f"客户信息：{customer_info}\n评分：{int(customer['score'])}\n分层：{customer['segment']}\n经营意图：{intent}\n市场环境：{market_summary}", temperature=0.1)
            script = call_agent(API_KEY, COPYWRITER_PROMPT, f"客户分层：{customer['segment']}\n经营意图：{intent}\n客户洞察：{insight}", temperature=0.7)
            
            final_script = script
            passed = False
            compliance_rounds = 0
            for round_num in range(1, 4):
                compliance_rounds = round_num
                check = call_agent(API_KEY, COMPLIANCE_PROMPT, final_script, temperature=0.1)
                verdict = parse_verdict(check)
                if verdict == "PASS":
                    passed = True
                    break
                else:
                    final_script = call_agent(API_KEY, REFLECT_FIX_PROMPT, f"原话术：{final_script}\n\n驳回原因：{check}", temperature=0.5)
            
            results.append({
                "customer_id": cid, "run_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "planner_intent": intent, "compliance_rounds": compliance_rounds,
                "compliance_passed": "PASS" if passed else "FAIL",
                "final_script": final_script, "status": "成功"
            })
            print(f"✅ {cid} 处理完成（合规轮次：{compliance_rounds}）")
        except Exception as e:
            print(f"❌ {cid} 处理失败：{e}")
            results.append({
                "customer_id": cid, "run_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "planner_intent": "无", "compliance_rounds": 0, "compliance_passed": "FAIL",
                "final_script": "", "status": f"失败：{str(e)}"
            })
        time.sleep(2)

    os.makedirs("data", exist_ok=True)
    pd.DataFrame(results).to_csv("data/batch_results.csv", index=False, encoding="utf-8-sig")
    print(f"\n🎉 批量处理完成！结果已保存到 data/batch_results.csv")

if __name__ == "__main__":
    batch_process()