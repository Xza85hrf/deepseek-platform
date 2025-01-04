import os
import sys
import weakref
from typing import Set, List, Optional, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class WorkspaceTracker:
    def __init__(self, cwd: str, update_callback: Callable[[List[str]], None]):
        """Initialize the WorkspaceTracker with a directory path and update callback."""
        self.update_callback = update_callback
        self.observer = Observer()
        self.file_paths: Set[str] = set()
        self.cwd = self._validate_workspace(cwd)
        # Initialize file paths before starting observer
        self.initialize_file_paths()
        self._register_listeners()

    def _validate_workspace(self, path: str) -> str:
        """Validate and normalize the workspace path."""
        if not path:
            raise ValueError("Workspace path cannot be empty")
            
        # Convert to absolute path
        abs_path = os.path.abspath(path)
        
        # Ensure the path exists and is a directory
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Workspace directory does not exist: {abs_path}")
        if not os.path.isdir(abs_path):
            raise NotADirectoryError(f"Path is not a directory: {abs_path}")
            
        return abs_path

    def is_within_workspace(self, path: str) -> bool:
        """Check if a path is within the workspace directory."""
        try:
            abs_path = os.path.abspath(path)
            return os.path.commonpath([abs_path, self.cwd]) == self.cwd
        except:
            return False

    def initialize_file_paths(self):
        """Initialize the set of file paths in the workspace."""
        if not self.cwd:
            return
            
        files = self._list_files(self.cwd, recursive=True)
        for file in files:
            self.file_paths.add(self._normalize_file_path(file))
        self._workspace_did_update()

    def _register_listeners(self):
        """Register event listeners for file changes using watchdog."""
        try:
            event_handler = FileChangeHandler(self)
            self.observer.schedule(event_handler, self.cwd, recursive=True)
            self.observer.start()
        except Exception as e:
            print(f"Warning: Failed to start file watcher: {e}")
            # Continue even if file watching fails
            pass

    def _on_files_created(self, file_path: str):
        """Handle file creation events."""
        self._add_file_path(file_path)
        self._workspace_did_update()

    def _on_files_deleted(self, file_path: str):
        """Handle file deletion events."""
        if self._remove_file_path(file_path):
            self._workspace_did_update()

    def _on_files_renamed(self, old_path: str, new_path: str):
        """Handle file rename events."""
        self._remove_file_path(old_path)
        self._add_file_path(new_path)
        self._workspace_did_update()

    def _workspace_did_update(self):
        """Notify the callback when the workspace changes."""
        if not self.cwd:
            return
            
        self.update_callback([
            self._get_relative_path(file)
            for file in self.file_paths
        ])

    def _normalize_file_path(self, file_path: str) -> str:
        """Normalize a file path relative to the workspace."""
        resolved_path = os.path.join(self.cwd, file_path) if self.cwd else file_path
        return resolved_path + os.sep if file_path.endswith(os.sep) else resolved_path

    def _add_file_path(self, file_path: str) -> str:
        """Add a file path to the set, handling directories appropriately."""
        normalized_path = self._normalize_file_path(file_path)
        try:
            is_directory = os.path.isdir(normalized_path)
            path_with_slash = normalized_path + os.sep if is_directory and not normalized_path.endswith(os.sep) else normalized_path
            self.file_paths.add(path_with_slash)
            return path_with_slash
        except:
            # If stat fails, assume it's a file
            self.file_paths.add(normalized_path)
            return normalized_path

    def _remove_file_path(self, file_path: str) -> bool:
        """Remove a file path from the set."""
        normalized_path = self._normalize_file_path(file_path)
        removed1 = self.file_paths.discard(normalized_path)
        removed2 = self.file_paths.discard(normalized_path + os.sep)
        return bool(removed1 or removed2)

    def _get_relative_path(self, file_path: str) -> str:
        """Get the relative path of a file within the workspace."""
        relative_path = os.path.relpath(file_path, self.cwd)
        return relative_path.replace(os.sep, "/") + "/" if file_path.endswith(os.sep) else relative_path.replace(os.sep, "/")

    def dispose(self):
        """Clean up resources and event listeners."""
        self.observer.stop()
        self.observer.join()

    def get_python_env_path(self) -> Optional[str]:
        """
        Get the path of the active Python environment.
        
        Returns:
            Optional[str]: Path to the Python environment if found, None otherwise
        """
        # Check for virtual environment
        if 'VIRTUAL_ENV' in os.environ:
            return os.environ['VIRTUAL_ENV']
            
        # Check for conda environment
        if 'CONDA_PREFIX' in os.environ:
            return os.environ['CONDA_PREFIX']
            
        # Fall back to the current Python interpreter path
        python_path = sys.executable
        if python_path:
            return os.path.dirname(os.path.dirname(python_path))
            
        return None

    def _list_files(self, directory: str, recursive: bool = False) -> List[str]:
        """List files in a directory, optionally recursively."""
        try:
            if recursive:
                result = []
                for root, _, files in os.walk(directory):
                    for file in files:
                        result.append(os.path.join(root, file))
                return result
            else:
                return [os.path.join(directory, f) for f in os.listdir(directory) 
                       if os.path.isfile(os.path.join(directory, f))]
        except Exception:
            return []

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, tracker):
        self.tracker = tracker

    def on_created(self, event):
        self.tracker._on_files_created(event.src_path)

    def on_deleted(self, event):
        self.tracker._on_files_deleted(event.src_path)

    def on_moved(self, event):
        self.tracker._on_files_renamed(event.src_path, event.dest_path)
