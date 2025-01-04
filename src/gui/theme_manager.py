from PyQt6.QtCore import QFile, QTextStream, pyqtSignal, QObject
from pathlib import Path
import logging

class ThemeManager(QObject):
    theme_changed = pyqtSignal(str)  # Signal emitted when theme changes
    
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.current_theme = "dark"
        self.theme_path = Path(__file__).parent / "themes"
        self.available_themes = self._discover_themes()
        self.load_theme()
        
    def _discover_themes(self):
        """Discover available themes in the themes directory"""
        themes = {}
        if self.theme_path.exists():
            for theme_file in self.theme_path.glob("*.css"):
                theme_name = theme_file.stem
                themes[theme_name] = theme_file
        return themes
        
    def load_theme(self):
        """Load the current theme from CSS file and force update"""
        if self.current_theme not in self.available_themes:
            logging.warning(f"Theme '{self.current_theme}' not found")
            return
            
        theme_file = self.available_themes[self.current_theme]
        try:
            file = QFile(str(theme_file))
            if file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
                stream = QTextStream(file)
                stylesheet = stream.readAll()
                file.close()
                
                # Apply stylesheet
                self.app.setStyleSheet("")  # Clear existing stylesheet
                self.app.setStyleSheet(stylesheet)  # Apply new stylesheet
                
                # Force style update on all widgets
                for widget in self.app.allWidgets():
                    widget.style().unpolish(widget)
                    widget.style().polish(widget)
                    widget.update()
                
                self.theme_changed.emit(self.current_theme)
        except Exception as e:
            logging.error(f"Failed to load theme: {str(e)}")
                
    def toggle_theme(self):
        """Switch between dark and light themes"""
        new_theme = "light" if self.current_theme == "dark" else "dark"
        self.set_theme(new_theme)
        
    def set_theme(self, theme_name):
        """Set a specific theme by name"""
        if theme_name in self.available_themes:
            self.current_theme = theme_name
            self.load_theme()
        else:
            logging.warning(f"Theme '{theme_name}' not available")
            
    def get_available_themes(self):
        """Get list of available theme names"""
        return list(self.available_themes.keys())
        
    def add_custom_theme(self, theme_name, css_content):
        """Add a custom theme programmatically"""
        theme_file = self.theme_path / f"{theme_name}.css"
        try:
            with open(theme_file, 'w') as f:
                f.write(css_content)
            self.available_themes[theme_name] = theme_file
            return True
        except Exception as e:
            logging.error(f"Failed to add custom theme: {str(e)}")
            return False
