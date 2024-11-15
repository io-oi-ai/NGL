import asyncio
from local_ai_client import AIClient
from config import CLAUDE_API_KEY

async def test_ai():
    # 创建 AI 客户端
    client = AIClient(api_key=CLAUDE_API_KEY)
    
    # 测试问题列表
    test_prompts = [
        "你好，请介绍一下你自己",
        "比特币是什么？",
        "以太坊和比特币有什么区别？",
        "什么是 DeFi？"
    ]
    
    # 测试每个问题
    for prompt in test_prompts:
        print(f"\n用户: {prompt}")
        try:
            response = await client.get_ai_response(prompt)
            print(f"AI: {response}")
        except Exception as e:
            print(f"错误: {e}")
        await asyncio.sleep(1)  # 添加延迟避免请求过快

if __name__ == "__main__":
    asyncio.run(test_ai()) 