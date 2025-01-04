"""Module for monitoring and managing file diagnostics."""

from typing import List, Tuple, Dict
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from deepdiff import DeepDiff

FileDiagnostics = List[Tuple[str, List[Dict]]]

class DiagnosticsMonitor:
    """Monitors file diagnostics and provides access to error information.
    
    Attributes:
        _observer: File system observer for monitoring changes
        _last_diagnostics: Cache of last retrieved diagnostics
        _file_errors: Dictionary tracking errors per file
    """

    def __init__(self):
        """Initialize the diagnostics monitor."""
        self._observer = Observer()
        self._last_diagnostics = []
        self._file_errors = {}
        
        # Set up file system event handler
        event_handler = FileChangeHandler(self._handle_file_change)
        self._observer.schedule(event_handler, path='.', recursive=True)
        self._observer.start()

    async def get_current_diagnostics(self, should_wait_for_changes: bool) -> FileDiagnostics:
        """Get current diagnostics, optionally waiting for changes.
        
        Args:
            should_wait_for_changes: Whether to wait for diagnostics changes
            
        Returns:
            List of tuples containing file path and error diagnostics
        """
        current_diagnostics = self._get_diagnostics()
        
        if not should_wait_for_changes:
            self._last_diagnostics = current_diagnostics
            return current_diagnostics

        if not DeepDiff(self._last_diagnostics, current_diagnostics):
            self._last_diagnostics = current_diagnostics
            return current_diagnostics

        timeout = 0.3  # Default timeout in seconds when no errors exist

        # Extend timeout if existing errors are present
        if any(errors for _, errors in current_diagnostics):
            print("Existing errors detected, extending timeout", current_diagnostics)
            timeout = 10.0

        return await self._wait_for_updated_diagnostics(timeout)

    async def _wait_for_updated_diagnostics(self, timeout: float) -> FileDiagnostics:
        """Wait for diagnostics to update within the specified timeout.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            Updated diagnostics
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            current_diagnostics = self._get_diagnostics()
            if DeepDiff(self._last_diagnostics, current_diagnostics):
                self._last_diagnostics = current_diagnostics
                return current_diagnostics
            time.sleep(0.1)
        
        return self._last_diagnostics

    def _get_diagnostics(self) -> FileDiagnostics:
        """Retrieve and filter current diagnostics to only include errors.
        
        Returns:
            Filtered list of error diagnostics
        """
        return [
            (file_path, errors)
            for file_path, errors in self._file_errors.items()
            if errors
        ]

    def _handle_file_change(self, file_path: str):
        """Handle file change events and update diagnostics."""
        # Implement your error detection logic here
        # This is a placeholder - you'll need to add actual error detection
        self._file_errors[file_path] = self._detect_errors(file_path)

    def _detect_errors(self, file_path: str) -> List[Dict]:
        """Detect errors in a given file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            List of error dictionaries containing:
            - message: Error description
            - severity: Error severity level
            - line: Line number where error occurs
        """
        # Implement your error detection logic here
        # This could involve running linters, parsers, or other analysis tools
        return []  # Return empty list by default

    def dispose(self):
        """Clean up resources and stop monitoring."""
        self._observer.stop()
        self._observer.join()

class FileChangeHandler(FileSystemEventHandler):
    """Handles file system change events."""
    
    def __init__(self, callback):
        self._callback = callback
        
    def on_modified(self, event):
        if not event.is_directory:
            self._callback(event.src_path)
