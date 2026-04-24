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
    QTextBrowser,
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

    _MESSAGE_CSS = (
        "body{font-family:Helvetica,Arial,sans-serif;font-size:14px;line-height:1.5;color:#e5e7eb;}"
        "pre{background:#0b0d10;border:1px solid #30363d;border-radius:4px;padding:10px;white-space:pre-wrap;}"
        "code{font-family:'Menlo','SF Mono',Consolas,'Courier New',monospace;font-size:13px;}"
        "p{margin:0 0 8px 0;}"
        "p:last-child{margin-bottom:0;}"
        "table{border-collapse:collapse;width:100%;}"
        "th,td{border:1px solid #30363d;padding:4px 8px;}"
        "th{background:#1a1d24;}"
        "blockquote{border-left:3px solid #4b5563;margin:0 0 8px 0;padding-left:12px;color:#9ca3af;}"
        "a{color:#93c5fd;}"
        "ul,ol{margin:0 0 8px 0;padding-left:20px;}"
        "li{margin-bottom:2px;}"
    )

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
        self.copy_button.hide()

        self.delete_button = QToolButton()
        self.delete_button.setText("Delete")
        self.delete_button.setToolTip("Delete message")
        self.delete_button.clicked.connect(self._delete_message)
        self.delete_button.hide()

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.addWidget(self.role_label)
        actions.addStretch(1)
        actions.addWidget(self.copy_button)
        actions.addWidget(self.delete_button)

        self.body = QTextBrowser()
        self.body.setOpenExternalLinks(True)
        self.body.setFrameShape(QFrame.Shape.NoFrame)
        self.body.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.body.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.body.setStyleSheet("QTextBrowser { background: transparent; border: none; }")
        self.body.document().setDefaultStyleSheet(self._MESSAGE_CSS)
        self.body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.body.document().contentsChanged.connect(self._resize_body)

        layout = QVBoxLayout()
        layout.setContentsMargins(14, 10, 14, 10)
        layout.addLayout(actions)
        layout.addWidget(self.body)
        self.setLayout(layout)
        self.set_message_id(message_id)
        self.set_content(content)

    def enterEvent(self, event) -> None:
        if self.message_id is not None:
            self.copy_button.show()
            self.delete_button.show()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.copy_button.hide()
        self.delete_button.hide()
        super().leaveEvent(event)

    def set_message_id(self, message_id: str | None) -> None:
        self.message_id = message_id

    def _resize_body(self) -> None:
        height = int(self.body.document().size().height()) + 4
        self.body.setFixedHeight(max(20, height))

    def set_content(self, content: str) -> None:
        self.content = content
        if self.role == "assistant":
            body_html = markdown2.markdown(
                content,
                extras=["fenced-code-blocks", "tables", "strike", "break-on-newline"],
            )
        else:
            body_html = f"<p>{html.escape(content).replace(chr(10), '<br>')}</p>"
        self.body.setHtml(body_html)

    def append_content(self, chunk: str) -> None:
        self.set_content(f"{self.content}{chunk}")

    def _copy_message(self) -> None:
        if self.message_id is not None:
            self.copy_requested.emit(self.message_id)

    def _delete_message(self) -> None:
        if self.message_id is not None:
            self.delete_requested.emit(self.message_id)


class SavedChatRow(QWidget):
    menu_requested = Signal(str, QPoint)

    def __init__(self, session_id: str, title: str, is_active: bool) -> None:
        super().__init__()
        self.session_id = session_id
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.title_label = QLabel(title)
        self.title_label.setToolTip(title)

        if is_active:
            self.setStyleSheet("""
                QWidget { background: #1e2333; }
                QLabel { font-weight: 600; background: transparent; color: #e5e7eb; }
                QToolButton { background: transparent; border: none; color: #9ca3af; }
            """)
            indicator = QLabel()
            indicator.setFixedWidth(3)
            indicator.setStyleSheet("background: #2563eb; border-radius: 1px;")
        else:
            indicator = QLabel()
            indicator.setFixedWidth(3)
            indicator.setStyleSheet("background: transparent;")

        self.menu_button = QToolButton()
        self.menu_button.setText("···")
        self.menu_button.setToolTip("Chat actions")
        self.menu_button.clicked.connect(self._emit_menu_requested)
        self.menu_button.hide()

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 4, 4, 4)
        layout.setSpacing(6)
        layout.addWidget(indicator)
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
        self._auto_scroll = True
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
                background: #1c2333;
                border: 1px solid #3b5bdb;
                border-radius: 10px;
            }
            QFrame#assistantMessage {
                background: #181c22;
                border: 1px solid #2d3748;
                border-radius: 10px;
            }
            QFrame#systemMessage {
                background: #26211b;
                border: 1px solid #6b5a35;
                border-radius: 10px;
            }
            QLabel#messageRole {
                color: #6b7280;
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            QListWidget {
                border: 0;
                background: #15181d;
            }
            QListWidget::item {
                padding: 0;
            }
            QListWidget::item:selected {
                background: transparent;
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
            QComboBox::drop-down {
                border: none;
                padding-right: 8px;
            }
            QPushButton, QToolButton {
                background: #20242b;
                border: 1px solid #30363d;
                border-radius: 6px;
                color: #e5e7eb;
                padding: 5px 12px;
            }
            QFrame QToolButton {
                font-size: 11px;
                padding: 2px 8px;
                background: #171a1f;
                border-color: #2d3340;
            }
            QPushButton#sendButton {
                background: #2563eb;
                border-color: #1d4ed8;
                font-weight: 600;
                padding: 6px 18px;
            }
            QPushButton#sendButton:hover {
                background: #1d4ed8;
            }
            QPushButton#sendButton:disabled {
                background: #1e2a4a;
                border-color: #1e3a6e;
                color: #4b6ab0;
            }
            QPushButton:hover, QToolButton:hover {
                background: #2a3038;
                border-color: #4b5563;
            }
            QPushButton:disabled, QToolButton:disabled {
                color: #4b5563;
            }
            QMenu {
                background: #1a1d24;
                border: 1px solid #2d3340;
                border-radius: 6px;
                color: #e5e7eb;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: #2563eb;
            }
            QStatusBar {
                color: #6b7280;
                font-size: 12px;
            }
            """
        )

        self.chat_list = QListWidget()
        self.chat_list.itemSelectionChanged.connect(self._on_chat_selected)

        self.sidebar_toggle_button = QToolButton()
        self.sidebar_toggle_button.setText("‹")
        self.sidebar_toggle_button.setToolTip("Hide chat history")
        self.sidebar_toggle_button.setFixedSize(28, 28)
        self.sidebar_toggle_button.clicked.connect(self._toggle_chat_history)

        self.chat_menu = QMenu(self)
        self.rename_action = QAction("Rename", self)
        self.rename_action.triggered.connect(self._on_rename_chat_clicked)
        self.delete_action = QAction("Delete", self)
        self.delete_action.triggered.connect(self._on_delete_chat_clicked)
        self.chat_menu.addAction(self.rename_action)
        self.chat_menu.addAction(self.delete_action)
        self._menu_session_id: str | None = None

        self.sidebar_new_chat_button = QPushButton("+ New Chat")
        self.sidebar_new_chat_button.clicked.connect(self._on_new_chat_clicked)

        sidebar_header_label = QLabel("Chats")
        sidebar_header_label.setStyleSheet("font-weight: 600; font-size: 13px; color: #9ca3af;")

        history_header = QHBoxLayout()
        history_header.setContentsMargins(12, 10, 8, 8)
        history_header.addWidget(sidebar_header_label)
        history_header.addStretch(1)
        history_header.addWidget(self.sidebar_new_chat_button)

        history_layout = QVBoxLayout()
        history_layout.setContentsMargins(0, 0, 0, 0)
        history_layout.setSpacing(0)
        history_layout.addLayout(history_header)
        history_layout.addWidget(self.chat_list, stretch=1)

        self.history_group = QWidget()
        self.history_group.setLayout(history_layout)
        self.history_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        self.chat_title_label = QLabel("New Chat")
        self.chat_title_label.setStyleSheet("font-size: 14px; font-weight: 600;")

        self.model_selector = QComboBox()
        self.model_selector.setMinimumWidth(200)
        self.model_selector.currentIndexChanged.connect(self._on_model_changed)

        self.scroll_bottom_button = QToolButton()
        self.scroll_bottom_button.setText("↓")
        self.scroll_bottom_button.setToolTip("Jump to latest message")
        self.scroll_bottom_button.setFixedSize(28, 28)
        self.scroll_bottom_button.clicked.connect(self._scroll_to_bottom)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(12, 10, 12, 10)
        title_row.addWidget(self.sidebar_toggle_button)
        title_row.addSpacing(8)
        title_row.addWidget(self.chat_title_label)
        title_row.addStretch(1)
        title_row.addWidget(self.model_selector)
        title_row.addWidget(self.scroll_bottom_button)

        self.message_container = QWidget()
        self.message_layout = QVBoxLayout()
        self.message_layout.setContentsMargins(18, 18, 18, 18)
        self.message_layout.setSpacing(12)
        self.message_layout.addStretch(1)
        self.message_container.setLayout(self.message_layout)

        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.chat_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.chat_scroll.setWidget(self.message_container)
        self._message_widgets: list[ChatMessageWidget] = []
        self.chat_scroll.verticalScrollBar().rangeChanged.connect(self._on_scroll_range_changed)
        self.chat_scroll.verticalScrollBar().valueChanged.connect(self._on_scroll_value_changed)

        self.message_input = MessageInput()
        self.message_input.setPlaceholderText("Message… (Enter to send, Shift+Enter for newline)")
        self.message_input.setFixedHeight(64)
        self.message_input.textChanged.connect(self.message_input.resize_for_content)
        self.message_input.submit_requested.connect(self._on_send_clicked)

        self.send_button = QPushButton("Send")
        self.send_button.setObjectName("sendButton")
        self.send_button.clicked.connect(self._on_send_clicked)

        self.history_button = QPushButton("Transcript")
        self.history_button.setToolTip("Show full message history")
        self.history_button.clicked.connect(self._on_history_clicked)

        input_area = QWidget()
        input_area.setStyleSheet("QWidget { background: #13161b; border-top: 1px solid #1f2430; }")
        input_layout = QVBoxLayout()
        input_layout.setContentsMargins(16, 12, 16, 12)
        input_layout.setSpacing(8)
        input_layout.addWidget(self.message_input)
        chat_controls = QHBoxLayout()
        chat_controls.addWidget(self.history_button)
        chat_controls.addStretch(1)
        chat_controls.addWidget(self.send_button)
        input_layout.addLayout(chat_controls)
        input_area.setLayout(input_layout)

        title_bar = QWidget()
        title_bar.setStyleSheet("QWidget { background: #13161b; border-bottom: 1px solid #1f2430; }")
        title_bar.setLayout(title_row)

        chat_layout = QVBoxLayout()
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)
        chat_layout.addWidget(title_bar)
        chat_layout.addWidget(self.chat_scroll, stretch=1)
        chat_layout.addWidget(input_area)

        chat_panel = QWidget()
        chat_panel.setLayout(chat_layout)

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.addWidget(self.history_group)
        self.main_splitter.addWidget(chat_panel)
        self.main_splitter.setCollapsible(0, True)
        self.main_splitter.setCollapsible(1, False)
        self.main_splitter.setSizes([260, 1060])
        self.main_splitter.setHandleWidth(1)
        self.main_splitter.setStyleSheet("QSplitter::handle { background: #1f2430; }")

        self.setCentralWidget(self.main_splitter)
        self.setStatusBar(QStatusBar())

    def bind_controller(self, controller) -> None:
        self.controller = controller

    def show_welcome(self, app_name: str, provider_name: str, model_name: str) -> None:
        self.setWindowTitle(app_name)
        self.update_provider_display(provider_name, model_name)
        self.show_system_message(
            "Ready. Chats are auto-saved — manage them from the sidebar."
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
                label = f"{provider} · {model}"
                self.model_selector.addItem(label, provider)
                if provider == active_provider:
                    active_index = index
            self.model_selector.setCurrentIndex(active_index)
        finally:
            self._suppress_model_signal = False

    def update_provider_display(self, provider_name: str, model_name: str) -> None:
        pass

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
        self.chat_title_label.setText(title)

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
        self._pending_assistant_widget = self._add_message_widget("assistant", "Thinking…")
        self.statusBar().showMessage("Waiting for response…")

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
        self.send_button.setText("Thinking…" if busy else "Send")
        self.history_button.setDisabled(busy)
        self.sidebar_new_chat_button.setDisabled(busy)
        self.model_selector.setDisabled(busy)
        self.chat_list.setDisabled(busy)
        self.statusBar().showMessage("Working…" if busy else "Ready")

    def append_to_last_assistant_message(self, chunk: str) -> None:
        if not self._message_widgets or self._message_widgets[-1].role != "assistant":
            self._add_message_widget("assistant", "")
        self._message_widgets[-1].append_content(chunk)
        self._scroll_to_bottom()

    def copy_text(self, content: str) -> None:
        QApplication.clipboard().setText(content)
        self.statusBar().showMessage("Copied to clipboard.", 3000)

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

    def _on_scroll_range_changed(self, _, max_val: int) -> None:
        if self._auto_scroll:
            self.chat_scroll.verticalScrollBar().setValue(max_val)

    def _on_scroll_value_changed(self, value: int) -> None:
        bar = self.chat_scroll.verticalScrollBar()
        self._auto_scroll = value >= bar.maximum() - 20

    def _scroll_to_bottom(self) -> None:
        self._auto_scroll = True
        QTimer.singleShot(0, lambda: self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        ))

    def _toggle_chat_history(self) -> None:
        if self._history_visible:
            self.history_group.hide()
            self.main_splitter.setSizes([0, 1])
            self.sidebar_toggle_button.setText("›")
            self.sidebar_toggle_button.setToolTip("Show chat history")
        else:
            self.history_group.show()
            self.main_splitter.setSizes([260, 1060])
            self.sidebar_toggle_button.setText("‹")
            self.sidebar_toggle_button.setToolTip("Hide chat history")
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
        self._menu_session_id = None
        if session_id is None:
            return
        title, accepted = QInputDialog.getText(self, "Rename Chat", "New title:")
        if accepted:
            self.controller.rename_chat_by_id(session_id, title)

    def _on_delete_chat_clicked(self) -> None:
        if self.controller is None:
            return
        session_id = self._current_menu_session_id()
        self._menu_session_id = None
        if session_id is None:
            return
        row = self._chat_rows.get(session_id)
        title = row.title_label.text() if row is not None else "this chat"
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Delete Chat")
        dlg.setText(f"Delete \"{title}\"?")
        dlg.setIcon(QMessageBox.Icon.NoIcon)
        dlg.setStandardButtons(QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Ok)
        dlg.setDefaultButton(QMessageBox.StandardButton.Cancel)
        dlg.button(QMessageBox.StandardButton.Ok).setText("Delete")
        if dlg.exec() == QMessageBox.StandardButton.Ok:
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
