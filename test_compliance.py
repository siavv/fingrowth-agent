from llm_client import call_agent
from prompts import COMPLIANCE_PROMPT

api_key = "b5654796301e46918b45225ee57e9187.ov2CWT1iDNSmzV7b"   # 填进去

# 故意放一段有违规点的话术
fake_script = """
## 微信首次触达
王先生您好，这款产品稳赚不赔，年化收益稳定在5%以上，很多客户都抢着买，您也赶紧入手吧！

## 电话开场白
您好，我是XX保险的客户经理，给您推荐一款保证收益的产品。

## 三天后跟进
这款产品真的很划算，放心买，绝对没问题。
"""

result = call_agent(api_key, COMPLIANCE_PROMPT, fake_script)
print("======== 合规返回 ========")
print(result)
print("==========================")