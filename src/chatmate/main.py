from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from chatmate.config import load_app_config
from chatmate.controllers.chat_controller import ChatController
from chatmate.services.chat_repository import ChatRepository
from chatmate.services.llm.factory import build_llm_client
from chatmate.views.main_window import MainWindow


def _config_path() -> Path:
    # Prefer user-level config so the bundle config can be overridden
    user_config = Path.home() / ".config" / "chatmate" / "config.yaml"
    if user_config.exists():
        return user_config
    # When running as a PyInstaller bundle, data files land in sys._MEIPASS
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "config.yaml"  # type: ignore[attr-defined]
    return Path("config.yaml")


def main() -> None:
    config = load_app_config(_config_path())
    llm_client = build_llm_client(config)
    # Always store chats in ~/.chatmate/chats so they survive app updates
    chat_repository = ChatRepository(Path.home() / ".chatmate" / "chats")
    app = QApplication.instance() or QApplication([])
    view = MainWindow()
    controller = ChatController(config, llm_client, chat_repository, view)
    controller.initialize()
    view.show()
    app.exec()
