import sys
import asyncio
import datetime
from qasync import QEventLoop, asyncSlot
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QHBoxLayout,
    QTextEdit,
    QComboBox,
    QSplitter,
    QLabel,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtGui import QIcon, QFont

# Import our initialized QApplication instance
from . import app
from .file_explorer import FileExplorer
from .code_comparison import CodeComparisonWidget
from .chat_widget import ChatWidget
from .theme_manager import ThemeManager
from .syntax_highlighter import CodeSyntaxHighlighter
from .terminal_widget import TerminalWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DeepSeek GUI")
        # Set initial size based on screen
        screen = QApplication.primaryScreen()
        if screen:
            screen_size = screen.size()
            self.resize(int(screen_size.width() * 0.75), int(screen_size.height() * 0.75))
        else:
            self.resize(1200, 800)
        self.setMinimumSize(800, 600)

        # Create main layout with responsive design
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        # Apply Material Design spacing system
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Create responsive grid layout system
        self.grid_size = 8  # Base grid unit (8dp)
        
        # Create responsive file explorer with Material elevation
        self.file_explorer_container = QWidget()
        self.file_explorer_container.setAccessibleName("file_explorer_container")
        self.file_explorer_container.setMinimumWidth(self.grid_size * 25)  # 200dp
        self.file_explorer_container.setMaximumWidth(self.grid_size * 50)  # 400dp
        self.file_explorer_container.setProperty("elevation", 1)  # Material elevation level
        
        file_explorer_layout = QVBoxLayout(self.file_explorer_container)
        file_explorer_layout.setContentsMargins(self.grid_size, self.grid_size,
                                              self.grid_size, self.grid_size)
        
        self.file_explorer = FileExplorer()
        self.file_explorer.setAccessibleName("file_explorer")
        file_explorer_layout.addWidget(self.file_explorer)
        
        # Create main content area
        self.main_content = QWidget()
        self.main_content.setAccessibleName("main_content")
        self.main_content_layout = QVBoxLayout(self.main_content)
        self.main_content_layout.setContentsMargins(0, 0, 0, 0)
        self.main_content_layout.setSpacing(0)

        # Add widgets to main layout
        self.main_layout.addWidget(self.file_explorer_container)
        self.main_layout.addWidget(self.main_content)

        # Create Material Design toolbar with elevation
        toolbar = QWidget()
        toolbar.setAccessibleName("toolbar")
        toolbar.setProperty("elevation", 2)  # Material elevation level
        toolbar.setFixedHeight(self.grid_size * 8)  # 64dp standard height
        toolbar_layout = QHBoxLayout(toolbar)
        
        # Apply Material Design spacing
        toolbar_layout.setContentsMargins(self.grid_size * 3, 0,  # 24dp horizontal
                                        self.grid_size * 3, 0)
        toolbar_layout.setSpacing(self.grid_size * 2)  # 16dp between sections
        self.main_content_layout.addWidget(toolbar)

        # Initialize theme manager with transition support
        self.theme_manager = ThemeManager(app)
        self.theme_manager.setProperty("enableTransitions", True)

        # Create left toolbar section with Material spacing
        left_section = QWidget()
        left_section.setAccessibleName("toolbar_left_section")
        left_layout = QHBoxLayout(left_section)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(self.grid_size)  # 8dp between items

        # Add theme toggle button with Material touch target
        self.theme_button = QPushButton()
        self.theme_button.setAccessibleName("theme_button")
        self.theme_button.setProperty("flat", True)
        self.theme_button.setProperty("hasRipple", True)  # Enable ripple effect
        self.theme_button.setIcon(QIcon("icons/theme.png"))
        self.theme_button.setIconSize(QSize(24, 24))  # Material icon size
        self.theme_button.setFixedSize(48, 48)  # 48dp touch target
        self.theme_button.setToolTip("Toggle Dark/Light Theme")
        self.theme_button.clicked.connect(self.theme_manager.toggle_theme)
        self.theme_button.setProperty("role", "switch")  # ARIA role
        self.theme_button.setProperty("ariaLabel", "Theme switcher")
        left_layout.addWidget(self.theme_button)

        # Add language selection with Material styling
        self.language_combo = QComboBox()
        self.language_combo.setAccessibleName("language_selector")
        self.language_combo.addItems(["Python", "JavaScript", "TypeScript", "HTML", "CSS", "Markdown"])
        self.language_combo.setToolTip("Select Language")
        self.language_combo.setMinimumWidth(self.grid_size * 15)  # 120dp
        self.language_combo.setProperty("hasRipple", True)  # Enable ripple effect
        self.language_combo.setProperty("role", "combobox")  # ARIA role
        self.language_combo.setProperty("ariaLabel", "Language selection")
        left_layout.addWidget(self.language_combo)

        toolbar_layout.addWidget(left_section)
        toolbar_layout.addStretch(1)

        # Create center toolbar section with Material spacing
        center_section = QWidget()
        center_section.setAccessibleName("toolbar_center_section")
        center_layout = QHBoxLayout(center_section)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(self.grid_size)  # 8dp spacing

        # Add comparison mode button with Material touch target
        self.compare_button = QPushButton()
        self.compare_button.setAccessibleName("compare_button")
        self.compare_button.setProperty("flat", True)
        self.compare_button.setProperty("hasRipple", True)  # Enable ripple effect
        self.compare_button.setIcon(QIcon("icons/compare.png"))
        self.compare_button.setIconSize(QSize(24, 24))  # Material icon size
        self.compare_button.setFixedSize(48, 48)  # 48dp touch target
        self.compare_button.setToolTip("Toggle Comparison Mode")
        self.compare_button.setCheckable(True)
        self.compare_button.setProperty("role", "switch")  # ARIA role
        self.compare_button.setProperty("ariaLabel", "Compare mode")
        self.compare_button.clicked.connect(self.toggle_comparison_mode)
        center_layout.addWidget(self.compare_button)

        toolbar_layout.addWidget(center_section)
        toolbar_layout.addStretch(1)

        # Create right toolbar section with Material spacing
        right_section = QWidget()
        right_section.setAccessibleName("toolbar_right_section")
        right_layout = QHBoxLayout(right_section)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(self.grid_size)  # 8dp spacing

        # Add chat button with Material touch target
        self.chat_button = QPushButton()
        self.chat_button.setAccessibleName("chat_button")
        self.chat_button.setProperty("flat", True)
        self.chat_button.setProperty("hasRipple", True)  # Enable ripple effect
        self.chat_button.setIcon(QIcon("icons/chat.png"))
        self.chat_button.setIconSize(QSize(24, 24))  # Material icon size
        self.chat_button.setFixedSize(48, 48)  # 48dp touch target
        self.chat_button.setToolTip("Toggle Chat")
        self.chat_button.setCheckable(True)
        self.chat_button.setProperty("role", "switch")  # ARIA role
        self.chat_button.setProperty("ariaLabel", "Chat panel")
        self.chat_button.clicked.connect(self.toggle_chat)
        right_layout.addWidget(self.chat_button)

        # Add terminal button with Material touch target
        self.terminal_button = QPushButton()
        self.terminal_button.setAccessibleName("terminal_button")
        self.terminal_button.setProperty("flat", True)
        self.terminal_button.setProperty("hasRipple", True)  # Enable ripple effect
        self.terminal_button.setIcon(QIcon("icons/terminal.png"))
        self.terminal_button.setIconSize(QSize(24, 24))  # Material icon size
        self.terminal_button.setFixedSize(48, 48)  # 48dp touch target
        self.terminal_button.setToolTip("Toggle Terminal")
        self.terminal_button.setCheckable(True)
        self.terminal_button.setProperty("role", "switch")  # ARIA role
        self.terminal_button.setProperty("ariaLabel", "Terminal panel")
        self.terminal_button.clicked.connect(self.toggle_terminal)
        right_layout.addWidget(self.terminal_button)

        # Add status label with Material typography
        self.status_label = QLabel()
        self.status_label.setAccessibleName("status_label")
        self.status_label.setProperty("typography", "caption")  # Material typography style
        self.status_label.setProperty("ariaLive", "polite")  # ARIA live region
        right_layout.addWidget(self.status_label)

        toolbar_layout.addWidget(right_section)

        # Create main editor container with Material elevation
        self.editor_container = QWidget()
        self.editor_container.setAccessibleName("editor_container")
        self.editor_container.setProperty("elevation", 2)  # Material elevation level
        editor_layout = QVBoxLayout(self.editor_container)
        editor_layout.setContentsMargins(self.grid_size * 2, self.grid_size * 2,  # 16dp padding
                                       self.grid_size * 2, self.grid_size * 2)
        editor_layout.setSpacing(self.grid_size)  # 8dp spacing
        self.main_content_layout.addWidget(self.editor_container)

        # Create code editor with Material Design styling
        self.code_editor = QTextEdit()
        self.code_editor.setAccessibleName("code_editor")
        editor_font = QFont("Cascadia Code", 14)
        editor_font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        self.code_editor.setFont(editor_font)
        self.code_editor.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.code_editor.setAcceptRichText(False)
        self.code_editor.setProperty("elevation", 1)  # Material elevation level
        self.code_editor.setProperty("role", "textbox")  # ARIA role
        self.code_editor.setProperty("ariaLabel", "Code editor")
        self.code_editor.setProperty("ariaMultiLine", "true")
        
        # Set up tab size and indentation
        metrics = self.code_editor.fontMetrics()
        self.code_editor.setTabStopDistance(metrics.horizontalAdvance(' ') * 4)
        editor_layout.addWidget(self.code_editor)

        # Initialize syntax highlighter with enhanced theme support
        self.highlighter = CodeSyntaxHighlighter(
            self.code_editor.document(),
            theme_manager=self.theme_manager
        )
        self.highlighter.setProperty("enableTransitions", True)  # Enable color transitions

        # Create bottom panel with Material Design elevation
        self.bottom_panel = QWidget()
        self.bottom_panel.setAccessibleName("bottom_panel")
        self.bottom_panel.setProperty("elevation", 3)  # Higher elevation for overlay
        self.bottom_panel.setVisible(False)
        self.bottom_panel.setProperty("role", "complementary")  # ARIA role
        self.bottom_panel.setProperty("ariaLabel", "Terminal and chat panel")
        
        # Add smooth height transition
        self.bottom_panel_animation = QPropertyAnimation(self.bottom_panel, b"maximumHeight")
        self.bottom_panel_animation.setDuration(200)  # 200ms animation
        self.bottom_panel_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Set up Material Design layout
        self.bottom_panel_layout = QVBoxLayout(self.bottom_panel)
        self.bottom_panel_layout.setContentsMargins(
            self.grid_size * 2, self.grid_size,  # 16dp horizontal, 8dp vertical
            self.grid_size * 2, self.grid_size
        )
        self.bottom_panel_layout.setSpacing(self.grid_size)  # 8dp spacing
        editor_layout.addWidget(self.bottom_panel)

        # Initialize panel widgets with proper setup
        self.terminal_widget = None
        self.chat_widget = None
        
        # Set up editor container with Material responsive design
        self.editor_container.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.editor_container.setProperty("elevation", 2)  # Base elevation level

        # Initialize chat widget
        try:
            self.chat_widget = ChatWidget(self.theme_manager)
            if self.chat_widget:
                self.chat_widget.message_sent.connect(self.handle_chat_message)
                # Connect to conversation handler
                from src.conversation.handler import ConversationHandler
                self.chat_widget.conversation_handler = ConversationHandler()

                # Connect message sending
                self.chat_widget.send_button.clicked.connect(self.handle_send_message)
                self.chat_widget.message_input.returnPressed.connect(
                    self.handle_send_message
                )
            else:
                print("Error: Failed to initialize chat widget")
                self.status_label.setText("Error: Chat initialization failed")
        except Exception as e:
            print(f"Error initializing chat widget: {str(e)}")
            self.status_label.setText("Error: Chat initialization failed")
            self.chat_widget = None

    def toggle_comparison_mode(self, checked):
        """Toggle between normal and comparison mode with smooth transition"""
        if checked:
            # Save current content
            current_content = self.code_editor.toPlainText()

            # Create and show comparison widget
            self.comparison_widget = CodeComparisonWidget()
            self.comparison_widget.setAccessibleName("comparison_widget")
            self.comparison_widget.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding
            )
            self.comparison_widget.set_left_content(current_content)

            # Replace code editor with comparison widget in editor container
            editor_layout = self.editor_container.layout()
            if isinstance(editor_layout, QVBoxLayout):
                editor_layout.replaceWidget(self.code_editor, self.comparison_widget)
            self.code_editor.hide()
            self.status_label.setText("Comparison Mode: Active")

            # Hide bottom panel when comparison mode is active
            self.bottom_panel.setVisible(False)
            if self.terminal_widget:
                self.terminal_widget.setVisible(False)
            if self.chat_widget:
                self.chat_widget.setVisible(False)
            self.terminal_button.setChecked(False)
            self.chat_button.setChecked(False)
        else:
            if self.comparison_widget:
                # Get content from left editor
                content = self.comparison_widget.left_editor.toPlainText()

                # Restore code editor
                editor_layout = self.editor_container.layout()
                if isinstance(editor_layout, QVBoxLayout):
                    editor_layout.replaceWidget(self.comparison_widget, self.code_editor)
                self.code_editor.setPlainText(content)
                self.code_editor.show()

                # Clean up comparison widget
                self.comparison_widget.deleteLater()
                self.comparison_widget = None
                self.status_label.setText("")

    def toggle_terminal(self, checked):
        """Toggle terminal window visibility with Material Design transitions"""
        if checked:
            # Prepare bottom panel animation
            self.bottom_panel.setVisible(True)
            target_height = int(self.height() * 0.3)  # 30% of window height
            self.bottom_panel_animation.setStartValue(0)
            self.bottom_panel_animation.setEndValue(target_height)

            # Create terminal widget if needed
            if not self.terminal_widget:
                self.terminal_widget = TerminalWidget()
                self.terminal_widget.setAccessibleName("terminal")
                self.terminal_widget.setProperty("elevation", 2)  # Material elevation
                self.terminal_widget.setProperty("role", "terminal")  # ARIA role
                self.terminal_widget.setProperty("ariaLabel", "Terminal window")
                self.terminal_widget.setSizePolicy(
                    QSizePolicy.Policy.Expanding,
                    QSizePolicy.Policy.Expanding
                )
                self.bottom_panel_layout.addWidget(self.terminal_widget)
            
            # Show terminal with transition
            self.terminal_widget.setVisible(True)
            self.bottom_panel_animation.start()
            self.status_label.setText("Terminal: Active")
        else:
            # Animate panel closing
            self.bottom_panel_animation.setStartValue(self.bottom_panel.height())
            self.bottom_panel_animation.setEndValue(0)
            
            if self.terminal_widget:
                self.terminal_widget.setVisible(False)
                self.status_label.setText("")

            # Hide bottom panel with animation if no other widgets visible
            if not self.chat_widget or not self.chat_widget.isVisible():
                self.bottom_panel_animation.finished.connect(
                    lambda: self.bottom_panel.setVisible(False)
                )
                self.bottom_panel_animation.start()

    @asyncSlot()
    async def handle_send_message(self):
        """Handle message sending with async support"""
        if not self.chat_widget or not hasattr(self.chat_widget, "send_message"):
            print("Error: Chat widget not properly initialized")
            self.status_label.setText("Error: Chat not initialized")
            return

        try:
            # Send message using qasync event loop
            await self.chat_widget.send_message()
            QApplication.processEvents()  # Keep UI responsive
        except Exception as e:
            print(f"Error sending message: {str(e)}")
            self.status_label.setText(f"Error: {str(e)}")

    def toggle_chat(self, checked):
        """Toggle chat window visibility with Material Design transitions"""
        if checked and not self.chat_widget:
            try:
                # Initialize chat widget with Material Design styling
                self.chat_widget = ChatWidget(self.theme_manager)
                self.chat_widget.setAccessibleName("chat_widget")
                self.chat_widget.setProperty("elevation", 2)  # Material elevation
                self.chat_widget.setProperty("role", "complementary")  # ARIA role
                self.chat_widget.setProperty("ariaLabel", "Chat interface")
                self.chat_widget.setSizePolicy(
                    QSizePolicy.Policy.Expanding,
                    QSizePolicy.Policy.Expanding
                )
                
                # Connect signals
                self.chat_widget.message_sent.connect(self.handle_chat_message)
                from src.conversation.handler import ConversationHandler
                self.chat_widget.conversation_handler = ConversationHandler()
                self.chat_widget.send_button.clicked.connect(self.handle_send_message)
                self.chat_widget.message_input.returnPressed.connect(self.handle_send_message)
                
                # Add to bottom panel with Material spacing
                self.bottom_panel_layout.addWidget(self.chat_widget)
            except Exception as e:
                print(f"Error initializing chat widget: {str(e)}")
                self.status_label.setText("Error: Chat initialization failed")
                self.chat_button.setChecked(False)
                return

        if self.chat_widget:
            if checked:
                # Prepare bottom panel animation
                self.bottom_panel.setVisible(True)
                target_height = int(self.height() * 0.4)  # 40% of window height for chat
                self.bottom_panel_animation.setStartValue(0)
                self.bottom_panel_animation.setEndValue(target_height)
                
                # Show chat with transition
                self.chat_widget.setVisible(True)
                self.bottom_panel_animation.start()
                self.status_label.setText("Chat: Active")
            else:
                # Animate panel closing
                self.bottom_panel_animation.setStartValue(self.bottom_panel.height())
                self.bottom_panel_animation.setEndValue(0)
                
                self.chat_widget.setVisible(False)
                self.status_label.setText("")

                # Hide bottom panel with animation if no other widgets visible
                if not self.terminal_widget or not self.terminal_widget.isVisible():
                    self.bottom_panel_animation.finished.connect(
                        lambda: self.bottom_panel.setVisible(False)
                    )
                    self.bottom_panel_animation.start()

    @asyncSlot()
    async def handle_chat_message(self, message):
        """Handle incoming chat messages"""
        if not self.chat_widget:
            print("Error: Chat widget not initialized")
            self.status_label.setText("Error: Chat not initialized")
            return

        try:
            # Process message with qasync event loop

            # Add user message
            self.chat_widget.messages.append({
                "timestamp": datetime.datetime.now(),
                "sender": "You",
                "message": message,
            })
            self.chat_widget.update_chat_history()

            # Process commands
            if message.startswith("/add "):
                file_path = message[len("/add "):].strip()
                try:
                    with open(file_path, "r") as f:
                        content = f.read()
                        self.chat_widget.messages.append({
                            "timestamp": datetime.datetime.now(),
                            "sender": "System",
                            "message": f"Added file '{file_path}' to conversation",
                        })
                        self.status_label.setText(f"Added file: {file_path}")
                except Exception as e:
                    self.chat_widget.messages.append({
                        "timestamp": datetime.datetime.now(),
                        "sender": "System",
                        "message": f"Could not add file: {str(e)}",
                    })
                    self.status_label.setText(f"Error: Could not add file")
                self.chat_widget.update_chat_history()
                return

            # Send message to backend and get streaming response
            try:
                # Show typing indicator
                self.chat_widget.messages.append({
                    "timestamp": datetime.datetime.now(),
                    "sender": "Assistant",
                    "message": "...",
                })
                self.chat_widget.update_chat_history()
                self.status_label.setText("Assistant is typing...")

                # Stream response from conversation handler
                full_response = ""
                async for response_chunk in self.chat_widget.conversation_handler.handle_user_message(message):
                    full_response = response_chunk
                    # Update the last message with the streaming response
                    self.chat_widget.messages[-1]["message"] = full_response
                    self.chat_widget.update_chat_history()
                    # Process Qt events to keep UI responsive
                    QApplication.processEvents()

                # Update status based on final response type
                if full_response:
                    if "```" in full_response:
                        self.status_label.setText("Code block received")
                    elif "table" in full_response.lower():
                        self.status_label.setText("Table data received")
                    else:
                        self.status_label.setText("Response received")
                else:
                    self.status_label.setText("No response from assistant")
            except Exception as e:
                error_msg = f"Error getting response: {str(e)}"
                self.chat_widget.messages.append({
                    "timestamp": datetime.datetime.now(),
                    "sender": "System",
                    "message": error_msg,
                })
                self.chat_widget.update_chat_history()
                self.status_label.setText("Error: Failed to get response")
        except Exception as e:
            print(f"Error handling chat message: {str(e)}")
            self.status_label.setText(f"Error: {str(e)}")

# Initialize QApplication at module level
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

def run_application():
    """Initialize and run the application"""
    try:
        # Set up asyncio policy for Windows
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        # Set up qasync event loop
        loop = QEventLoop(app)
        asyncio.set_event_loop(loop)

        # Create and show main window
        window = MainWindow()
        window.show()

        # Run event loop
        with loop:
            loop.run_forever()

    except Exception as e:
        print(f"Error running application: {str(e)}")
        raise

# Entry point
if __name__ == "__main__":
    sys.exit(run_application())
else:
    run_application()  # When imported as a module
