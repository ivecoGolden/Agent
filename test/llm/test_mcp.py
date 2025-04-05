import asyncio
from app.core.config import settings
from app.mcp.gaode_mcp import GaoDeMCPClient

if __name__ == "__main__":

    async def run():
        api_key = settings.GAODE_KEY
        client = GaoDeMCPClient(api_key)

        async with client.connect():
            tools = await client.list_tools()
            print("可用工具列表：", tools)

            # result = await client.call_tool("maps_weather", {"city": "上海"})
            # print("天气查询结果：", result)

    asyncio.run(run())
