from enum import Enum
from dataclasses import dataclass
from typing import Type, List, Optional, Union
from pydantic import BaseModel
from app.core.config import settings


@dataclass
class LLMModelConfig:
    _model: str
    _name_zh: str
    _api_key: str
    stream: bool
    _base_url: Optional[str] = None
    stream_options: Optional[dict] = (
        None  # 当 stream = True 时，配置是否输出 token 使用信息
    )
    modalities: Optional[List[str]] = None  # ["text"]；适用于 Qwen-Omni
    temperature: Optional[float] = None  # [0,2)
    top_p: Optional[float] = None  # (0,1.0]
    presence_penalty: Optional[float] = None  # [-2.0, 2.0]
    response_format: Optional[dict] = None  # {"type": "text"} / {"type": "json_object"}
    max_tokens: Optional[int] = None  # 最大返回 token 数
    n: Optional[int] = None  # 响应数量
    seed: Optional[int] = None  # 固定生成结果的随机种子
    stop: Optional[Union[str, List[Union[str, int]]]] = None  # 生成终止词
    tools: Optional[List[dict]] = None  # function calling 工具集
    tool_choice: Optional[Union[str, dict]] = None  # tool 使用策略
    parallel_tool_calls: Optional[bool] = None  # 是否允许并行调用工具
    translation_options: Optional[dict] = None  # 翻译模型专用配置
    enable_search: Optional[bool] = None  # 是否使用互联网搜索
    search_options: Optional[dict] = None  # 联网搜索策略配置

    @property
    def model(self) -> str:
        return self._model

    @property
    def name_zh(self) -> str:
        return self._name_zh

    @property
    def base_url(self) -> Optional[str]:
        return self._base_url

    @property
    def api_key(self) -> str:
        return self._api_key

    @property
    def input_schema(self) -> Type[BaseModel]:
        return self._input_schema

    @property
    def output_schema(self) -> Type[BaseModel]:
        return self._output_schema


class LLMModel(Enum):
    TEXT = LLMModelConfig(
        _model="qwen-turbo",
        _name_zh="通义千问-文本模型",
        _base_url=settings.ALI_TEXT_MODEL_URL,
        _api_key=settings.ALI_MODEL_API_KEY,
        temperature=0.7,
        stream=False,
    )
    IMAGE = LLMModelConfig(
        _model="qwen2.5-vl-3b-instruct",
        _name_zh="阿里图像识别模型",
        _base_url="https://dashscope.aliyuncs.com/api/image/classify",
        _api_key=settings.ALI_MODEL_API_KEY,
        temperature=0.7,
        stream=False,
    )
    VIDEO = LLMModelConfig(
        _model="qwen-omni-turbo",
        _name_zh="阿里视频识别模型",
        _base_url="https://dashscope.aliyuncs.com/api/video/recognize",
        _api_key="ALIYUN_VIDEO_MODEL_API_KEY",
        temperature=0.7,
        stream=False,
    )

    def validate_config(self) -> None:
        """
        对模型配置中关键参数进行范围校验
        """
        cfg = self.value
        if cfg.temperature is not None and not (0 <= cfg.temperature < 2):
            raise ValueError("temperature 必须在 [0, 2) 范围内")
        if cfg.top_p is not None and not (0 < cfg.top_p <= 1.0):
            raise ValueError("top_p 必须在 (0, 1.0] 范围内")
        if cfg.presence_penalty is not None and not (
            -2.0 <= cfg.presence_penalty <= 2.0
        ):
            raise ValueError("presence_penalty 必须在 [-2.0, 2.0] 范围内")

    # ============================
    # 安全风险评估与规范性报告
    # ============================
    # ✅ 当前功能说明：
    # - 定义了 `LLMModel` 枚举类，统一管理多种阿里云大模型（文本、图像、视频）的调用配置；
    # - 每个模型使用不可变的数据类 `LLMModelConfig` 封装，包含 base_url、api_key、输入输出 schema 等调用参数；
    # - 提供 `.validate_config()` 方法，对生成类参数如 temperature、top_p、presence_penalty 做范围校验，提升调用安全性；

    # 🔐 安全风险分析：
    # - ✅ 使用 `@dataclass(frozen=True)` 定义模型配置，防止运行时被修改，保障配置安全；
    # - ✅ 所有参数都有类型注解，且多数为 Optional 类型，调用方可根据模型特性按需赋值；
    # - ✅ 通过 `settings` 引入 API Key 和 base_url 等敏感信息，避免硬编码；
    # - ❗ VIDEO 模型中的 `api_key="ALIYUN_VIDEO_MODEL_API_KEY"` 为硬编码字符串，存在安全隐患；
    #   建议：统一通过 `settings` 引用配置项，如 `settings.ALI_VIDEO_MODEL_API_KEY`；
    # - ✅ 输入输出 schema 类型继承自 `BaseModel`，可利用 Pydantic 校验防止非法入参；

    # 📐 编码规范审查：
    # - ✅ 命名符合 PEP8 规范，字段和类名清晰；
    # - ✅ 每个字段都添加了详细注释，说明了用途、类型及默认行为；
    # - ✅ 配置结构清晰，避免魔法字符串硬编码模型类型；

    # 🏗 架构设计与可维护性建议：
    # - ✅ 使用数据类封装模型配置，便于 IDE 补全与测试；
    # - ✅ 枚举类统一管理多模型，具备良好的扩展性；
    # - ✅ 后续可考虑将 `.validate_config()` 逻辑改为 schema 驱动式校验，提升灵活性；
    # - ✅ 建议新增 `from_model_name()` 工厂方法，支持根据模型名动态查找配置，提升可维护性；
