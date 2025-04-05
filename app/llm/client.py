from typing import Iterable, List, Optional
from openai import AsyncOpenAI
from app.llm.enums import LLMModel
from app.llm.base import LLMBaseClient
from app.llm.exceptions import LLMInvokeError
from openai.types.chat import (
    ChatCompletionToolParam,
    ChatCompletion,
    ChatCompletionMessageParam,
)


class LLMClient(LLMBaseClient):
    async def call(
        self,
        model: LLMModel,
        messages: Iterable[ChatCompletionMessageParam],
        tools: Optional[List[ChatCompletionToolParam]] = None,
    ) -> ChatCompletion:
        # 获取模型配置
        config = model.value

        # 校验模型配置参数（温度、top_p 等）
        model.validate_config()

        # 初始化 OpenAI 客户端（可根据 base_url 设定自定义 API 入口）
        client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
        )

        try:
            response = await client.chat.completions.create(
                model=config.model,
                messages=messages,
                temperature=config.temperature,
                stream=config.stream,
                tools=tools,
            )
        except Exception as e:
            raise LLMInvokeError(f"模型调用异常：{str(e)}")

        try:
            # ChatCompletion
            return response
        except Exception as e:
            raise LLMInvokeError(f"响应解析失败：{str(e)}")


# ============================
# 安全风险评估与规范性报告
# ============================
# ✅ 当前功能说明：
# - `LLMClient` 封装对 OpenAI ChatCompletion 接口的异步调用逻辑，支持指定模型、上下文消息、工具参数等。
#
# 🔐 安全风险分析：
# - ⚠️ 未设置调用超时：若 LLM 响应时间异常长，可能导致接口卡顿或阻塞。
#   建议：在 client 或 create 调用中添加超时控制。
# - ⚠️ 返回的 `response` 未做结构校验，若 OpenAI 接口发生非预期变更或返回错误结构，可能导致异常。
#   建议：增加 response 类型与结构验证。
#
# 📐 编码规范审查：
# - 命名规范：✅ 合理使用驼峰式命名与 PEP8 命名风格
# - 类型注解：✅ 所有参数与返回值已提供类型注解
# - 注释完整性：✅ 函数与关键逻辑处有明确注释
# - 异常处理：✅ 使用了统一封装的异常 `LLMInvokeError`，提升了可控性
#
# 🏗 架构设计与可维护性建议：
# - ✅ 客户端与枚举、配置、异常解耦良好；
# - ✅ 使用 AsyncOpenAI 支持异步非阻塞调用；
# - ✅ 工具参数支持良好，便于与 Function Calling 等机制集成；
# - 🔧 可考虑将客户端初始化提取至构造函数中，仅初始化一次，提升性能；
# - 🔧 后续可支持更丰富的请求配置项，如 stop、max_tokens、tool_choice 等，以增强灵活性。
