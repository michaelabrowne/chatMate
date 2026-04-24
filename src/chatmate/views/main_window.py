from __future__ import annotations

import html

import markdown2
from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QContextMenuEvent, QIcon, QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from chatmate.models.chat import ChatSession


class MessageInput(QPlainTextEdit):
    submit_requested = Signal()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            modifiers = event.modifiers()
            if modifiers & (
                Qt.KeyboardModifier.ShiftModifier | Qt.KeyboardModifier.AltModifier
            ):
                self.insertPlainText("\r\n")
                return
            self.submit_requested.emit()
            return
        super().keyPressEvent(event)

    def resize_for_content(self) -> None:
        document_height = int(self.document().size().height()) + 18
        self.setFixedHeight(max(64, min(180, document_height)))


class ChatMessageWidget(QFrame):
    copy_requested = Signal(str)
    delete_requested = Signal(str)

    def __init__(self, message_id: str | None, role: str, content: str) -> None:
        super().__init__()
        self.message_id = message_id
        self.role = role
        self.content = content
        self.setObjectName(f"{role}Message")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setMaximumWidth(860 if role == "assistant" else 760)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)

        self.role_label = QLabel(role.title())
        self.role_label.setObjectName("messageRole")

        self.copy_button = QToolButton()
        self.copy_button.setText("Copy")
        self.copy_button.setToolTip("Copy message")
        self.copy_button.clicked.connect(self._copy_message)

        self.delete_button = QToolButton()
        self.delete_button.setText("Delete")
        self.delete_button.setToolTip("Delete message")
        self.delete_button.clicked.connect(self._delete_message)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.addWidget(self.role_label)
        actions.addStretch(1)
        actions.addWidget(self.copy_button)
        actions.addWidget(self.delete_button)

        self.body = QLabel()
        self.body.setTextFormat(Qt.TextFormat.RichText)
        self.body.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        self.body.setOpenExternalLinks(True)
        self.body.setWordWrap(True)
        self.body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.body.setStyleSheet("background: transparent;")

        layout = QVBoxLayout()
        layout.setContentsMargins(14, 10, 14, 10)
        layout.addLayout(actions)
        layout.addWidget(self.body)
        self.setLayout(layout)
        self.set_message_id(message_id)
        self.set_content(content)

    def set_message_id(self, message_id: str | None) -> None:
        self.message_id = message_id
        has_saved_message = message_id is not None
        self.copy_button.setVisible(has_saved_message)
        self.delete_button.setVisible(has_saved_message)

    def set_content(self, content: str) -> None:
        self.content = content
        if self.role == "assistant":
            body_html = markdown2.markdown(
                content,
                extras=["fenced-code-blocks", "tables", "strike", "break-on-newline"],
            )
        else:
            body_html = f"<p>{html.escape(content).replace(chr(10), '<br>')}</p>"
        self.body.setText(self._wrap_html(body_html))
        self.body.adjustSize()

    def append_content(self, chunk: str) -> None:
        self.set_content(f"{self.content}{chunk}")

    def _copy_message(self) -> None:
        if self.message_id is not None:
            self.copy_requested.emit(self.message_id)

    def _delete_message(self) -> None:
        if self.message_id is not None:
            self.delete_requested.emit(self.message_id)

    def _wrap_html(self, body_html: str) -> str:
        return f"""
        <style>
            body {{
                font-family: Helvetica, Arial, sans-serif;
                font-size: 14px;
                line-height: 1.45;
                color: #e5e7eb;
            }}
            pre {{
                background: #0b0d10;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 10px;
                white-space: pre-wrap;
            }}
            code {{
                font-family: "SFMono-Regular", Consolas, monospace;
                font-size: 13px;
            }}
            table {{
                border-collapse: collapse;
            }}
            th, td {{
                border: 1px solid #30363d;
                padding: 4px 8px;
            }}
            a {{
                color: #93c5fd;
            }}
        </style>
        {body_html}
        """


class SavedChatRow(QWidget):
    menu_requested = Signal(str, QPoint)

    def __init__(self, session_id: str, title: str, is_active: bool) -> None:
        super().__init__()
        self.session_id = session_id

        self.title_label = QLabel(title)
        self.title_label.setToolTip(title)

        if is_active:
            self.title_label.setStyleSheet("font-weight: 600;")

        self.menu_button = QToolButton()
        self.menu_button.setText("...")
        self.menu_button.setToolTip("Chat actions")
        self.menu_button.clicked.connect(self._emit_menu_requested)
        self.menu_button.hide()

        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 4, 4)
        layout.addWidget(self.title_label, stretch=1)
        layout.addWidget(self.menu_button)
        self.setLayout(layout)

    def _emit_menu_requested(self) -> None:
        menu_position = self.menu_button.mapToGlobal(self.menu_button.rect().bottomLeft())
        self.menu_requested.emit(self.session_id, menu_position)

    def enterEvent(self, event) -> None:
        self.menu_button.show()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.menu_button.hide()
        super().leaveEvent(event)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        self.menu_requested.emit(self.session_id, event.globalPos())


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.controller = None
        self._suppress_chat_list_signal = False
        self._suppress_model_signal = False
        self._chat_rows: dict[str, SavedChatRow] = {}
        self._history_visible = True
        self._pending_assistant_widget: ChatMessageWidget | None = None
        self.setWindowTitle("ChatMate")
        self.resize(1320, 840)
        self.setStyleSheet(
            """
            QWidget {
                font-family: Helvetica, Arial, sans-serif;
                background: #111316;
                color: #e5e7eb;
            }
            QFrame#userMessage {
                background: #171b22;
                border: 1px solid #64748b;
                border-radius: 10px;
            }
            QFrame#assistantMessage {
                background: #181c22;
                border: 1px solid #64748b;
                border-radius: 10px;
            }
            QFrame#systemMessage {
                background: #26211b;
                border: 1px solid #6b5a35;
                border-radius: 10px;
            }
            QLabel#messageRole {
                color: #9ca3af;
                font-size: 12px;
                font-weight: 600;
            }
            QListWidget {
                border: 0;
                background: #15181d;
            }
            QListWidget::item:selected {
                background: #20242b;
            }
            QScrollArea {
                background: #111316;
            }
            QPlainTextEdit, QComboBox {
                background: #171a1f;
                border: 1px solid #30363d;
                border-radius: 6px;
                color: #e5e7eb;
                padding: 6px;
            }
            QPushButton, QToolButton {
                background: #20242b;
                border: 1px solid #30363d;
                border-radius: 6px;
                color: #e5e7eb;
                padding: 5px 9px;
            }
            QFrame QToolButton {
                font-size: 11px;
                padding: 3px 6px;
                background: #171a1f;
                border-color: #3d4652;
            }
            QPushButton:hover, QToolButton:hover {
                background: #2a3038;
            }
            QPushButton:disabled, QToolButton:disabled {
                color: #6b7280;
            }
            QMenu {
                background: #171a1f;
                border: 1px solid #30363d;
                color: #e5e7eb;
            }
            QMenu::item:selected {
                background: #2563eb;
            }
            """
        )

        self.chat_list = QListWidget()
        self.chat_list.itemSelectionChanged.connect(self._on_chat_selected)

        self.sidebar_toggle_button = QToolButton()
        self.sidebar_toggle_button.setText("<")
        self.sidebar_toggle_button.setToolTip("Collapse chat history")
        self.sidebar_toggle_button.clicked.connect(self._toggle_chat_history)

        self.history_toggle_button = QPushButton("Hide Chats")
        self.history_toggle_button.clicked.connect(self._toggle_chat_history)

        self.chat_menu = QMenu(self)
        self.rename_action = QAction("Rename Chat", self)
        self.rename_action.triggered.connect(self._on_rename_chat_clicked)
        self.delete_action = QAction("Delete Chat", self)
        self.delete_action.triggered.connect(self._on_delete_chat_clicked)
        self.chat_menu.addAction(self.rename_action)
        self.chat_menu.addAction(self.delete_action)
        self._menu_session_id: str | None = None

        self.sidebar_new_chat_button = QPushButton("New")
        self.sidebar_new_chat_button.clicked.connect(self._on_new_chat_clicked)

        history_header = QHBoxLayout()
        history_header.addWidget(QLabel("Saved Chats"))
        history_header.addStretch(1)
        history_header.addWidget(self.sidebar_new_chat_button)

        history_layout = QVBoxLayout()
        history_layout.addLayout(history_header)
        history_layout.addWidget(self.chat_list, stretch=1)

        self.history_group = QWidget()
        self.history_group.setLayout(history_layout)
        self.history_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        self.chat_title_label = QLabel("Current Chat: New Chat")
        self.provider_label = QLabel()
        self.provider_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self.model_selector = QComboBox()
        self.model_selector.currentIndexChanged.connect(self._on_model_changed)

        self.inline_new_chat_icon = QToolButton()
        self.inline_new_chat_icon.setIcon(QIcon.fromTheme("document-new"))
        self.inline_new_chat_icon.setText("+")
        self.inline_new_chat_icon.setToolTip("Start a new chat")
        self.inline_new_chat_icon.clicked.connect(self._on_new_chat_clicked)

        self.scroll_bottom_button = QToolButton()
        self.scroll_bottom_button.setText("v")
        self.scroll_bottom_button.setToolTip("Jump to latest message")
        self.scroll_bottom_button.clicked.connect(self._scroll_to_bottom)

        title_row = QHBoxLayout()
        title_row.addWidget(self.chat_title_label)
        title_row.addStretch(1)
        title_row.addWidget(QLabel("Model"))
        title_row.addWidget(self.model_selector)
        title_row.addWidget(self.inline_new_chat_icon)
        title_row.addWidget(self.scroll_bottom_button)
        title_row.addWidget(self.history_toggle_button)

        self.message_container = QWidget()
        self.message_layout = QVBoxLayout()
        self.message_layout.setContentsMargins(18, 18, 18, 18)
        self.message_layout.setSpacing(12)
        self.message_layout.addStretch(1)
        self.message_container.setLayout(self.message_layout)

        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.chat_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.chat_scroll.setWidget(self.message_container)
        self._message_widgets: list[ChatMessageWidget] = []

        self.message_input = MessageInput()
        self.message_input.setPlaceholderText(
            "Type a message..."
        )
        self.message_input.setFixedHeight(72)
        self.message_input.textChanged.connect(self.message_input.resize_for_content)
        self.message_input.submit_requested.connect(self._on_send_clicked)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self._on_send_clicked)

        self.history_button = QPushButton("Show Transcript")
        self.history_button.clicked.connect(self._on_history_clicked)

        chat_controls = QHBoxLayout()
        chat_controls.addWidget(self.provider_label, stretch=1)
        chat_controls.addWidget(self.history_button)
        chat_controls.addWidget(self.send_button)

        chat_layout = QVBoxLayout()
        chat_layout.addLayout(title_row)
        chat_layout.addWidget(self.chat_scroll, stretch=1)
        chat_layout.addWidget(self.message_input)
        chat_layout.addLayout(chat_controls)

        chat_panel = QWidget()
        chat_panel.setLayout(chat_layout)

        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(chat_panel, stretch=1)
        right_panel.setLayout(right_layout)

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.addWidget(self.history_group)
        self.main_splitter.addWidget(right_panel)
        self.main_splitter.setCollapsible(0, True)
        self.main_splitter.setCollapsible(1, False)
        self.main_splitter.setSizes([320, 1000])

        top_bar_widget = QWidget()
        top_bar_widget.setFixedHeight(36)
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(8, 4, 8, 4)
        top_bar.setSpacing(8)
        top_bar.addWidget(self.sidebar_toggle_button)
        top_bar.addWidget(QLabel("ChatMate"))
        top_bar.addStretch(1)
        top_bar_widget.setLayout(top_bar)

        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(top_bar_widget)
        layout.addWidget(self.main_splitter)
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.setStatusBar(QStatusBar())

    def bind_controller(self, controller) -> None:
        self.controller = controller

    def show_welcome(self, app_name: str, provider_name: str, model_name: str) -> None:
        self.setWindowTitle(app_name)
        self.update_provider_display(provider_name, model_name)
        self.show_system_message(
            "Ready. Chats are auto-saved, and you can manage them from the sidebar or the main chat area."
        )

    def set_model_options(
        self,
        models: list[tuple[str, str]],
        active_provider: str,
    ) -> None:
        self._suppress_model_signal = True
        try:
            self.model_selector.clear()
            active_index = 0
            for index, (provider, model) in enumerate(models):
                label = f"{provider} | {model}"
                self.model_selector.addItem(label, provider)
                if provider == active_provider:
                    active_index = index
            self.model_selector.setCurrentIndex(active_index)
        finally:
            self._suppress_model_signal = False

    def update_provider_display(self, provider_name: str, model_name: str) -> None:
        self.provider_label.setText(f"Provider: {provider_name} | Model: {model_name}")

    def render_session(self, session: ChatSession) -> None:
        self._clear_messages()
        self.update_session_title(session.title)
        for message in session.messages:
            self._add_message_widget(message.role, message.content, message.message_id)

    def update_chat_list(self, sessions: list[ChatSession], active_session_id: str) -> None:
        self._suppress_chat_list_signal = True
        try:
            self._chat_rows = {}
            self.chat_list.clear()
            active_item: QListWidgetItem | None = None
            for session in sessions:
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, session.session_id)
                item.setToolTip(f"Updated: {session.updated_at}")
                self.chat_list.addItem(item)
                row = SavedChatRow(
                    session_id=session.session_id,
                    title=session.title,
                    is_active=session.session_id == active_session_id,
                )
                row.menu_requested.connect(self._open_chat_menu_for_session)
                self.chat_list.setItemWidget(item, row)
                item.setSizeHint(row.sizeHint())
                self._chat_rows[session.session_id] = row
                if session.session_id == active_session_id:
                    active_item = item
            if active_item is not None:
                self.chat_list.setCurrentItem(active_item)
        finally:
            self._suppress_chat_list_signal = False

    def update_session_title(self, title: str) -> None:
        self.chat_title_label.setText(f"Current Chat: {title}")

    def show_user_message(self, message_id: str, content: str) -> None:
        self._add_message_widget("user", content, message_id)
        self.message_input.clear()

    def show_assistant_message(self, message_id: str, content: str) -> None:
        if self._pending_assistant_widget is not None:
            self._pending_assistant_widget.set_message_id(message_id)
            self._pending_assistant_widget.set_content(content)
            self._pending_assistant_widget = None
            self._scroll_to_bottom()
            return
        self._add_message_widget("assistant", content, message_id)

    def show_system_message(self, content: str) -> None:
        self._add_message_widget("system", content)
        self.statusBar().showMessage(content, 5000)

    def show_assistant_pending(self) -> None:
        self._pending_assistant_widget = self._add_message_widget("assistant", "Thinking...")
        self.statusBar().showMessage("Waiting for model response...")

    def show_response_error(self, content: str) -> None:
        if self._pending_assistant_widget is not None:
            self._pending_assistant_widget.set_content(content)
            self._pending_assistant_widget = None
        else:
            self._add_message_widget("system", content)
        self.statusBar().showMessage(content, 5000)

    def show_history(self, history: list[tuple[str, str]]) -> None:
        if not history:
            self.show_system_message("No messages yet.")
            return
        lines = [f"{role.title()}: {content}" for role, content in history]
        self.show_system_message("\n".join(lines))

    def set_busy(self, busy: bool) -> None:
        self.send_button.setDisabled(busy)
        self.send_button.setText("Thinking..." if busy else "Send")
        self.history_button.setDisabled(busy)
        self.sidebar_new_chat_button.setDisabled(busy)
        self.inline_new_chat_icon.setDisabled(busy)
        self.model_selector.setDisabled(busy)
        self.chat_list.setDisabled(busy)
        self.statusBar().showMessage("Working..." if busy else "Ready")

    def append_to_last_assistant_message(self, chunk: str) -> None:
        if not self._message_widgets or self._message_widgets[-1].role != "assistant":
            self._add_message_widget("assistant", "")
        self._message_widgets[-1].append_content(chunk)
        self._scroll_to_bottom()

    def copy_text(self, content: str) -> None:
        QApplication.clipboard().setText(content)
        self.statusBar().showMessage("Message copied.", 3000)

    def _clear_messages(self) -> None:
        while self.message_layout.count() > 1:
            item = self.message_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._message_widgets = []

    def _add_message_widget(
        self,
        role: str,
        content: str,
        message_id: str | None = None,
    ) -> ChatMessageWidget:
        widget = ChatMessageWidget(message_id, role, content)
        widget.copy_requested.connect(self._on_copy_message_clicked)
        widget.delete_requested.connect(self._on_delete_message_clicked)
        alignment = Qt.AlignmentFlag.AlignRight if role == "user" else Qt.AlignmentFlag.AlignLeft
        self.message_layout.insertWidget(
            max(0, self.message_layout.count() - 1),
            widget,
            alignment=alignment,
        )
        self._message_widgets.append(widget)
        self._scroll_to_bottom()
        return widget

    def _scroll_to_bottom(self) -> None:
        def scroll() -> None:
            bar = self.chat_scroll.verticalScrollBar()
            bar.setValue(bar.maximum())

        QTimer.singleShot(0, scroll)

    def _toggle_chat_history(self) -> None:
        if self._history_visible:
            self.history_group.hide()
            self.main_splitter.setSizes([0, 1])
            self.sidebar_toggle_button.setText(">")
            self.sidebar_toggle_button.setToolTip("Expand chat history")
            self.history_toggle_button.setText("Show Chats")
        else:
            self.history_group.show()
            self.main_splitter.setSizes([320, 1000])
            self.sidebar_toggle_button.setText("<")
            self.sidebar_toggle_button.setToolTip("Collapse chat history")
            self.history_toggle_button.setText("Hide Chats")
        self._history_visible = not self._history_visible

    def _on_send_clicked(self) -> None:
        if self.controller is None:
            return
        self.controller.send_message(self.message_input.toPlainText().strip())

    def _on_history_clicked(self) -> None:
        if self.controller is None:
            return
        self.controller.show_history()

    def _on_new_chat_clicked(self) -> None:
        if self.controller is None:
            return
        self.controller.create_chat()

    def _on_rename_chat_clicked(self) -> None:
        if self.controller is None:
            return
        session_id = self._current_menu_session_id()
        if session_id is None:
            return
        title, accepted = QInputDialog.getText(self, "Rename Chat", "New title:")
        if accepted:
            self.controller.rename_chat_by_id(session_id, title)

    def _on_delete_chat_clicked(self) -> None:
        if self.controller is None:
            return
        session_id = self._current_menu_session_id()
        if session_id is None:
            return
        row = self._chat_rows.get(session_id)
        title = row.title_label.text() if row is not None else "this chat"
        confirmed = QMessageBox.question(self, "Delete Chat", f"Delete '{title}'?")
        if confirmed == QMessageBox.StandardButton.Yes:
            self.controller.delete_chat(session_id)

    def _on_chat_selected(self) -> None:
        if self.controller is None or self._suppress_chat_list_signal:
            return
        item = self.chat_list.currentItem()
        if item is None:
            return
        self.controller.load_chat(item.data(Qt.ItemDataRole.UserRole))

    def _on_model_changed(self) -> None:
        if self.controller is None or self._suppress_model_signal:
            return
        provider = self.model_selector.currentData()
        if provider:
            self.controller.switch_model(provider)

    def _on_copy_message_clicked(self, message_id: str) -> None:
        if self.controller is None:
            return
        self.controller.copy_message(message_id)

    def _on_delete_message_clicked(self, message_id: str) -> None:
        if self.controller is None:
            return
        self.controller.delete_message(message_id)

    def _open_chat_menu_for_session(self, session_id: str, global_position: QPoint) -> None:
        self._menu_session_id = session_id
        for index in range(self.chat_list.count()):
            item = self.chat_list.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == session_id:
                self.chat_list.setCurrentItem(item)
                break
        self.chat_menu.exec(global_position)

    def _current_menu_session_id(self) -> str | None:
        if self._menu_session_id is not None:
            return self._menu_session_id
        item = self.chat_list.currentItem()
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)
