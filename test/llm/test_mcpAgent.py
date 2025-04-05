import asyncio
from app.agent.MCPAgent import MCPAgent


async def main():
    """
    正常调用 MCPAgent，输出 Final Answer。
    """
    agent = MCPAgent()
    # result = await agent.run("帮我看一下上海的天气，世博园有什么好玩的")
    # print(f"Final Answer: {result}")

    async for step in agent.run("帮我看一下上海的天气，世博园有什么好玩的"):
        print("中间步骤：", step)


if __name__ == "__main__":
    asyncio.run(main())
