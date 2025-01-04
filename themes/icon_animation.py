import time
import threading
from pathlib import Path
from rich.console import Console

# Add project root to Python path
import sys

project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from src.utils.state_manager import EngineerState, get_state_manager

# Initialize console for status messages
status_console = Console(stderr=True)


class IconAnimation:
    def __init__(self):
        self.state_manager = get_state_manager()
        self.running = False
        self.animation_thread = None
        self.icons = {
            EngineerState.IDLE: "🐋",
            EngineerState.THINKING: "🤔",
            EngineerState.WORKING: "💻",
            EngineerState.ERROR: "❌",
        }

    def start(self):
        """Start the icon animation thread"""
        if self.running:
            return

        self.running = True
        self.animation_thread = threading.Thread(target=self._animate)
        self.animation_thread.daemon = True
        self.animation_thread.start()

    def stop(self):
        """Stop the icon animation thread"""
        self.running = False
        if self.animation_thread:
            self.animation_thread.join()

    def _animate(self):
        """Animation loop that updates the icon based on state"""
        last_state = None
        while self.running:
            current_state = self.state_manager.state
            # Only update if state has changed
            if current_state != last_state:
                icon = self.icons.get(current_state, "🐋")
                status_console.print(f"{icon}", style="bold blue")
                last_state = current_state
            time.sleep(0.1)


def get_icon_animation() -> IconAnimation:
    """Get the singleton icon animation instance"""
    if not hasattr(get_icon_animation, "instance"):
        get_icon_animation.instance = IconAnimation()
    return get_icon_animation.instance


if __name__ == "__main__":
    animation = get_icon_animation()
    animation.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        animation.stop()
