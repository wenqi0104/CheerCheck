import os
from dotenv import load_dotenv
import asyncio
from openai import AsyncOpenAI

# 加载 .env 文件
load_dotenv()

# 从环境变量获取 API 信息
api_key = os.getenv("TURING_API_KEY")
api_base = os.getenv("TURING_API_BASE")

# 初始化客户端
async_client = AsyncOpenAI(
    api_key=api_key,
    base_url=api_base
)

messages = [
    {"role": "system", "content": "你是一个友好的 AI 助手"}
]

# 发送测试请求
async def chat():
    while True:
        user_input = input("你: ").strip()
        if user_input.lower() in ["exit", "quit", "退出"]:
            print("👋 再见！")
            break

        # 添加用户消息
        messages.append({"role": "user", "content": user_input})

        try:
            # 发送请求
            response = await async_client.chat.completions.create(
                model="turing/gpt-5-chat",
                messages=messages
            )
            reply = response.choices[0].message.content
            print("AI:", reply)

            # 保存 AI 回复到历史
            messages.append({"role": "assistant", "content": reply})

        except Exception as e:
            print("❌ 出错:", str(e))

if __name__ == "__main__":
    asyncio.run(chat())