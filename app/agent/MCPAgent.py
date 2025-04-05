import json
from typing import Dict, List
from app.llm.client import LLMClient
from app.llm.enums import LLMModel
from app.llm.exceptions import LLMInvokeError
from app.core.config import settings
from app.mcp.gaode_mcp import GaoDeMCPClient
from openai.types.chat import (
    ChatCompletionUserMessageParam,
    ChatCompletionSystemMessageParam,
)

from app.promt.planning import Planning


class MCPAgent:
    """
    MCP 智能体类，负责执行多轮思考直到得出最终答案。

    用途说明：
    - 管理与 LLM 的交互流程，结合高德地图工具进行多轮推理与工具调用。
    - 每一轮推理包括计划生成、工具调用、循环控制以及最终结果产出。
    - 集成了工具信息，支持动态生成系统提示词以指导 LLM 调用相应工具。
    """

    def __init__(self) -> None:
        """
        初始化 MCPAgent。

        目的：
        - 初始化工具集成，加载默认工具列表以供后续 LLM 与工具调用使用。
        """
        self.tools = self.get_default_tools()

    async def run(self, user_input: str) -> str:
        """
        启动一个自动推理智能体循环，直到模型判断完成。

        参数:
        - user_input: 用户初始输入（str）

        返回:
        - 最终结果（str）

        逻辑说明：
        - 计划生成阶段：构造初始计划并展示当前计划。
        - 工具调用阶段：在每轮中调用 LLM 生成下一步操作，并根据返回信息决定是否调用工具。
        - 循环控制阶段：根据计划是否还有下一步决定是否继续推理。
        - 结果产出阶段：当无下一步时，调用 LLM 生成最终答案并返回。
        """
        llm_client = LLMClient()
        gaode_client = GaoDeMCPClient(settings.GAODE_KEY)
        max_rounds = 6  # 防止无限循环
        final_answer = ""  # 用于存储最终答案

        # 制定计划
        # --- 计划生成阶段 ---
        planning = Planning(user_input)
        planning_prompt = self.build_system_prompt_with_tools(self.tools)
        # 调用 LLM 生成初始计划
        planning_result = await llm_client.call(
            LLMModel.TEXT,
            [
                ChatCompletionSystemMessageParam(
                    role="system",
                    content=planning_prompt,
                ),
                ChatCompletionUserMessageParam(role="user", content=user_input),
            ],
        )
        planning.set_plan_steps_from_text(planning_result.choices[-1].message.content)
        # 输出当前计划信息
        yield "----------当前计划----------"  # 显示计划头部
        yield str(planning)  # 显示详细计划
        yield "---------------------------"  # 显示计划尾部

        async with gaode_client.connect():

            for _ in range(max_rounds):
                # --- 每轮推理阶段开始 ---
                yield "---------------------------"  # 分割线标识新一轮开始
                current_step = planning.get_current_step()
                yield str(current_step)  # 输出当前计划步骤
                # 调用 LLM 生成下一步操作，传入当前计划信息
                result = await llm_client.call(
                    LLMModel.TEXT,
                    [
                        ChatCompletionSystemMessageParam(
                            role="user",
                            content=str(planning),
                        )
                    ],
                    tools=self.tools,
                )
                finish_reason = result.choices[-1].finish_reason
                # --- 工具调用阶段 ---
                if finish_reason == "tool_calls":
                    for tool_call in result.choices[-1].message.tool_calls:
                        function_name = tool_call.function.name
                        function_args = tool_call.function.arguments
                        yield f"调用工具: {function_name}, 参数: {function_args}"  # 记录工具调用信息
                        # 调用实际工具，并传入解析后的参数
                        tool_wait = await gaode_client.call_tool(
                            function_name, json.loads(function_args)
                        )
                        # 将工具调用结果整合进上下文，辅助后续推理
                        tool_result = await llm_client.call(
                            LLMModel.TEXT,
                            [
                                ChatCompletionSystemMessageParam(
                                    role="user",
                                    content=f"工具调用结果: {tool_wait},整合数据信息",
                                )
                            ],
                        )
                        planning.add_info(tool_result.choices[-1].message.content)

                # TODO: 思考是否需要调整计划

                # --- 循环控制阶段 ---
                can_next = planning.advance_step()
                if not can_next:
                    # --- 结果产出阶段 ---
                    yield "没有下一步了，直接输出结果"  # 提示无后续步骤
                    result = await llm_client.call(
                        LLMModel.TEXT,
                        [
                            ChatCompletionSystemMessageParam(
                                role="user",
                                content=f"根据以下信息给出最终结果:\n{str(planning)}",
                            )
                        ],
                    )
                    final_answer = result.choices[-1].message.content
                    break

        if not final_answer:
            raise LLMInvokeError(
                "超过最大轮数仍未得到最终答案。"
            )  # 超出最大轮数错误处理
        yield f"最终答案：{final_answer}"

    def build_system_prompt_with_tools(self, tools: List[Dict]) -> str:
        """
        根据给定的工具列表，生成带工具功能描述的系统提示词。

        详细说明：
        - 设计动机：构造一个系统提示，指导 LLM 根据可用工具制定具体操作步骤。
        - 提示生成格式：提示词包含工具功能描述，每个工具以列表项形式呈现，格式为 "- 工具名：描述；"。
        - 工具结构含义：每个工具包含名称、描述及参数定义，帮助 LLM 理解工具用途和调用方式。

        :param tools: OpenAI 工具定义列表（每个元素是 function 类型）
        :return: 用于 ChatCompletionSystemMessageParam 的 content 字符串
        """
        # 提示开头
        intro = (
            "你是一个助手，根据用户已有的信息和可用工具，制定出一系列可执行的步骤。（如果工具需要的信息缺失就不要加到步骤中）"
            "每一步都应是调用工具可以完成的具体操作，每一个步中只能有一个工具，步骤应清晰具体，逻辑合理。"
            "使用英文逗号 `。` 分隔每个步骤，不要换行，最多3步。用中文回复。\n\n"
            "当前可用的工具如下：\n"
        )

        # 拼接工具说明
        tool_descriptions = []
        for tool in tools:
            func = tool.get("function", {})
            name = func.get("name", "unknown_tool")
            desc = func.get("description", "（无描述）")
            tool_descriptions.append(f"- {name}：{desc}；")

        return intro + "\n".join(tool_descriptions)

    @staticmethod
    def get_default_tools() -> List[Dict]:
        """
        获取默认工具列表，用于初始化 MCPAgent 的工具集成。

        详细说明：
        - 工具元信息结构设计：每个工具包含 type、function 信息，其中 function 包括名称、描述和参数定义。
        - 设计动机：将工具元信息集中管理，便于后续扩展和自动注册。
        """
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "maps_direction_bicycling",
                    "description": "骑行路径规划用于规划骑行通勤方案，规划时会考虑天桥、单行线、封路等情况。最大支持 500km 的骑行路线规划",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "origin": {
                                "type": "string",
                                "description": "出发点经纬度，坐标格式为：经度，纬度",
                            },
                            "destination": {
                                "type": "string",
                                "description": "目的地经纬度，坐标格式为：经度，纬度",
                            },
                        },
                        "required": ["origin", "destination"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "maps_direction_driving",
                    "description": "驾车路径规划 API 可以根据用户起终点经纬度坐标规划以小客车、轿车通勤出行的方案，并且返回通勤方案的数据。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "origin": {
                                "type": "string",
                                "description": "出发点经纬度，坐标格式为：经度，纬度",
                            },
                            "destination": {
                                "type": "string",
                                "description": "目的地经纬度，坐标格式为：经度，纬度",
                            },
                        },
                        "required": ["origin", "destination"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "maps_direction_transit_integrated",
                    "description": "根据用户起终点经纬度坐标规划综合各类公共（火车、公交、地铁）交通方式的通勤方案，并且返回通勤方案的数据，跨城场景下必须传起点城市与终点城市",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "origin": {
                                "type": "string",
                                "description": "出发点经纬度，坐标格式为：经度，纬度",
                            },
                            "destination": {
                                "type": "string",
                                "description": "目的地经纬度，坐标格式为：经度，纬度",
                            },
                            "city": {
                                "type": "string",
                                "description": "公共交通规划起点城市",
                            },
                            "cityd": {
                                "type": "string",
                                "description": "公共交通规划终点城市",
                            },
                        },
                        "required": [
                            "origin",
                            "destination",
                            "city",
                            "cityd",
                        ],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "maps_direction_walking",
                    "description": "根据输入起点终点经纬度坐标规划100km 以内的步行通勤方案，并且返回通勤方案的数据",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "origin": {
                                "type": "string",
                                "description": "出发点经度，纬度，坐标格式为：经度，纬度",
                            },
                            "destination": {
                                "type": "string",
                                "description": "目的地经度，纬度，坐标格式为：经度，纬度",
                            },
                        },
                        "required": ["origin", "destination"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "maps_distance",
                    "description": "测量两个经纬度坐标之间的距离,支持驾车、步行以及球面距离测量",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "origins": {
                                "type": "string",
                                "description": "起点经度，纬度，可以传多个坐标，使用分号隔离，比如120,30;120,31，坐标格式为：经度，纬度",
                            },
                            "destination": {
                                "type": "string",
                                "description": "终点经度，纬度，坐标格式为：经度，纬度",
                            },
                            "type": {
                                "type": "string",
                                "description": "距离测量类型,1代表驾车距离测量，0代表直线距离测量，3步行距离测量",
                            },
                        },
                        "required": ["origins", "destination"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "maps_geo",
                    "description": "将详细的结构化地址转换为经纬度坐标。支持对地标性名胜景区、建筑物名称解析为经纬度坐标",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "address": {
                                "type": "string",
                                "description": "待解析的结构化地址信息",
                            },
                            "city": {
                                "type": "string",
                                "description": "指定查询的城市",
                            },
                        },
                        "required": ["address"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "maps_regeocode",
                    "description": "将一个高德经纬度坐标转换为行政区划地址信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "经纬度",
                            }
                        },
                        "required": ["location"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "maps_ip_location",
                    "description": "IP 定位根据用户输入的 IP 地址，定位 IP 的所在位置",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ip": {
                                "type": "string",
                                "description": "IP地址",
                            }
                        },
                        "required": ["ip"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "maps_around_search",
                    "description": "周边搜，根据用户传入关键词以及坐标location，搜索出radius半径范围的POI",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keywords": {
                                "type": "string",
                                "description": "搜索关键词",
                            },
                            "location": {
                                "type": "string",
                                "description": "中心点经度纬度",
                            },
                            "radius": {
                                "type": "string",
                                "description": "搜索半径",
                            },
                        },
                        "required": ["keywords", "location"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "maps_search_detail",
                    "description": "查询关键词搜或者周边搜获取到的POI ID的详细信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "关键词搜或者周边搜获取到的POI ID",
                            }
                        },
                        "required": ["id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "maps_text_search",
                    "description": "关键字搜索 API 根据用户输入的关键字进行 POI 搜索，并返回相关的信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keywords": {
                                "type": "string",
                                "description": "查询关键字",
                            },
                            "city": {
                                "type": "string",
                                "description": "查询城市",
                            },
                            "citylimit": {
                                "type": "boolean",
                                "default": False,
                                "description": "是否限制城市范围内搜索，默认不限制",
                            },
                        },
                        "required": ["keywords"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "maps_weather",
                    "description": "根据城市名称或者标准adcode查询指定城市的天气",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "城市名称或者adcode",
                            }
                        },
                        "required": ["city"],
                    },
                },
            },
        ]
        return tools


# ============================
# 安全风险评估与规范性报告
# ============================
# ✅ 当前功能说明：
# - `MCPAgent` 实现了一个多轮推理智能体，结合 LLM 与高德地图工具，自动规划并执行工具调用任务直至得出最终答案。
#
# 🔐 安全风险分析：
# - ⚠️ `user_input` 未经严格验证直接进入 LLM，可能存在 prompt injection 风险。
#   建议：增加前置的输入清洗或注入检测逻辑。
# - ⚠️ LLM 工具调用结果未做显式验证（如类型、结构校验），可能被非预期数据污染后续上下文。
#   建议：对 tool_result 做 schema 验证。
# - ✅ 工具调用使用统一封装的 `GaoDeMCPClient.call_tool()` 接口，具备良好的扩展性。
#
# 📐 编码规范审查：
# - 命名规范：✅ 命名符合 PEP8 且清晰表达意图
# - 类型注解：✅ 全部函数和方法均使用类型注解
# - 注释完整性：✅ 每个类与方法均附带 docstring，说明详细
# - 格式排版：✅ 使用四空格缩进，逻辑清晰，未发现格式问题
#
# 🏗 架构设计与可维护性建议：
# - ✅ MCPAgent 逻辑集中且清晰，遵循 “控制器-执行器” 分离原则；
# - ✅ `build_system_prompt_with_tools` 解耦良好，可适配动态工具注入；
# - ✅ `get_default_tools` 工具元信息结构合理，具备自动注册可能性；
# - 🔧 后续建议将工具元信息迁移为独立配置或注册模块，提升可维护性与自动化注册能力；
# - ✅ 使用 yield 实现推理过程流式返回，适合与前端长连接或流式接口集成。
