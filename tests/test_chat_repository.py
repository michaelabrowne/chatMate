from pathlib import Path

from chatmate.models.chat import ChatSession
from chatmate.services.chat_repository import ChatRepository


def test_chat_repository_save_and_load(tmp_path: Path) -> None:
    repository = ChatRepository(tmp_path / "chats")
    session = ChatSession(system_prompt="Be helpful", title="Project Notes")
    session.add_user_message("Hello world")
    session.add_assistant_message("Hi there")

    repository.save(session)
    loaded = repository.load(session.session_id)

    assert loaded.title == "Project Notes"
    assert len(loaded.messages) == 2
    assert loaded.messages[0].content == "Hello world"


def test_chat_repository_lists_newest_first(tmp_path: Path) -> None:
    repository = ChatRepository(tmp_path / "chats")
    older = ChatSession(system_prompt="A", title="Older")
    newer = ChatSession(system_prompt="B", title="Newer")

    repository.save(older)
    repository.save(newer)

    sessions = repository.list_sessions()

    assert sessions[0].session_id == newer.session_id
