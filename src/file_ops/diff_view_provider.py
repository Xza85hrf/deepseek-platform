import re
from pathlib import Path
from typing import Optional, List, Tuple, Dict
import difflib
from rich.console import Console
from .operations import ensure_file_in_context, read_local_file, apply_diff_edit
from ..conversation.decoration_controller import DecorationController

# Initialize Rich consoles for different outputs
status_console = Console(stderr=True)  # For status messages
chat_console = Console()  # For chat messages

class DiffViewProvider:
    def __init__(self, cwd: str):
        self.cwd = Path(cwd)
        self.edit_type: Optional[str] = None  # "create" or "modify"
        self.is_editing = False
        self.original_content: Optional[str] = None
        self.created_dirs: List[Path] = []
        self.document_was_open = False
        self.rel_path: Optional[Path] = None
        self.new_content: Optional[str] = None
        self.active_diff_editor: Optional[Dict] = None
        self.faded_overlay_controller: Optional[DecorationController] = None
        self.active_line_controller: Optional[DecorationController] = None
        self.streamed_lines: List[str] = []
        self.pre_diagnostics: List[Tuple[str, List[Dict]]] = []

    async def open(self, rel_path: str) -> None:
        """Open a file in diff view mode."""
        self.rel_path = Path(rel_path)
        file_exists = self.edit_type == "modify"
        absolute_path = self.cwd / self.rel_path
        self.is_editing = True

        # Get original content
        if file_exists:
            self.original_content = read_local_file(str(absolute_path))
        else:
            self.original_content = ""

        # Create directories if needed
        self.created_dirs = self._create_directories_for_file(absolute_path)

        # Create empty file if it doesn't exist
        if not file_exists:
            with open(absolute_path, "w") as f:
                f.write("")

        # Open diff view
        self.active_diff_editor = await self._open_diff_view()
        self.faded_overlay_controller = DecorationController("fadedOverlay")
        self.active_line_controller = DecorationController("activeLine")
        self.streamed_lines = []

    async def update(self, accumulated_content: str, is_final: bool) -> None:
        """Update the diff view with new content."""
        if not self.rel_path or not self.active_line_controller or not self.faded_overlay_controller:
            raise ValueError("Required values not set")

        self.new_content = accumulated_content
        accumulated_lines = accumulated_content.split("\n")
        if not is_final:
            accumulated_lines.pop()  # Remove last partial line

        diff_lines = accumulated_lines[len(self.streamed_lines):]

        # Apply updates to the diff view
        for i, line in enumerate(diff_lines):
            current_line = len(self.streamed_lines) + i
            self._update_diff_content(current_line, accumulated_lines)
            self.active_line_controller.set_active_line(current_line)
            self.faded_overlay_controller.update_overlay_after_line(current_line, len(accumulated_lines))
            self._scroll_to_line(current_line)

        self.streamed_lines = accumulated_lines

        if is_final:
            self._finalize_update()

    async def save_changes(self) -> Dict[str, Optional[str]]:
        """Save changes made in the diff view."""
        if not self.rel_path or not self.new_content or not self.active_diff_editor:
            return {
                "new_problems_message": None,
                "user_edits": None,
                "final_content": None
            }

        absolute_path = self.cwd / self.rel_path
        updated_content = self.new_content

        # Save the file
        with open(absolute_path, "w") as f:
            f.write(updated_content)

        # Get post-save diagnostics
        post_diagnostics = self._get_current_diagnostics()
        new_problems = self._compare_diagnostics(self.pre_diagnostics, post_diagnostics)

        return {
            "new_problems_message": new_problems,
            "user_edits": None,  # TODO: Implement user edits detection
            "final_content": updated_content
        }

    async def revert_changes(self) -> None:
        """Revert changes made in the diff view."""
        if not self.rel_path:
            return

        absolute_path = self.cwd / self.rel_path
        file_exists = self.edit_type == "modify"

        if not file_exists:
            # Delete the file and created directories
            absolute_path.unlink()
            for dir_path in reversed(self.created_dirs):
                if dir_path.exists() and not any(dir_path.iterdir()):
                    dir_path.rmdir()
        else:
            # Revert to original content
            with open(absolute_path, "w") as f:
                f.write(self.original_content or "")

        await self.reset()

    async def reset(self) -> None:
        """Reset the diff view provider to initial state."""
        self.edit_type = None
        self.is_editing = False
        self.original_content = None
        self.created_dirs = []
        self.document_was_open = False
        self.active_diff_editor = None
        self.faded_overlay_controller = None
        self.active_line_controller = None
        self.streamed_lines = []
        self.pre_diagnostics = []

    def _create_directories_for_file(self, file_path: Path) -> List[Path]:
        """Create directories needed for a file and return created directories."""
        created = []
        for parent in file_path.parents:
            if not parent.exists():
                parent.mkdir()
                created.append(parent)
        return created

    async def _open_diff_view(self) -> Dict:
        """Open a diff view for the file."""
        # TODO: Implement actual diff view opening
        if not self.rel_path:
            raise ValueError("Relative path not set")
        return {
            "document": {
                "uri": str(self.cwd / self.rel_path) if self.rel_path else "",
                "line_count": len(self.original_content.split("\n")) if self.original_content else 0
            }
        }

    def _update_diff_content(self, current_line: int, accumulated_lines: List[str]) -> None:
        """Update the diff content up to the current line."""
        # TODO: Implement actual diff content update
        pass

    def _scroll_to_line(self, line: int) -> None:
        """Scroll the diff view to the specified line."""
        # TODO: Implement scrolling
        pass

    def _finalize_update(self) -> None:
        """Finalize the update operation."""
        if self.faded_overlay_controller:
            self.faded_overlay_controller.clear()
        if self.active_line_controller:
            self.active_line_controller.clear()

    def _get_current_diagnostics(self) -> List[Tuple[str, List[Dict]]]:
        """Get current diagnostics for open files."""
        # TODO: Implement diagnostics retrieval
        return []

    def _compare_diagnostics(self, pre: List[Tuple[str, List[Dict]]], post: List[Tuple[str, List[Dict]]]) -> str:
        """Compare diagnostics before and after changes."""
        # TODO: Implement diagnostics comparison
        return ""

    def _detect_code_omission(self, original_content: str, new_content: str) -> bool:
        """
        Detects potential AI-generated code omissions in the given file content.
        
        Args:
            original_content: The original content of the file
            new_content: The new content of the file to check
            
        Returns:
            bool: True if a potential omission is detected, False otherwise
        """
        original_lines = original_content.split("\n")
        new_lines = new_content.split("\n")
        omission_keywords = {"remain", "remains", "unchanged", "rest", "previous", "existing", "..."}

        comment_patterns = [
            r"^\s*#",  # Python single-line comment
            r"^\s*\"\"\"",  # Python multi-line comment opening
            r"^\s*'''",  # Python multi-line comment opening
        ]

        for line in new_lines:
            if any(re.match(pattern, line) for pattern in comment_patterns):
                words = set(word.lower() for word in line.split())
                if omission_keywords.intersection(words):
                    if line not in original_lines:
                        return True
        return False

    def _log_omission_warning(self, original_content: str, new_content: str) -> None:
        """
        Logs a warning if a potential code omission is detected.
        
        Args:
            original_content: The original content of the file
            new_content: The new content of the file to check
        """
        if self._detect_code_omission(original_content, new_content):
            warning_msg = (
                "Potential code truncation detected. This happens when the AI reaches its max output limit.\n"
                "For more information, see: https://github.com/cline/cline/wiki/Troubleshooting-%E2%80%90-Cline-Deleting-Code-with-%22Rest-of-Code-Here%22-Comments"
            )
            status_console.print(f"[yellow]Warning: {warning_msg}[/yellow]")
