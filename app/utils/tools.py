from typing import List
from mcp import Tool
from openai.types.chat import ChatCompletionToolParam


def convert_tool_to_openai_param(tool: Tool) -> ChatCompletionToolParam:
    """
    将 Tool 实例转换为 OpenAI Function Calling 所需的 ChatCompletionToolParam 结构

    :param tool: Tool 实例（必须包含 name、description、inputSchema）
    :return: ChatCompletionToolParam 结构体（字典格式）
    """
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.inputSchema,
        },
    }


def convert_tools_to_openai_params(tools: List[Tool]) -> List[ChatCompletionToolParam]:
    """
    批量转换 Tool 列表为 ChatCompletionToolParam 列表

    :param tools: Tool 实例列表
    :return: 可直接传入 openai.ChatCompletion.create(..., tools=...) 的参数结构
    """
    return [convert_tool_to_openai_param(tool) for tool in tools]
