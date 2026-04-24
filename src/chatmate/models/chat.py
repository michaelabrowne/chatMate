from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from uuid import uuid4


@dataclass(slots=True)
class ChatMessage:
    role: str
    content: str
    message_id: str = field(default_factory=lambda: uuid4().hex)


@dataclass(slots=True)
class ChatSession:
    system_prompt: str
    session_id: str = field(default_factory=lambda: uuid4().hex)
    title: str = "New Chat"
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    messages: list[ChatMessage] = field(default_factory=list)

    def add_user_message(self, content: str) -> None:
        self.messages.append(ChatMessage(role="user", content=content))
        self.touch()
        if self.title == "New Chat":
            self.title = self.derive_title()

    def add_assistant_message(self, content: str) -> None:
        self.messages.append(ChatMessage(role="assistant", content=content))
        self.touch()

    def delete_message(self, message_id: str) -> bool:
        original_count = len(self.messages)
        self.messages = [
            message for message in self.messages if message.message_id != message_id
        ]
        deleted = len(self.messages) != original_count
        if deleted:
            self.touch()
            if not any(message.role == "user" for message in self.messages):
                self.title = "New Chat"
        return deleted

    def as_prompt_messages(self) -> list[dict[str, str]]:
        payload = [{"role": "system", "content": self.system_prompt}]
        payload.extend(
            {"role": message.role, "content": message.content}
            for message in self.messages
        )
        return payload

    def derive_title(self) -> str:
        for message in self.messages:
            if message.role == "user" and message.content.strip():
                return message.content.strip().splitlines()[0][:50]
        return "New Chat"

    def touch(self) -> None:
        self.updated_at = datetime.now(UTC).isoformat()
