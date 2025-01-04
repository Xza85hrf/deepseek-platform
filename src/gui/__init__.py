import sys
from PyQt6.QtWidgets import QApplication

# Initialize QApplication at package level
if QApplication.instance() is None:
    app = QApplication(sys.argv)
else:
    app = QApplication.instance()

# Type annotation to help static type checking
assert isinstance(app, QApplication)