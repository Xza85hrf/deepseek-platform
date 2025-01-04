import asyncio
import datetime
import json
import os
import logging
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QTextEdit,
    QLineEdit,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QProgressBar,
    QScrollArea,
    QFrame,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import (
    QTextCursor,
    QTextCharFormat,
    QColor,
    QSyntaxHighlighter,
    QTextFormat,
    QPainter,
    QPalette,
    QIcon,
)
import markdown
import pygments
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name


class ChatWidget(QWidget):
    message_sent = pyqtSignal(str)
    new_message = pyqtSignal(dict)

    def __init__(self, theme_manager=None):
        if not QApplication.instance():
            raise RuntimeError("QApplication must be created before ChatWidget")

        super().__init__()
        self.theme_manager = theme_manager
        self.setWindowTitle("Chat")
        self.setAccessibleName("chat_widget")

        # Connect theme change signal if theme manager is provided
        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self._apply_theme)

        # Create main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create header with title and file button
        header = QHBoxLayout()
        self.title_label = QLabel("Chat")
        self.title_label.setAccessibleName("title_label")
        header.addWidget(self.title_label)

        # Add file button
        self.file_button = QPushButton("Add File")
        self.file_button.setAccessibleName("file_button")
        self.file_button.setIcon(QIcon.fromTheme("document-open"))
        self.file_button.clicked.connect(self._handle_file_button)
        header.addWidget(self.file_button)
        header.addStretch()
        layout.addLayout(header)

        # Create scrollable chat area with theme support
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setAccessibleName("chat_scroll_area")

        self.chat_container = QWidget()
        self.chat_container.setAccessibleName("chat_container")
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.addStretch()

        self.scroll_area.setWidget(self.chat_container)
        layout.addWidget(self.scroll_area)

        # Create message input area
        input_area = QHBoxLayout()

        # Create message input with theme support
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message...")
        self.message_input.setAccessibleName("message_input")
        input_area.addWidget(self.message_input)

        # Create send button with theme support
        self.send_button = QPushButton("Send")
        self.send_button.setIcon(QIcon.fromTheme("mail-send"))
        self.send_button.setAccessibleName("send_button")
        input_area.addWidget(self.send_button)

        layout.addLayout(input_area)

        # Add typing indicator
        self.typing_indicator = QLabel()
        self.typing_indicator.setAccessibleName("typing_indicator")
        self.typing_indicator.hide()
        layout.addWidget(self.typing_indicator)

        # Add progress bar for file operations
        self.progress_bar = QProgressBar()
        self.progress_bar.setAccessibleName("progress_bar")
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Initialize message history
        self.messages = []
        self._load_messages()

        # Initialize conversation handler
        from src.conversation.handler import ConversationHandler

        self.conversation_handler = ConversationHandler()

        # Connect signals
        self.new_message.connect(self._handle_new_message)

        # Initialize event loop for async operations
        self.loop = asyncio.get_event_loop()

    async def send_message(self):
        """Send a message from the input and handle streaming response"""
        message = self.message_input.text()
        if not message.strip():
            return

        # Disable input while processing
        self.message_input.setEnabled(False)
        self.send_button.setEnabled(False)

        try:
            # Clear input
            self.message_input.clear()

            # Add user message to history
            self.messages.append(
                {
                    "timestamp": datetime.datetime.now(),
                    "sender": "You",
                    "message": message,
                }
            )
            self.update_chat_history()

            if self.conversation_handler:
                # Show typing indicator
                typing_msg = {
                    "timestamp": datetime.datetime.now(),
                    "sender": "Assistant",
                    "message": "...",
                }
                self.messages.append(typing_msg)
                self.update_chat_history()

                # Stream response from conversation handler
                full_response = ""
                async for response in self.conversation_handler.handle_user_message(
                    message
                ):
                    full_response = response
                    # Update the last message with the streaming response
                    self.messages[-1]["message"] = full_response
                    self.update_chat_history()

            else:
                self.messages.append(
                    {
                        "timestamp": datetime.datetime.now(),
                        "sender": "System",
                        "message": "Error: No conversation handler connected",
                    }
                )
                self.update_chat_history()
                logging.error("No conversation handler connected")

        except Exception as e:
            self.messages.append(
                {
                    "timestamp": datetime.datetime.now(),
                    "sender": "System",
                    "message": f"Error: {str(e)}",
                }
            )
            self.update_chat_history()
            logging.error(f"Error in send_message: {str(e)}")

        finally:
            # Re-enable input
            self.message_input.setEnabled(True)
            self.send_button.setEnabled(True)

    def check_for_messages(self):
        """Check for new messages from conversation handler"""
        # This will be populated by actual conversation handler responses
        pass

    def update_chat_history(self):
        """Update the chat history display"""
        # Store scroll position
        scroll_bar = self.scroll_area.verticalScrollBar()
        was_at_bottom = scroll_bar and scroll_bar.value() >= scroll_bar.maximum() - 10

        # Clear existing messages
        for i in reversed(range(self.chat_layout.count() - 1)):
            item = self.chat_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    self.chat_layout.removeWidget(widget)
                    widget.hide()
                    widget.setParent(None)
                    widget.deleteLater()

        for msg in self.messages:
            # Create message bubble with theme support
            bubble = QFrame()
            bubble.setAccessibleName("message_bubble")
            bubble.setProperty("sender", msg["sender"].lower())

            bubble_layout = QVBoxLayout(bubble)

            # Add header with timestamp and sender
            header = QLabel(f"{msg['sender']} • {msg['timestamp'].strftime('%H:%M')}")
            header.setAccessibleName("message_timestamp")
            bubble_layout.addWidget(header)

            # Process message content
            content = msg["message"]
            if "```" in content:
                # Handle code blocks
                parts = content.split("```")
                for i, part in enumerate(parts):
                    if i % 2 == 0:
                        if part.strip():
                            # Regular text
                            text = QLabel(part)
                            text.setWordWrap(True)
                            text.setTextFormat(Qt.TextFormat.MarkdownText)
                            bubble_layout.addWidget(text)
                    else:
                        # Code block
                        try:
                            lang = part.split("\n")[0] or "python"
                            code = "\n".join(part.split("\n")[1:])
                            lexer = get_lexer_by_name(lang)
                            formatter = HtmlFormatter(style="monokai")
                            highlighted = pygments.highlight(code, lexer, formatter)

                            code_block = QTextEdit()
                            code_block.setHtml(highlighted)
                            code_block.setReadOnly(True)
                            code_block.setAccessibleName("code_block")
                            bubble_layout.addWidget(code_block)
                        except Exception as e:
                            # Fallback for unknown language
                            code_text = QLabel(part)
                            code_text.setAccessibleName("code_text")
                            bubble_layout.addWidget(code_text)
            else:
                # Regular message
                text = QLabel(content)
                text.setWordWrap(True)
                text.setTextFormat(Qt.TextFormat.MarkdownText)
                bubble_layout.addWidget(text)

            self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)

        # Update typing indicator
        if (
            self.messages
            and self.messages[-1]["sender"] == "Assistant"
            and self.messages[-1]["message"] == "..."
        ):
            self.typing_indicator.setText("Assistant is typing...")
            self.typing_indicator.show()
        else:
            self.typing_indicator.hide()

        # Restore scroll position
        if was_at_bottom and scroll_bar:
            QTimer.singleShot(0, lambda: scroll_bar.setValue(scroll_bar.maximum()))

    def _get_bubble_style(self, sender):
        """Get CSS style for message bubble based on sender"""
        is_dark = self.theme_manager and self.theme_manager.current_theme == "dark"

        if sender == "You":
            return """
                QFrame {
                    background-color: #007bff;
                    border-radius: 12px;
                    padding: 8px 12px;
                    margin: 4px 48px 4px 8px;
                }
                QLabel {
                    color: white;
                }
            """
        elif sender == "Assistant":
            return f"""
                QFrame {{
                    background-color: {('#2d2d2d' if is_dark else '#f8f9fa')};
                    border: 1px solid {('#4d4d4d' if is_dark else '#dee2e6')};
                    border-radius: 12px;
                    padding: 8px 12px;
                    margin: 4px 8px 4px 48px;
                }}
                QLabel {{
                    color: {('#ffffff' if is_dark else '#212529')};
                }}
            """
        else:  # System messages
            return f"""
                QFrame {{
                    background-color: {('#363636' if is_dark else '#e9ecef')};
                    border-radius: 12px;
                    padding: 8px 12px;
                    margin: 4px 8px;
                }}
                QLabel {{
                    color: {('#cccccc' if is_dark else '#495057')};
                    font-style: italic;
                }}
            """

    def _handle_file_button(self):
        """Handle file button click"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select File", "", "All Files (*.*)"
        )

        if file_path:
            # Show progress bar
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.progress_bar.show()

            try:
                # Simulate progress (would be real file reading progress in production)
                for i in range(101):
                    self.progress_bar.setValue(i)
                    QApplication.processEvents()

                # Add file command to chat
                self.message_input.setText(f"/add {file_path}")
                self.send_button.click()

            finally:
                # Hide progress bar
                self.progress_bar.hide()

    def closeEvent(self, event):
        """Handle window close event"""
        self._save_messages()
        event.accept()

    def _apply_theme(self):
        """Apply current theme to chat widget"""
        if self.theme_manager:
            is_dark = self.theme_manager.current_theme == "dark"

            # Update background colors based on theme
            self.setStyleSheet(
                f"""
                QWidget {{
                    background-color: {('#2d2d2d' if is_dark else '#ffffff')};
                }}
            """
            )

            # Update message colors
            self.message_colors = {
                "user": QColor("#007bff"),
                "system": QColor("#363636" if is_dark else "#f8f9fa"),
                "timestamp": QColor("#888888"),
            }

            # Refresh messages to apply new theme
            self.update_chat_history()

    def _load_messages(self):
        """Load messages from persistent storage"""
        try:
            if os.path.exists("chat_history.json"):
                with open("chat_history.json", "r") as f:
                    self.messages = json.load(f)
                    # Convert string timestamps back to datetime
                    for msg in self.messages:
                        msg["timestamp"] = datetime.datetime.fromisoformat(
                            msg["timestamp"]
                        )
        except Exception as e:
            logging.error(f"Error loading chat history: {str(e)}")

    def _save_messages(self):
        """Save messages to persistent storage"""
        try:
            # Convert datetime to string for JSON serialization
            messages_to_save = [
                {**msg, "timestamp": msg["timestamp"].isoformat()}
                for msg in self.messages
            ]
            with open("chat_history.json", "w") as f:
                json.dump(messages_to_save, f)
        except Exception as e:
            logging.error(f"Error saving chat history: {str(e)}")

    def _handle_new_message(self, message):
        """Handle incoming new messages"""
        self.messages.append(message)
        self.update_chat_history()
