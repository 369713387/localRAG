"""GLM LLM客户端"""
import logging
from typing import Optional

from tenacity import retry, stop_after_attempt, wait_exponential
from zhipuai import ZhipuAI

from rag.core.config import settings
from rag.core.exceptions import LLMError

logger = logging.getLogger(__name__)


class GLMClient:
    """GLM模型客户端"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        self.api_key = api_key or settings.zhipu_api_key
        self.model = model or settings.zhipu_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = ZhipuAI(api_key=self.api_key)
        logger.info(f"GLMClient initialized with model: {self.model}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        生成回复

        Args:
            prompt: 输入提示词
            temperature: 生成温度
            max_tokens: 最大token数

        Returns:
            生成的文本
        """
        try:
            logger.debug(f"Generating response for prompt (length: {len(prompt)})")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
            )

            result = response.choices[0].message.content
            logger.debug(f"Generated response (length: {len(result) if result else 0})")
            return result

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise LLMError(f"LLM生成失败: {e}", cause=e)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def chat(
        self,
        messages: list[dict],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        多轮对话

        Args:
            messages: 消息列表
            temperature: 生成温度
            max_tokens: 最大token数

        Returns:
            生成的文本
        """
        try:
            logger.debug(f"Chat with {len(messages)} messages")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
            )

            result = response.choices[0].message.content
            logger.debug(f"Chat response (length: {len(result) if result else 0})")
            return result

        except Exception as e:
            logger.error(f"LLM chat failed: {e}")
            raise LLMError(f"LLM对话失败: {e}", cause=e)
