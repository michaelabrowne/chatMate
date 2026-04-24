from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal

from chatmate.config import AppConfig
from chatmate.models.chat import ChatSession
from chatmate.services.chat_repository import ChatRepository
from chatmate.services.llm.factory import build_llm_client
from chatmate.services.llm.base import LLMClient
from chatmate.views.main_window import MainWindow


class ChatGenerationWorker(QObject):
    finished = Signal()
    succeeded = Signal(str)
    failed = Signal(str)

    def __init__(self, llm_client: LLMClient, messages: list[dict[str, str]]) -> None:
        super().__init__()
        self.llm_client = llm_client
        self.messages = messages

    def run(self) -> None:
        try:
            reply = self.llm_client.generate(self.messages)
        except Exception as exc:
            self.failed.emit(str(exc))
        else:
            self.succeeded.emit(reply)
        finally:
            self.finished.emit()


class ChatController(QObject):
    def __init__(
        self,
        config: AppConfig,
        llm_client: LLMClient,
        chat_repository: ChatRepository,
        view: MainWindow,
    ) -> None:
        super().__init__()
        self.config = config
        self.llm_client = llm_client
        self.chat_repository = chat_repository
        self.view = view
        self.session = ChatSession(system_prompt=config.app.system_prompt)
        self.active_provider = config.provider.active.lower()
        self.llm_client = build_llm_client(config, self.active_provider)
        self._busy = False
        self._request_thread: QThread | None = None
        self._worker: ChatGenerationWorker | None = None
        self._pending_session_id: str | None = None

    def initialize(self) -> None:
        self.view.bind_controller(self)
        self.view.show_welcome(
            app_name=self.config.app.name,
            provider_name=self.active_provider,
            model_name=self._active_model_name(),
        )
        self.view.set_model_options(self.available_models(), self.active_provider)
        existing_sessions = self.chat_repository.list_sessions()
        if existing_sessions:
            self.session = existing_sessions[0]
            self.view.render_session(self.session)
        else:
            self.chat_repository.save(self.session)
        self._refresh_session_list()

    def send_message(self, user_input: str) -> None:
        if not user_input or self._busy:
            return

        self.session.add_user_message(user_input)
        user_message = self.session.messages[-1]
        self.view.show_user_message(user_message.message_id, user_input)
        self._autosave()
        self._busy = True
        self._pending_session_id = self.session.session_id
        self.view.set_busy(True)
        self.view.show_assistant_pending()

        prompt_messages = self.session.as_prompt_messages()
        self._request_thread = QThread()
        self._worker = ChatGenerationWorker(self.llm_client, prompt_messages)
        self._worker.moveToThread(self._request_thread)
        self._request_thread.started.connect(self._worker.run)
        self._worker.succeeded.connect(self._handle_generation_success)
        self._worker.failed.connect(self._handle_generation_error)
        self._worker.finished.connect(self._finish_generation)
        self._worker.finished.connect(self._worker.deleteLater)
        self._request_thread.finished.connect(self._request_thread.deleteLater)
        self._request_thread.start()

    def show_history(self) -> None:
        self.view.show_history(
            [(message.role, message.content) for message in self.session.messages]
        )

    def copy_message(self, message_id: str) -> None:
        message = self._find_message(message_id)
        if message is None:
            self.view.show_system_message("Message no longer exists.")
            return
        self.view.copy_text(message.content)

    def delete_message(self, message_id: str) -> None:
        if self._busy:
            self.view.show_system_message("Wait for the current response to finish before deleting messages.")
            return
        if self.session.delete_message(message_id):
            self._autosave()
            self.view.render_session(self.session)

    def create_chat(self) -> None:
        if self._busy:
            self.view.show_system_message("Wait for the current response to finish before starting a new chat.")
            return
        self.session = ChatSession(system_prompt=self.config.app.system_prompt)
        self.chat_repository.save(self.session)
        self.view.render_session(self.session)
        self._refresh_session_list()

    def load_chat(self, session_id: str) -> None:
        if self._busy:
            self.view.show_system_message("Wait for the current response to finish before switching chats.")
            return
        self.session = self.chat_repository.load(session_id)
        self.view.render_session(self.session)
        self._refresh_session_list()

    def rename_chat(self, title: str) -> None:
        if self._busy:
            self.view.show_system_message("Wait for the current response to finish before renaming this chat.")
            return
        cleaned = title.strip()
        if not cleaned:
            self.view.show_system_message("Chat title cannot be empty.")
            return
        self.session.title = cleaned[:80]
        self._autosave()
        self.view.update_session_title(self.session.title)

    def rename_chat_by_id(self, session_id: str, title: str) -> None:
        if self._busy:
            self.view.show_system_message("Wait for the current response to finish before renaming this chat.")
            return
        cleaned = title.strip()
        if not cleaned:
            self.view.show_system_message("Chat title cannot be empty.")
            return
        session = self.chat_repository.load(session_id)
        session.title = cleaned[:80]
        self.chat_repository.save(session)
        if self.session.session_id == session_id:
            self.session.title = session.title
            self.view.update_session_title(self.session.title)
        self._refresh_session_list()

    def delete_chat(self, session_id: str) -> None:
        if self._busy:
            self.view.show_system_message("Wait for the current response to finish before deleting a chat.")
            return
        self.chat_repository.delete(session_id)
        if self.session.session_id == session_id:
            remaining = self.chat_repository.list_sessions()
            if remaining:
                self.session = remaining[0]
            else:
                self.session = ChatSession(system_prompt=self.config.app.system_prompt)
                self.chat_repository.save(self.session)
            self.view.render_session(self.session)
        self._refresh_session_list()

    def available_models(self) -> list[tuple[str, str]]:
        return [
            ("openai", self.config.provider.openai.model),
            ("anthropic", self.config.provider.anthropic.model),
            ("lmstudio", self.config.provider.lmstudio.model),
        ]

    def switch_model(self, provider_name: str) -> None:
        if self._busy:
            self.view.show_system_message("Wait for the current response to finish before switching models.")
            return
        provider_name = provider_name.lower()
        try:
            self.llm_client = build_llm_client(self.config, provider_name)
        except Exception as exc:
            self.view.show_system_message(f"Could not switch model: {exc}")
            return
        self.active_provider = provider_name
        self.view.update_provider_display(provider_name, self._active_model_name())
        self.view.show_system_message(
            f"Switched model to {self._active_model_name()} via {provider_name}."
        )

    def _handle_generation_success(self, reply: str) -> None:
        if self._pending_session_id != self.session.session_id:
            return
        self.session.add_assistant_message(reply)
        assistant_message = self.session.messages[-1]
        self.view.show_assistant_message(assistant_message.message_id, reply)
        self._autosave()

    def _handle_generation_error(self, error_message: str) -> None:
        self.view.show_response_error(f"Provider error: {error_message}")

    def _finish_generation(self) -> None:
        if self._request_thread is not None:
            self._request_thread.quit()
            self._request_thread.wait()
        self._request_thread = None
        self._worker = None
        self._pending_session_id = None
        self._busy = False
        self.view.set_busy(False)

    def _active_model_name(self) -> str:
        active = self.active_provider
        if active == "openai":
            return self.config.provider.openai.model
        if active == "anthropic":
            return self.config.provider.anthropic.model
        return self.config.provider.lmstudio.model

    def _autosave(self) -> None:
        self.chat_repository.save(self.session)
        self._refresh_session_list()
        self.view.update_session_title(self.session.title)

    def _find_message(self, message_id: str):
        for message in self.session.messages:
            if message.message_id == message_id:
                return message
        return None

    def _refresh_session_list(self) -> None:
        self.view.update_chat_list(
            sessions=self.chat_repository.list_sessions(),
            active_session_id=self.session.session_id,
        )
