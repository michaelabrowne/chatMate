from pathlib import Path

from PySide6.QtWidgets import QApplication

from chatmate.config import load_app_config
from chatmate.controllers.chat_controller import ChatController
from chatmate.services.chat_repository import ChatRepository
from chatmate.services.llm.factory import build_llm_client
from chatmate.views.main_window import MainWindow


def main() -> None:
    config_path = Path("config.yaml")
    config = load_app_config(config_path)
    llm_client = build_llm_client(config)
    chat_repository = ChatRepository(Path(".chatmate/chats"))
    app = QApplication.instance() or QApplication([])
    view = MainWindow()
    controller = ChatController(config, llm_client, chat_repository, view)
    controller.initialize()
    view.show()
    app.exec()
