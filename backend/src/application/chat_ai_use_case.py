"""Chat with AI use case: sends user message + CV context to Gemini, persists conversation."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from ..domain.entities import ChatMessage
from ..domain.repositories import ChatRepository, CVRepository

log = logging.getLogger(__name__)


@dataclass
class ChatAIResult:
    response: str
    patches: list[dict]


class ChatWithAI:
    def __init__(
        self,
        chat_repo: ChatRepository,
        cv_repo: CVRepository,
        gemini_client,
    ) -> None:
        self._chat_repo = chat_repo
        self._cv_repo = cv_repo
        self._llm = gemini_client

    def execute(self, user_id: str, cv_id: str, message: str) -> ChatAIResult:
        # 1. Load CV context
        cv = self._cv_repo.get(cv_id, user_id)
        cv_text = cv.context_json or "{}"

        # 2. Load chat history for context
        history_msgs = self._chat_repo.get_messages(cv_id, user_id)
        history = []
        for msg in history_msgs:
            role = "user" if msg.role == "user" else "model"
            history.append({"role": role, "parts": [msg.content]})

        # 3. Call Gemini
        result = self._llm.chat(message, cv_text, history)

        # 4. Persist user message
        user_msg = ChatMessage(role="user", content=message)
        self._chat_repo.append(cv_id, user_id, user_msg)

        # 5. Persist AI response
        ai_msg = ChatMessage(role="assistant", content=result.response)
        self._chat_repo.append(cv_id, user_id, ai_msg)

        return ChatAIResult(response=result.response, patches=result.patches)
