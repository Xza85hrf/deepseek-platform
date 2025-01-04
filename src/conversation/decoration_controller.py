from typing import Literal, List, Tuple
from dataclasses import dataclass

@dataclass
class TextRange:
    start_line: int
    end_line: int

@dataclass
class DecorationStyle:
    background_color: str
    opacity: str
    is_whole_line: bool
    border: str = ""

# Define decoration styles
faded_overlay_style = DecorationStyle(
    background_color='rgba(255, 255, 0, 0.1)',
    opacity='0.4',
    is_whole_line=True
)

active_line_style = DecorationStyle(
    background_color='rgba(255, 255, 0, 0.3)',
    opacity='1',
    is_whole_line=True,
    border='1px solid rgba(255, 255, 0, 0.5)'
)

DecorationType = Literal['fadedOverlay', 'activeLine']

class DecorationController:
    def __init__(self, decoration_type: DecorationType):
        self.decoration_type = decoration_type
        self.ranges: List[TextRange] = []

    def get_style(self) -> DecorationStyle:
        """Get the decoration style based on the current type."""
        if self.decoration_type == 'fadedOverlay':
            return faded_overlay_style
        return active_line_style

    def add_lines(self, start_index: int, num_lines: int) -> None:
        """Add lines to be decorated starting from the specified index."""
        if start_index < 0 or num_lines <= 0:
            return

        end_line = start_index + num_lines - 1
        self.ranges.append(TextRange(start_index, end_line))

    def clear(self) -> None:
        """Clear all decorations."""
        self.ranges = []

    def update_overlay_after_line(self, line: int, total_lines: int) -> None:
        """Update decorations for all lines after the specified line."""
        # Remove ranges that start at or after the current line
        self.ranges = [r for r in self.ranges if r.end_line < line]

        # Add new range for lines after the current line
        if line < total_lines - 1:
            self.ranges.append(TextRange(line + 1, total_lines - 1))

    def set_active_line(self, line: int) -> None:
        """Set decoration for a single active line."""
        self.ranges = [TextRange(line, line)]

    def get_decorated_ranges(self) -> List[Tuple[TextRange, DecorationStyle]]:
        """Get all decorated ranges with their corresponding styles."""
        style = self.get_style()
        return [(range, style) for range in self.ranges]
