"""对话历史管理"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid

from rag.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """消息"""

    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Conversation:
    """对话"""

    id: str
    messages: list[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class ConversationMemory:
    """对话历史管理器"""

    def __init__(self, max_history: Optional[int] = None):
        self.max_history = max_history or settings.max_history
        self.conversations: dict[str, Conversation] = {}
        logger.info(f"ConversationMemory initialized with max_history: {self.max_history}")

    def create_conversation(self) -> str:
        """创建新对话"""
        conv_id = str(uuid.uuid4())
        self.conversations[conv_id] = Conversation(id=conv_id)
        logger.debug(f"Created new conversation: {conv_id}")
        return conv_id

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
    ) -> None:
        """添加消息到对话"""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = Conversation(id=conversation_id)
            logger.debug(f"Created new conversation for message: {conversation_id}")

        conv = self.conversations[conversation_id]
        conv.messages.append(
            Message(role=role, content=content)
        )
        conv.updated_at = datetime.now()

        logger.debug(f"Added {role} message to conversation {conversation_id}")

        # 限制历史长度
        self._trim_history(conversation_id)

    def add_exchange(
        self,
        conversation_id: str,
        question: str,
        answer: str,
    ) -> None:
        """添加一轮对话"""
        self.add_message(conversation_id, "user", question)
        self.add_message(conversation_id, "assistant", answer)
        logger.debug(f"Added exchange to conversation {conversation_id}")

    def get_history(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
    ) -> list[dict]:
        """
        获取对话历史

        Returns:
            格式化为 [{"question": ..., "answer": ...}, ...]
        """
        if conversation_id not in self.conversations:
            logger.debug(f"Conversation not found: {conversation_id}")
            return []

        conv = self.conversations[conversation_id]
        messages = conv.messages

        limit = limit or self.max_history
        if limit:
            messages = messages[-(limit * 2) :]  # 问答成对

        # 转换为问答格式
        history = []
        for i in range(0, len(messages) - 1, 2):
            if messages[i].role == "user" and messages[i + 1].role == "assistant":
                history.append(
                    {
                        "question": messages[i].content,
                        "answer": messages[i + 1].content,
                    }
                )

        logger.debug(f"Retrieved {len(history)} history items for conversation {conversation_id}")
        return history

    def get_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
    ) -> list[dict]:
        """
        获取原始消息列表

        Returns:
            格式化为 [{"role": ..., "content": ...}, ...]
        """
        if conversation_id not in self.conversations:
            logger.debug(f"Conversation not found: {conversation_id}")
            return []

        conv = self.conversations[conversation_id]
        messages = conv.messages

        limit = limit or self.max_history
        if limit:
            messages = messages[-(limit * 2) :]

        return [{"role": m.role, "content": m.content} for m in messages]

    def clear_history(self, conversation_id: str) -> None:
        """清空对话历史"""
        if conversation_id in self.conversations:
            self.conversations[conversation_id].messages = []
            self.conversations[conversation_id].updated_at = datetime.now()
            logger.debug(f"Cleared history for conversation {conversation_id}")

    def delete_conversation(self, conversation_id: str) -> bool:
        """删除对话"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            logger.debug(f"Deleted conversation {conversation_id}")
            return True
        return False

    def _trim_history(self, conversation_id: str) -> None:
        """裁剪历史记录"""
        conv = self.conversations[conversation_id]
        max_messages = self.max_history * 2

        if len(conv.messages) > max_messages:
            conv.messages = conv.messages[-max_messages:]
            logger.debug(f"Trimmed history for conversation {conversation_id} to {max_messages} messages")
