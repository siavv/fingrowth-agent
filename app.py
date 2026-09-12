import re
import os
import random
import streamlit as st
import pandas as pd
from datetime import datetime

from scoring import calculate_score, get_segment
from prompts import (PLANNER_PROMPT, ANALYST_PROMPT, COPYWRITER_PROMPT,
                     COMPLIANCE_PROMPT, REFLECT_FIX_PROMPT)
from llm_client import call_agent
from market import get_market_summary

VIOLATION_KEYWORDS = ["稳健增值", "给资金上把锁", "安全可靠", "稳赚", "稳赚不赔", "保本", "零风险", "绝对安全", "无风险", "绝对没问题", "放心买", "预期收益", "保证收益", "年化收益", "收益稳定", "高收益", "可观收益", "收益潜力", "赶紧入手", "抢着买", "极力推荐", "抓紧", "错过就没", "尽快决策", "尽快入手"]

def hard_check(text: str):
    issues = []
    for kw in VIOLATION_KEYWORDS:
        if kw in text: issues.append(f"出现违规词「{kw}」")
    return (len(issues) == 0), issues

def parse_verdict(text: str) -> str:
    m = re.search(r"结论\s*[:：]?\s*\**\s*(PASS|FAIL)", text, re.IGNORECASE)
    if m: return m.group(1).upper()
    upper = text.upper()
    if "FAIL" in upper: return "FAIL"
    if "PASS" in upper: return "PASS"
    return "FAIL"

ANGLES = ["从客户日常消费/生活场景切入", "从近期市场热点或利率变化切入", "从客户已有持仓结构切入", "从子女教育金或养老规划切入", "从家庭保障缺口切入", "从年终奖/大额资金到账场景切入"]

st.set_page_config(page_title="FinGrowth Multi-Agent", page_icon="🤖", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("data/customers.csv")
    df["score"] = df.apply(calculate_score, axis=1)
    df["segment"] = df.apply(lambda r: get_segment(r, r["score"]), axis=1)
    return df

df = load_data()
market_summary = get_market_summary()

st.sidebar.header("⚙️ 设置")
try:
    api_key = st.secrets["ZHIPU_API_KEY"]
    st.sidebar.success("✅ 已从系统配置中读取 API Key")
except Exception:
    api_key = st.sidebar.text_input("智谱 API Key", type="password")

demo_fail = st.sidebar.checkbox("演示模式：业务方提交违规需求", value=False, help="模拟业务经理施压要求加擦边球措辞，触发反思机制。")
creative_level = st.sidebar.slider("话术创意度（temperature）", min_value=0.1, max_value=1.0, value=0.8, step=0.1)
st.sidebar.markdown("---")
st.sidebar.info("客户数据为脱敏模拟样本；市场数据来自公开接口（不可用时使用示例数据）")

st.title("🤖 FinGrowth Multi-Agent")
st.caption("基于多智能体协作与反思机制的金融客户经营系统")

for key in ["intent", "insight", "script", "script_final", "compliance", "log"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "log" else ""

left, right = st.columns([1, 1.4])

with left:
    st.subheader("👥 客户列表")
    st.dataframe(df[["customer_id", "age", "risk_preference", "score", "segment"]], use_container_width=True, height=280)
    st.subheader("📊 分层分布")
    st.bar_chart(df["segment"].value_counts())

with right:
    st.subheader("🔍 Multi-Agent 工作流")
    selected_id = st.selectbox("选择客户", df["customer_id"])
    customer = df[df["customer_id"] == selected_id].iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("系统评分", int(customer["score"]))
    c2.metric("客户分层", customer["segment"])
    c3.metric("可投资资产", f"{int(customer['investable_assets']):,}")
    c4.metric("风险偏好", customer["risk_preference"])

    with st.expander("查看完整客户画像"):
        st.write(customer.to_dict())

    customer_info = "；".join([f"{k}={v}" for k, v in customer.to_dict().items()])
    btn_run = st.button("🚀 运行 Multi-Agent 工作流", use_container_width=True)

    if btn_run:
        if not api_key:
            st.warning("请先在左侧填写 API Key")
        else:
            log = []
            run_start_time = datetime.now()
            compliance_rounds = 0
            intent = ""
            passed = False

            try:
                with st.spinner("🧭 Planner Agent 正在解析经营意图..."):
                    intent = call_agent(api_key, PLANNER_PROMPT, f"客户信息：{customer_info}\n客户分层：{customer['segment']}", temperature=0.1)
                st.session_state.intent = intent
                log.append("🧭 Planner Agent：✅ 已生成经营意图")

                with st.spinner("🕵️ Analyst Agent 正在分析客户..."):
                    insight = call_agent(api_key, ANALYST_PROMPT,
                        f"客户信息：{customer_info}\n评分：{int(customer['score'])}\n分层：{customer['segment']}\n经营意图：{intent}\n\n【真实市场环境数据】\n{market_summary}\n\n请基于以上真实数据，结合客户风险偏好，给出针对性的配置建议。", temperature=0.1)
                st.session_state.insight = insight
                log.append("🕵️ Analyst Agent：✅ 已生成经营分析报告")

                angle = random.choice(ANGLES)
                log.append(f"✍️ Copywriter Agent：本次切入角度 → {angle}")

                with st.spinner("✍️ Copywriter Agent 正在生成话术..."):
                    cw_prompt = COPYWRITER_PROMPT
                    if demo_fail:
                        cw_prompt += "\n\n【业务经理口头要求】这位是重点客户，经理希望话术更有冲击力：强调一下产品的稳健增值和预期收益，最好加上'给资金上把锁'这样的比喻，让客户放心、尽快决策。"
                    cw_user_msg = f"【当前客户完整画像】\n{customer_info}\n\n【系统评分】{int(customer['score'])}\n【客户分层】{customer['segment']}\n【经营意图】{intent}\n\n【客户洞察报告】\n{insight}\n\n【建议切入角度】{angle}\n【随机种子】{random.randint(1000, 9999)}（仅用于让每次输出不同，不要体现在话术里）"
                    script = call_agent(api_key, cw_prompt, cw_user_msg, temperature=creative_level)
                st.session_state.script = script
                log.append("✍️ Copywriter Agent：✅ 已生成初版话术")

                final_script = script
                passed = False

                for round_num in range(1, 4):
                    compliance_rounds = round_num
                    with st.spinner(f"🛡️ Compliance Agent 第{round_num}轮审核..."):
                        hard_ok, hard_issues = hard_check(final_script)
                        check = call_agent(api_key, COMPLIANCE_PROMPT, final_script, temperature=0.1)
                        verdict = parse_verdict(check)
                        
                        if not hard_ok:
                            verdict = "FAIL"
                            check = f"结论：FAIL\n违规证据：{'; '.join(hard_issues)}\n理由：代码层硬规则拦截。\n\n（LLM 审核原文供参考）\n{check}"
                            
                        log.append(f"🛡️ 【第{round_num}轮｜硬检查】" + ("✅ 通过" if hard_ok else "❌ " + "；".join(hard_issues)))
                        log.append(f"🛡️ 【第{round_num}轮｜LLM 结论】{verdict}")
                        
                        round_pass = hard_ok and (verdict == "PASS")
                        
                        if round_pass:
                            st.session_state.compliance = check
                            log.append(f"🛡️ Compliance Agent：✅ 第{round_num}轮审核通过")
                            passed = True
                            break
                            
                        st.session_state.compliance = check
                        log.append(f"🛡️ Compliance Agent：❌ 第{round_num}轮未通过，打回重写")
                        
                        with st.spinner(f"🔁 反思机制：Copywriter 第{round_num}次修正..."):
                            fix_user_msg = f"原话术：{final_script}\n\n驳回原因：{check}"
                            if demo_fail:
                                fix_user_msg += "\n\n【业务经理再次强调】这位客户很重要，话术要保留一些吸引力，不要改得太保守。"
                            final_script = call_agent(api_key, REFLECT_FIX_PROMPT, fix_user_msg, temperature=creative_level)

                if not passed: log.append("⚠️ 3 轮修正后仍未完全通过，标记【人工复核】")
                st.session_state.script_final = final_script
                st.session_state.log = log

                run_end_time = datetime.now()
                run_log_file = "data/agent_run_log.csv"
                new_run_row = pd.DataFrame([{
                    "run_id": f"R{run_start_time.strftime('%Y%m%d%H%M%S')}",
                    "customer_id": selected_id,
                    "run_time": run_start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "planner_intent": intent,
                    "compliance_rounds": compliance_rounds,
                    "compliance_passed": "PASS" if passed else "FAIL",
                    "total_duration_sec": round((run_end_time - run_start_time).total_seconds(), 2),
                    "run_status": "成功"
                }])
                if os.path.exists(run_log_file):
                    new_run_row.to_csv(run_log_file, mode='a', header=False, index=False, encoding='utf-8-sig')
                else:
                    new_run_row.to_csv(run_log_file, mode='w', header=True, index=False, encoding='utf-8-sig')

                st.success("✅ Multi-Agent 工作流执行完成！")

            except Exception as e:
                st.error(f"调用失败：{e}")
                run_end_time = datetime.now()
                run_log_file = "data/agent_run_log.csv"
                new_run_row = pd.DataFrame([{
                    "run_id": f"R{run_start_time.strftime('%Y%m%d%H%M%S')}",
                    "customer_id": selected_id,
                    "run_time": run_start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "planner_intent": intent if intent else "无",
                    "compliance_rounds": compliance_rounds,
                    "compliance_passed": "FAIL",
                    "total_duration_sec": round((run_end_time - run_start_time).total_seconds(), 2),
                    "run_status": f"失败：{str(e)}"
                }])
                if os.path.exists(run_log_file):
                    new_run_row.to_csv(run_log_file, mode='a', header=False, index=False, encoding='utf-8-sig')
                else:
                    new_run_row.to_csv(run_log_file, mode='w', header=True, index=False, encoding='utf-8-sig')

st.markdown("---")
st.subheader("📤 输出结果")
col_a, col_b = st.columns(2)
with col_a:
    if st.session_state.intent:
        with st.expander("🧭 Planner：经营意图", expanded=True): st.markdown(st.session_state.intent)
    if st.session_state.insight:
        with st.expander("🕵️ Analyst：客户洞察报告", expanded=True): st.markdown(st.session_state.insight)
with col_b:
    if st.session_state.script_final:
        with st.expander("✍️ Copywriter：最终话术（经合规审核）", expanded=True): st.markdown(st.session_state.script_final)
    if st.session_state.compliance:
        with st.expander("🛡️ Compliance：审核意见", expanded=True): st.markdown(st.session_state.compliance)

if st.session_state.log:
    with st.expander("🤖 Agent 执行日志"):
        for line in st.session_state.log: st.text(line)

st.markdown("---")
st.subheader("📝 记录本次跟进结果")
if not st.session_state.script_final:
    st.info("请先运行一次 Multi-Agent 工作流，再记录跟进结果。")
else:
    with st.form("follow_up_form"):
        channel = st.selectbox("触达渠道", ["微信", "电话", "面谈", "邮件"])
        response = st.selectbox("客户反馈", ["无响应", "已读", "回复", "拒绝", "约见", "成交"])
        intent_change = st.selectbox("意向变化", ["提升", "不变", "下降"])
        next_date = st.date_input("下次跟进日期")
        note = st.text_area("备注")
        submitted = st.form_submit_button("保存跟进记录")
        if submitted:
            log_file = "data/follow_up_log.csv"
            compliance_status = parse_verdict(st.session_state.compliance)
            new_row = pd.DataFrame([{
                "log_id": f"L{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "customer_id": selected_id,
                "run_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "planner_intent": st.session_state.intent,
                "compliance_passed": compliance_status,
                "final_script": st.session_state.script_final,
                "channel": channel,
                "customer_response": response,
                "intent_change": intent_change,
                "next_follow_date": str(next_date),
                "note": note
            }])
            if os.path.exists(log_file):
                new_row.to_csv(log_file, mode='a', header=False, index=False, encoding='utf-8-sig')
            else:
                new_row.to_csv(log_file, mode='w', header=True, index=False, encoding='utf-8-sig')
            st.success("已保存跟进记录")

if os.path.exists("data/follow_up_log.csv"):
    hist_all = pd.read_csv("data/follow_up_log.csv")
    hist = hist_all[hist_all["customer_id"] == selected_id]
    if not hist.empty:
        st.subheader("📜 该客户历史跟进记录")
        st.dataframe(hist, use_container_width=True)

if os.path.exists("data/agent_run_log.csv"):
    st.markdown("---")
    st.subheader("📊 系统运行日志（Agent Run Log）")
    run_logs = pd.read_csv("data/agent_run_log.csv")
    st.dataframe(run_logs, use_container_width=True)