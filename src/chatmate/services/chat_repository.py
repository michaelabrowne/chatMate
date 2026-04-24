from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

from chatmate.models.chat import ChatMessage, ChatSession


class ChatRepository:
    def __init__(self, storage_dir: Path) -> None:
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save(self, session: ChatSession) -> None:
        session.touch()
        path = self.storage_dir / f"{session.session_id}.json"
        path.write_text(json.dumps(asdict(session), indent=2), encoding="utf-8")

    def load(self, session_id: str) -> ChatSession:
        path = self.storage_dir / f"{session_id}.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
        return ChatSession(
            system_prompt=raw["system_prompt"],
            session_id=raw["session_id"],
            title=raw["title"],
            created_at=raw["created_at"],
            updated_at=raw["updated_at"],
            messages=[
                ChatMessage(
                    role=message["role"],
                    content=message["content"],
                    message_id=message.get("message_id") or uuid4().hex,
                )
                for message in raw.get("messages", [])
            ],
        )

    def list_sessions(self) -> list[ChatSession]:
        sessions: list[ChatSession] = []
        for path in sorted(self.storage_dir.glob("*.json")):
            try:
                sessions.append(self.load(path.stem))
            except (OSError, ValueError, KeyError, json.JSONDecodeError, TypeError):
                continue
        sessions.sort(key=lambda session: session.updated_at, reverse=True)
        return sessions

    def delete(self, session_id: str) -> None:
        path = self.storage_dir / f"{session_id}.json"
        if path.exists():
            path.unlink()
