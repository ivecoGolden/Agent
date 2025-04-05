from abc import ABC, abstractmethod
from typing import Iterable, List, Optional
from pydantic import BaseModel
from openai.types.chat import ChatCompletionToolParam, ChatCompletionMessageParam


class LLMBaseClient(ABC):
    @abstractmethod
    async def call(
        self,
        messages: Iterable[ChatCompletionMessageParam],
        tools: Optional[List[ChatCompletionToolParam]] = None,
    ) -> BaseModel:
        pass
