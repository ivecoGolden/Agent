from mcp import ClientSession, ListToolsResult
from mcp.client.sse import sse_client
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager
from openai.types.chat import ChatCompletionToolParam
from app.utils.tools import convert_tools_to_openai_params


class GaoDeMCPClient:
    """
    GaoDeMCPClient 类用于封装与高德 MCP 的 SSE 长连接过程，提供工具列表获取与工具调用功能。
    通过该类，用户可以方便地与高德的服务进行交互，获取所需的工具并使用它们。
    """

    def __init__(self, api_key: str):
        """
        初始化 GaoDeMCPClient 实例。

        :param api_key: 用于连接高德 MCP 服务的 API 密钥
        """
        self.api_key = api_key
        self.session: Optional[ClientSession] = None  # 存储当前的客户端会话
        self._tools: List[ChatCompletionToolParam] = []  # 缓存工具列表

    @asynccontextmanager
    async def connect(self):
        """
        异步上下文管理器：自动连接 SSE 并初始化 session。
        该方法确保在使用完毕后自动关闭连接，管理连接的生命周期。

        使用示例：
        async with GaoDeMCPClient(api_key).connect() as client:
            # 在此处使用 client 进行操作
        """
        async with sse_client(url=f"https://mcp.amap.com/sse?key={self.api_key}") as (
            read,
            write,
        ):
            async with ClientSession(read, write) as session:
                self.session = session  # 初始化会话
                await self.session.initialize()  # 进行必要的初始化操作
                yield self  # 暴露当前实例以供使用
                self.session = None  # 清理会话

    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        获取工具列表，并转换为模型可识别的格式。

        此方法首先检查当前会话是否有效，若有效则请求工具列表，并将原始工具转换为适合 OpenAI 模型的格式。
        工具列表会被缓存，以避免重复请求。

        :return: 转换后的工具列表
        :raises RuntimeError: 如果当前会话无效
        """
        if not self.session:
            raise RuntimeError("请先在 connect() 中使用 MCPClient")

        raw_tools: ListToolsResult = await self.session.list_tools()  # 请求工具列表
        self._tools = convert_tools_to_openai_params(raw_tools.tools)  # 转换工具格式
        return self._tools  # 返回转换后的工具列表

    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """
        调用指定工具。

        在调用工具之前，首先校验工具名称是否在已注册的工具列表中。如果工具名称不合法，抛出异常。
        然后，调用对应的工具并传递参数。

        :param tool_name: 要调用的工具名称
        :param params: 传递给工具的参数
        :return: 工具调用的返回结果
        :raises RuntimeError: 如果当前会话无效
        :raises ValueError: 如果工具名称不在已注册的工具列表中
        """
        if not self.session:
            raise RuntimeError("请先在 connect() 中使用 MCPClient")

        if not self._tools:
            await self.list_tools()  # 如果工具列表为空，则获取工具列表

        # 校验工具名称是否在已注册的工具列表中
        if tool_name not in [tool["name"] for tool in self._tools]:
            raise ValueError(f"工具 '{tool_name}' 未注册或不可用")

        return await self.session.call_tool(tool_name, params)  # 调用工具并返回结果


# ============================
# 安全风险评估与规范性报告
# ============================
# ✅ 当前功能说明：
# - `GaoDeMCPClient` 封装与高德 MCP 的 SSE 长连接过程，支持工具列表获取与工具调用功能。
#
# 🔐 安全风险分析：
# - ⚠️ 未校验 `tool_name` 是否在 `_tools` 中存在：若模型生成错误工具名将导致调用失败或异常。
#   建议：调用前校验 `tool_name` 是否为合法注册工具。
# - ⚠️ 所有 `params` 直接透传至远端，若未做校验，可能引发调用失败或数据异常。
#   建议：增加参数结构验证机制。
#
# 📐 编码规范审查：
# - 命名规范：✅ 命名清晰，遵循 PEP8 规范
# - 类型注解：✅ 所有函数参数及返回值都有明确类型注解
# - 注释完整性：✅ 每个方法均有 docstring，描述其用途与行为
# - 结构清晰：✅ 使用上下文管理器封装连接逻辑，职责清晰
#
# 🏗 架构设计与可维护性建议：
# - ✅ `connect` 方法采用 async context manager 封装，保障连接生命周期管理；
# - ✅ 工具列表缓存于 `_tools`，避免重复请求；
# - 🔧 建议工具支持热更新机制（如 TTL 缓存、定时刷新等）以适配动态变化场景；
# - ✅ 使用 `convert_tools_to_openai_params` 实现工具格式标准化，便于与 LLM 对接。
