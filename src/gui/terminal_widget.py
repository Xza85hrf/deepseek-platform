from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QLineEdit, 
                            QHBoxLayout, QLabel, QPushButton)
from PyQt6.QtCore import QProcess, QTextStream, Qt, pyqtSignal
from PyQt6.QtGui import QTextCursor, QTextCharFormat, QColor
import os
import sys
import json
import logging
from collections import deque

class TerminalWidget(QWidget):
    command_executed = pyqtSignal(str)
    process_started = pyqtSignal()
    process_stopped = pyqtSignal(int)
    
    def __init__(self, theme_manager=None):
        super().__init__()
        self.theme_manager = theme_manager
        self.setWindowTitle("Terminal")
        self.command_history = deque(maxlen=100)
        self.history_index = -1
        self.process_active = False
        
        # Create layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Create status bar
        self.status_bar = QHBoxLayout()
        self.status_label = QLabel("Terminal")
        self.process_status = QLabel("Inactive")
        self.status_bar.addWidget(self.status_label)
        self.status_bar.addStretch()
        self.status_bar.addWidget(self.process_status)
        layout.addLayout(self.status_bar)
        
        # Create output display
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self._apply_theme()
        layout.addWidget(self.output)
        
        # Create input area
        input_area = QHBoxLayout()
        
        # Create input line
        self.input = QLineEdit()
        self.input.setPlaceholderText("Enter command...")
        self.input.returnPressed.connect(self.execute_command)
        self.input.textChanged.connect(self.reset_history_index)
        input_area.addWidget(self.input)
        
        # Create execute button
        self.execute_button = QPushButton("Run")
        self.execute_button.clicked.connect(self.execute_command)
        input_area.addWidget(self.execute_button)
        
        layout.addLayout(input_area)
        
        # Create process
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.readyReadStandardError.connect(self.read_error)
        self.process.started.connect(self._on_process_start)
        self.process.finished.connect(self._on_process_finish)
        
        # Set up environment
        self.setup_environment()
        
    def setup_environment(self):
        """Set up terminal environment"""
        env = self.process.processEnvironment()
        
        # Set PATH and other environment variables
        if sys.platform == "win32":
            env.insert("PATH", os.environ["PATH"])
            self.process.setProgram("cmd.exe")
        else:
            env.insert("PATH", os.environ["PATH"])
            self.process.setProgram("/bin/bash")
            
        self.process.setProcessEnvironment(env)
        self.process.start()
        
    def execute_command(self):
        """Execute entered command"""
        command = self.input.text()
        self.input.clear()
        
        # Write command to process
        self.process.write((command + "\n").encode())
        
        # Echo command to output
        self.output.append(f"$ {command}")
        
    def read_output(self):
        """Read standard output from process"""
        stream = QTextStream(self.process)
        while not stream.atEnd():
            line = stream.readLine()
            self.output.append(line)
            
    def read_error(self):
        """Read standard error from process"""
        stream = QTextStream(self.process)
        while not stream.atEnd():
            line = stream.readLine()
            self.output.append(f"Error: {line}")
            
    def closeEvent(self, event):
        """Handle window close event"""
        self._cleanup_process()
        event.accept()
        
    def __del__(self):
        """Destructor to ensure process cleanup"""
        self._cleanup_process()
        
    def _cleanup_process(self):
        """Clean up the QProcess instance"""
        if self.process:
            try:
                if self.process.state() == QProcess.ProcessState.Running:
                    self.process.terminate()
                    if not self.process.waitForFinished(1000):
                        self.process.kill()
                self.process.close()
            except Exception as e:
                logging.error(f"Error cleaning up terminal process: {str(e)}")
        
    def _apply_theme(self):
        """Apply current theme to the terminal"""
        if self.theme_manager:
            theme = self.theme_manager.current_theme()
            self.output.setStyleSheet(f"""
                QTextEdit {{
                    background-color: {theme['background']};
                    color: {theme['foreground']};
                    font-family: monospace;
                    font-size: 12px;
                }}
            """)
        else:
            self.output.setStyleSheet("""
                QTextEdit {
                    background-color: black;
                    color: white;
                    font-family: monospace;
                    font-size: 12px;
                }
            """)
            
    def reset_history_index(self):
        """Reset command history navigation index"""
        self.history_index = -1
        
    def _on_process_start(self):
        """Handle process start event"""
        self.process_active = True
        self.process_status.setText("Active")
        self.process_started.emit()
        
    def _on_process_finish(self, exit_code):
        """Handle process finish event"""
        self.process_active = False
        self.process_status.setText("Inactive")
        self.process_stopped.emit(exit_code)
