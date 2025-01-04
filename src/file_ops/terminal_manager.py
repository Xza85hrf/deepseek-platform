"""
Enhanced Terminal Manager Module

Provides advanced terminal process management with event handling, shell integration,
and output processing similar to VSCode's terminal implementation.

Classes:
    TerminalProcess: Manages terminal processes with event handling and output processing
    TerminalManager: Manages multiple terminal processes and command execution

Events:
    line: Emitted when a complete line of output is received
    continue: Emitted when process can continue execution
    completed: Emitted when process completes
    error: Emitted when an error occurs
    no_shell_integration: Emitted when shell integration is not available

Example Usage:
    manager = TerminalManager()
    
    async def run_example():
        process = await manager.run_command("ls -la", "/path/to/dir")
        
        @process.on('line')
        def handle_line(line: str):
            print(f"Output: {line}")
            
        await process.wait()
        print(process.get_unretrieved_output())
    
    asyncio.run(run_example())
"""

import asyncio
import re
import subprocess
import threading
from typing import Dict, List, Optional, Set, Union, Callable, Any
from pathlib import Path
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TerminalInfo:
    """Metadata for a terminal process"""
    terminal_id: int
    busy: bool = False
    last_command: str = ""
    process: Optional['TerminalProcess'] = None

class TerminalEventType(Enum):
    LINE = auto()
    CONTINUE = auto()
    COMPLETED = auto()
    ERROR = auto()
    NO_SHELL_INTEGRATION = auto()


@dataclass
class TerminalEvent:
    type: TerminalEventType
    data: Any = None


class TerminalProcess:
    """
    Manages terminal processes with event handling and advanced output processing.

    Attributes:
        _process (Optional[subprocess.Popen]): The underlying process
        _output_buffer (str): Buffer for storing process output
        _last_retrieved_index (int): Index of last retrieved output
        _is_hot (bool): Indicates if process is actively running
        _hot_timer (Optional[asyncio.TimerHandle]): Timer for hot state
        _event_handlers (Dict[TerminalEventType, List[Callable]]): Event handlers
        _lock (threading.Lock): Thread synchronization lock
    """

    PROCESS_HOT_TIMEOUT_NORMAL = 2.0
    PROCESS_HOT_TIMEOUT_COMPILING = 15.0

    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._output_buffer = ""
        self._last_retrieved_index = 0
        self._is_hot = False
        self._hot_timer: Optional[asyncio.TimerHandle] = None
        self._event_handlers: Dict[TerminalEventType, List[Callable]] = {
            event_type: [] for event_type in TerminalEventType
        }
        self._lock = threading.Lock()
        self._loop = asyncio.get_event_loop()

    def on(self, event_type: TerminalEventType, handler: Callable):
        """Register an event handler."""
        self._event_handlers[event_type].append(handler)
        return self

    def _emit(self, event: TerminalEvent):
        """Emit an event to all registered handlers."""
        for handler in self._event_handlers[event.type]:
            handler(event.data)

    async def run(self, command: str, cwd: Optional[str] = None):
        """Execute a command in the terminal."""
        self._process = subprocess.Popen(
            command,
            shell=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        self._is_hot = True
        self._set_hot_timer(self.PROCESS_HOT_TIMEOUT_NORMAL)

        # Start output reading in background
        threading.Thread(target=self._read_output, daemon=True).start()

    def _read_output(self):
        """Read and process output from the process."""
        if self._process and self._process.stdout:
            for data in self._process.stdout:
                with self._lock:
                    self._process_output(data)

            self._emit(TerminalEvent(TerminalEventType.COMPLETED))
            self._emit(TerminalEvent(TerminalEventType.CONTINUE))
            self._is_hot = False

    def _process_output(self, data: str):
        """Process and emit output data."""
        # Strip ANSI codes
        data = self._strip_ansi(data)

        # Handle VSCode shell integration sequences
        data = self._handle_vscode_sequences(data)

        # Update buffer and emit lines
        self._output_buffer += data
        self._emit_if_eol(data)

        # Update hot state based on content
        self._update_hot_state(data)

    def _strip_ansi(self, text: str) -> str:
        """Remove ANSI escape sequences from text."""
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return ansi_escape.sub("", text)

    def _handle_vscode_sequences(self, data: str) -> str:
        """Handle VSCode shell integration sequences."""
        # Remove VSCode custom sequences
        vscode_sequence_regex = re.compile(r"\x1b\]633;[^\x07]*\x07")
        return vscode_sequence_regex.sub("", data)

    def _emit_if_eol(self, chunk: str):
        """Emit complete lines from the buffer."""
        self._buffer += chunk
        while (line_end_index := self._buffer.find("\n")) != -1:
            line = self._buffer[:line_end_index].rstrip("\r")
            self._emit(TerminalEvent(TerminalEventType.LINE, line))
            self._buffer = self._buffer[line_end_index + 1 :]
            self._last_retrieved_index = len(self._output_buffer) - len(self._buffer)

    def _update_hot_state(self, data: str):
        """Update hot state based on output content."""
        compiling_markers = [
            "compiling",
            "building",
            "bundling",
            "transpiling",
            "generating",
            "starting",
        ]
        marker_nullifiers = [
            "compiled",
            "success",
            "finish",
            "complete",
            "succeed",
            "done",
            "end",
            "stop",
            "exit",
            "terminate",
            "error",
            "fail",
        ]

        is_compiling = any(
            marker in data.lower() for marker in compiling_markers
        ) and not any(nullifier in data.lower() for nullifier in marker_nullifiers)

        timeout = (
            self.PROCESS_HOT_TIMEOUT_COMPILING
            if is_compiling
            else self.PROCESS_HOT_TIMEOUT_NORMAL
        )

        self._set_hot_timer(timeout)

    def _set_hot_timer(self, timeout: float):
        """Set or reset the hot state timer."""
        if self._hot_timer:
            self._hot_timer.cancel()

        self._hot_timer = self._loop.call_later(
            timeout, lambda: setattr(self, "_is_hot", False)
        )

    def get_unretrieved_output(self) -> str:
        """Retrieve all unretrieved output."""
        with self._lock:
            unretrieved = self._output_buffer[self._last_retrieved_index :]
            self._last_retrieved_index = len(self._output_buffer)
            return self._remove_last_line_artifacts(unretrieved)

    def _remove_last_line_artifacts(self, output: str) -> str:
        """Remove terminal artifacts from output."""
        lines = output.rstrip().split("\n")
        if lines:
            lines[-1] = re.sub(r"[%$#>]\s*$", "", lines[-1])
        return "\n".join(lines)

    async def wait(self):
        """Wait for process completion."""
        while self._process and self._process.poll() is None:
            await asyncio.sleep(0.1)

    def continue_execution(self):
        """Allow process to continue in background."""
        self._emit(TerminalEvent(TerminalEventType.CONTINUE))

    @property
    def is_hot(self) -> bool:
        """Check if process is still running."""
        return self._is_hot


class TerminalManager:
    """
    Manages multiple terminal processes and command execution.
    
    Attributes:
        _processes (Dict[int, TerminalProcess]): Active terminal processes
        _terminals (Dict[int, TerminalInfo]): Terminal metadata
        _next_id (int): Next terminal ID
    """
    
    def __init__(self):
        self._processes: Dict[int, TerminalProcess] = {}
        self._terminals: Dict[int, TerminalInfo] = {}
        self._next_id = 0
        
    def create_terminal(self, cwd: Optional[str] = None) -> TerminalInfo:
        """Create a new terminal with metadata tracking"""
        terminal_id = self._next_id
        self._next_id += 1
        
        terminal_info = TerminalInfo(
            terminal_id=terminal_id,
            process=None,
            busy=False
        )
        self._terminals[terminal_id] = terminal_info
        return terminal_info
        
    def get_terminal(self, terminal_id: int) -> Optional[TerminalInfo]:
        """Get terminal info if it exists and is active"""
        if terminal_id not in self._terminals:
            return None
            
        terminal_info = self._terminals[terminal_id]
        if terminal_info.process and not terminal_info.process.is_hot:
            self.remove_terminal(terminal_id)
            return None
            
        return terminal_info
        
    def update_terminal(self, terminal_id: int, updates: dict):
        """Update terminal metadata"""
        terminal_info = self.get_terminal(terminal_id)
        if terminal_info:
            for key, value in updates.items():
                setattr(terminal_info, key, value)
                
    def remove_terminal(self, terminal_id: int):
        """Remove a terminal from tracking"""
        if terminal_id in self._terminals:
            del self._terminals[terminal_id]
        if terminal_id in self._processes:
            process = self._processes[terminal_id]
            if process._process:
                process._process.terminate()
            del self._processes[terminal_id]
            
    def get_all_terminals(self) -> List[TerminalInfo]:
        """Get all active terminals"""
        active_terminals = []
        for terminal_id in list(self._terminals.keys()):
            terminal_info = self.get_terminal(terminal_id)
            if terminal_info:
                active_terminals.append(terminal_info)
        return active_terminals

    async def run_command(
        self, command: str, cwd: Optional[str] = None
    ) -> TerminalProcess:
        """Execute a command in a new terminal process."""
        process = TerminalProcess()
        terminal_id = self._next_id
        self._next_id += 1

        self._processes[terminal_id] = process
        await process.run(command, cwd)
        return process

    def get_unretrieved_output(self, terminal_id: int) -> str:
        """Retrieve unretrieved output from a terminal."""
        if terminal_id in self._processes:
            return self._processes[terminal_id].get_unretrieved_output()
        return ""

    def is_process_hot(self, terminal_id: int) -> bool:
        """Check if a process is still running."""
        if terminal_id in self._processes:
            return self._processes[terminal_id].is_hot
        return False

    def dispose_all(self):
        """Clean up all terminal processes."""
        for process in self._processes.values():
            if process._process:
                process._process.terminate()
        self._processes.clear()
