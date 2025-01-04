from PyQt6.QtWidgets import (
    QWidget,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QScrollBar,
    QLabel,
    QHBoxLayout,
    QToolBar,
)
from PyQt6.QtGui import QAction, QTextCursor, QColor, QTextCharFormat
from PyQt6.QtCore import Qt, pyqtSignal
from src.gui.syntax_highlighter import CodeSyntaxHighlighter
import difflib
import logging


class CodeComparisonWidget(QWidget):
    content_changed = pyqtSignal()

    def __init__(self, theme_manager=None):
        super().__init__()
        self.theme_manager = theme_manager
        self.diff_colors = {}
        self.differences = []
        self.current_diff_index = -1
        self._init_diff_colors()

        # Create main layout
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Create header with labels
        header = QHBoxLayout()
        self.left_label = QLabel("Original")
        self.right_label = QLabel("Modified")
        header.addWidget(self.left_label)
        header.addWidget(self.right_label)
        self.main_layout.addLayout(header)

        # Create splitter for side-by-side comparison
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.splitter)

        # Create left editor
        self.left_editor = QTextEdit()
        self._setup_editor(self.left_editor)

        # Create right editor
        self.right_editor = QTextEdit()
        self._setup_editor(self.right_editor)

        # Initialize syntax highlighters
        self.left_highlighter = CodeSyntaxHighlighter(
            self.left_editor.document(), theme_manager=self.theme_manager
        )
        self.right_highlighter = CodeSyntaxHighlighter(
            self.right_editor.document(), theme_manager=self.theme_manager
        )

        # Create navigation toolbar
        self._create_navigation_toolbar()

        # Connect scroll bars
        self._connect_scrollbars()

    def _init_diff_colors(self):
        """Initialize diff colors based on current theme"""
        if self.theme_manager and self.theme_manager.is_dark_theme():
            self.diff_colors = {
                "added": QColor("#1e4620"),  # Dark green
                "removed": QColor("#4a1f1f"),  # Dark red
                "modified": QColor("#4a3c1f"),  # Dark yellow
            }
        else:
            self.diff_colors = {
                "added": QColor("#d4fadb"),  # Light green
                "removed": QColor("#ffd4d4"),  # Light red
                "modified": QColor("#fff3d4"),  # Light yellow
            }

    def _setup_editor(self, editor):
        """Configure editor settings"""
        editor.setFontFamily("Courier")
        editor.setFontPointSize(12)
        editor.textChanged.connect(self.content_changed.emit)
        self.splitter.addWidget(editor)

    def _connect_scrollbars(self):
        """Synchronize scroll bars between editors"""
        left_scroll = self.left_editor.verticalScrollBar()
        right_scroll = self.right_editor.verticalScrollBar()

        if left_scroll and right_scroll:

            def sync_scrollbars(value):
                if left_scroll:
                    left_scroll.setValue(value)
                if right_scroll:
                    right_scroll.setValue(value)

            left_scroll.valueChanged.connect(sync_scrollbars)
            right_scroll.valueChanged.connect(sync_scrollbars)
        else:
            logging.warning("Failed to initialize scrollbar synchronization")

    def _create_navigation_toolbar(self):
        """Create toolbar for navigating differences"""
        toolbar = QToolBar()
        prev_action = QAction("Previous Difference", self)
        next_action = QAction("Next Difference", self)

        prev_action.triggered.connect(self._navigate_previous_diff)
        next_action.triggered.connect(self._navigate_next_diff)

        toolbar.addAction(prev_action)
        toolbar.addAction(next_action)
        self.main_layout.addWidget(toolbar)

    def _navigate_previous_diff(self):
        """Navigate to previous difference"""
        if self.differences:
            self.current_diff_index = max(0, self.current_diff_index - 1)
            self._highlight_current_diff()

    def _navigate_next_diff(self):
        """Navigate to next difference"""
        if self.differences:
            self.current_diff_index = min(
                len(self.differences) - 1, self.current_diff_index + 1
            )
            self._highlight_current_diff()

    def _highlight_current_diff(self):
        """Highlight the current difference"""
        if 0 <= self.current_diff_index < len(self.differences):
            diff = self.differences[self.current_diff_index]
            self._highlight_diff([diff])

    def set_left_content(self, content):
        """Set content for the left editor"""
        self.left_editor.setPlainText(content)

    def set_right_content(self, content):
        """Set content for the right editor"""
        self.right_editor.setPlainText(content)

    def compare_files(self, left_content, right_content):
        """Perform diff comparison between two files"""
        try:
            self.set_left_content(left_content)
            self.set_right_content(right_content)

            # Generate diff
            differ = difflib.Differ()
            diff = list(
                differ.compare(left_content.splitlines(), right_content.splitlines())
            )

            # Apply diff highlighting
            self._highlight_diff(diff)
        except Exception as e:
            logging.error(f"Error comparing files: {str(e)}")

    def _highlight_diff(self, diff):
        """Highlight differences between files"""
        left_cursor = self.left_editor.textCursor()
        right_cursor = self.right_editor.textCursor()

        left_format = QTextCharFormat()
        right_format = QTextCharFormat()

        for i, line in enumerate(diff):
            if line.startswith("- "):
                # Removed line
                left_format.setBackground(self.diff_colors["removed"])
                self._apply_format(left_cursor, i, left_format)
            elif line.startswith("+ "):
                # Added line
                right_format.setBackground(self.diff_colors["added"])
                self._apply_format(right_cursor, i, right_format)
            elif line.startswith("? "):
                # Modified line
                left_format.setBackground(self.diff_colors["modified"])
                right_format.setBackground(self.diff_colors["modified"])
                self._apply_format(left_cursor, i, left_format)
                self._apply_format(right_cursor, i, right_format)

    def _apply_format(self, cursor, line_number, format):
        """Apply formatting to specific line"""
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        for _ in range(line_number):
            cursor.movePosition(QTextCursor.MoveOperation.Down)
        cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        cursor.mergeCharFormat(format)
