import re
import os
import pandas as pd
from openai import OpenAI

API_KEY = os.environ.get("ZHIPU_API_KEY") or input("请粘贴智谱 API Key 后回车：")
BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
MODEL = "glm-4-flash"

VIOLATION_KEYWORDS = ["稳赚", "保本", "无风险", "最高收益", "必赚", "零风险", "绝对安全", "保证收益"]

def parse_verdict(text: str) -> str:
    m = re.search(r"结论\s*[:：]?\s*\**\s*(PASS|FAIL)", text, re.IGNORECASE)
    if m: return m.group(1).upper()
    upper = text.upper()
    if "FAIL" in upper: return "FAIL"
    if "PASS" in upper: return "PASS"
    return "FAIL"

def regex_check(text):
    for kw in VIOLATION_KEYWORDS:
        if kw in text: return "FAIL"
    return "PASS"

def llm_check(text):
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "你是金融合规审核官。审核以下话术。第一行只输出 PASS 或 FAIL。待审核话术："},
            {"role": "user", "content": text}
        ], temperature=0.1
    )
    return parse_verdict(resp.choices[0].message.content)

def run_evaluation():
    df = pd.read_csv("data/violation_test_set.csv")
    results = []
    for index, row in df.iterrows():
        text = row["text"]
        expected = row["expected"]
        results.append({"期望": expected, "规则检测": regex_check(text), "LLM检测": llm_check(text)})
    
    result_df = pd.DataFrame(results)
    regex_acc = (result_df["期望"] == result_df["规则检测"]).mean()
    llm_acc = (result_df["期望"] == result_df["LLM检测"]).mean()
    result_df.to_csv("data/eval_results.csv", index=False, encoding="utf-8-sig")
    
    print("=" * 40)
    print(f"📊 评估完成！结果已保存到 data/eval_results.csv")
    print(f"🔍 规则检测准确率：{regex_acc:.1%}")
    print(f"🤖 LLM 检测准确率：{llm_acc:.1%}")
    print("=" * 40)

if __name__ == "__main__":
    run_evaluation()