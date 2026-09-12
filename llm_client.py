from openai import OpenAI

BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
MODEL = "glm-4-flash"  # 会自动路由到最新的 GLM-4.7-Flash

def call_agent(api_key, agent_prompt, user_message, temperature=0.3):
    client = OpenAI(api_key=api_key, base_url=BASE_URL)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": agent_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=temperature,
        max_tokens=1500
    )
    return response.choices[0].message.content