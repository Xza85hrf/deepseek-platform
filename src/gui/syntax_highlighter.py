from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import QRegularExpression, pyqtSignal
import json
from pathlib import Path
import logging

class CodeSyntaxHighlighter(QSyntaxHighlighter):
    language_changed = pyqtSignal(str)
    config_loaded = pyqtSignal(bool)
    
    def __init__(self, document, theme_manager=None, language="python"):
        super().__init__(document)
        self.highlighting_rules = []
        self.language = language
        self.theme_manager = theme_manager
        self.config_path = Path(__file__).parent / "syntax_configs"
        self.available_languages = self._discover_languages()
        self.load_syntax_config()
        
    def _discover_languages(self):
        """Discover available language configurations"""
        languages = []
        if self.config_path.exists():
            for config_file in self.config_path.glob("*.json"):
                languages.append(config_file.stem)
        return languages
        
    def load_syntax_config(self):
        """Load syntax highlighting rules from JSON config"""
        self.highlighting_rules = []
        config_file = self.config_path / f"{self.language}.json"
        
        if not config_file.exists():
            logging.warning(f"Syntax config for '{self.language}' not found")
            self.config_loaded.emit(False)
            return
            
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                
            for rule in config.get('rules', []):
                fmt = QTextCharFormat()
                
                # Handle theme-aware colors
                if 'color' in rule:
                    color_value = rule['color']
                    if isinstance(color_value, dict) and self.theme_manager:
                        # Use theme-specific colors if available
                        theme = self.theme_manager.current_theme
                        color_value = color_value.get(theme, color_value.get('default', '#000000'))
                    
                    # Handle both string colors and theme-specific color dictionaries
                    if isinstance(color_value, dict) and self.theme_manager:
                        # Use theme-specific colors if available
                        theme = self.theme_manager.current_theme
                        color_value = color_value.get(theme, color_value.get('default', '#000000'))
                    
                    if isinstance(color_value, str):
                        try:
                            fmt.setForeground(QColor(color_value))
                        except:
                            logging.warning(f"Invalid color value: {color_value}")
                    
                if 'bold' in rule and rule['bold']:
                    fmt.setFontWeight(QFont.Weight.Bold)
                if 'italic' in rule and rule['italic']:
                    fmt.setFontItalic(True)
                if 'background' in rule:
                    fmt.setBackground(QColor(rule['background']))
                    
                for pattern in rule.get('patterns', []):
                    try:
                        regex = QRegularExpression(pattern)
                        if regex.isValid():
                            self.highlighting_rules.append((regex, fmt))
                        else:
                            logging.warning(f"Invalid regex pattern: {pattern}")
                    except Exception as e:
                        logging.error(f"Error compiling regex: {str(e)}")
                        
            self.config_loaded.emit(True)
        except Exception as e:
            logging.error(f"Failed to load syntax config: {str(e)}")
            self.config_loaded.emit(False)
                
    def set_language(self, language):
        """Change the syntax highlighting language"""
        if language in self.available_languages:
            self.language = language
            self.highlighting_rules = []
            self.load_syntax_config()
            self.rehighlight()
            self.language_changed.emit(language)
        else:
            logging.warning(f"Language '{language}' not supported")
            
    def get_available_languages(self):
        """Get list of available languages"""
        return self.available_languages
        
    def add_custom_language(self, language_name, config):
        """Add a custom language configuration"""
        config_file = self.config_path / f"{language_name}.json"
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            self.available_languages.append(language_name)
            return True
        except Exception as e:
            logging.error(f"Failed to add custom language: {str(e)}")
            return False

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)
