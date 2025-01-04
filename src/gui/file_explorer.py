from PyQt6.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QTreeView,
    QMenu,
    QMessageBox,
    QInputDialog,
    QFileDialog,
    QApplication
)
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtGui import QFileSystemModel, QDragEnterEvent, QDropEvent, QAction
from PyQt6.QtCore import QDir, Qt, QMimeData, pyqtSignal
import os
import shutil
import logging

class FileExplorer(QWidget):
    file_opened = pyqtSignal(str)
    file_created = pyqtSignal(str)
    file_deleted = pyqtSignal(str)
    file_renamed = pyqtSignal(str, str)
    directory_changed = pyqtSignal(str)
    
    def __init__(self, theme_manager=None):
        super().__init__()
        self.theme_manager = theme_manager
        self.setWindowTitle("File Explorer")
        self.setMinimumWidth(300)
        self.current_path = QDir.currentPath()
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Create layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Create file system model
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.rootPath())
        self.model.setFilter(QDir.Filter.AllDirs | QDir.Filter.Files | QDir.Filter.NoDotAndDotDot)
        
        # Create tree view
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setRootIndex(self.model.index(self.current_path))
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setAnimated(True)
        self.tree_view.setIndentation(15)
        self.tree_view.setSortingEnabled(True)
        
        # Set up context menu
        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)
        
        # Add to layout
        layout.addWidget(self.tree_view)
        
        # Apply initial theme
        self._apply_theme()
        
        # Connect theme change signals if theme manager exists
        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self._apply_theme)
        
    def _apply_theme(self):
        """Apply current theme to the file explorer"""
        if self.theme_manager:
            theme = self.theme_manager.current_theme()
            self.setStyleSheet(f"""
                QTreeView {{
                    background-color: {theme['background']};
                    color: {theme['foreground']};
                    font-family: monospace;
                    font-size: 12px;
                    border: 1px solid {theme['border']};
                    border-radius: 4px;
                    padding: 8px;
                }}
                
                QTreeView::item:hover {{
                    background-color: {theme['hover']};
                }}
                
                QTreeView::item:selected {{
                    background-color: {theme['selection']};
                    color: {theme['selection_text']};
                }}
            """)
        else:
            self.setStyleSheet("""
                QTreeView {
                    background-color: #ffffff;
                    color: #333333;
                    font-family: sans-serif;
                    font-size: 14px;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    padding: 8px;
                }
                
                QTreeView::item:hover {
                    background-color: #f0f0f0;
                }
                
                QTreeView::item:selected {
                    background-color: #0078d7;
                    color: #ffffff;
                }
            """)
        
    def show_context_menu(self, position):
        """Show context menu for file operations"""
        index = self.tree_view.indexAt(position)
        if not index.isValid():
            return
            
        # Create menu
        menu = QMenu(self)
        
        # Add file operations
        file_ops_menu = QMenu("File Operations", self)
        menu.addMenu(file_ops_menu)
        
        open_action = QAction("Open", self)
        open_action.triggered.connect(lambda: self.open_file(index))
        file_ops_menu.addAction(open_action)
        
        new_file_action = QAction("New File", self)
        new_file_action.triggered.connect(lambda: self.create_file(index))
        file_ops_menu.addAction(new_file_action)
        
        new_folder_action = QAction("New Folder", self)
        new_folder_action.triggered.connect(lambda: self.create_folder(index))
        file_ops_menu.addAction(new_folder_action)
        
        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(lambda: self.tree_view.edit(index))
        file_ops_menu.addAction(rename_action)
        
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.delete_file(index))
        file_ops_menu.addAction(delete_action)
        
        # Add copy/paste operations
        edit_menu = QMenu("Edit", self)
        menu.addMenu(edit_menu)
        
        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(lambda: self.copy_file(index))
        edit_menu.addAction(copy_action)
        
        cut_action = QAction("Cut", self)
        cut_action.triggered.connect(lambda: self.cut_file(index))
        edit_menu.addAction(cut_action)
        
        paste_action = QAction("Paste", self)
        paste_action.triggered.connect(lambda: self.paste_file(index))
        edit_menu.addAction(paste_action)
        
        # Add separator
        menu.addSeparator()
        
        # Add properties
        properties_action = QAction("Properties", self)
        properties_action.triggered.connect(lambda: self.show_properties(index))
        menu.addAction(properties_action)
        
        # Show menu
        viewport = self.tree_view.viewport()
        if viewport:
            menu.exec(viewport.mapToGlobal(position))
        
    def open_file(self, index):
        """Handle file open operation"""
        path = self.model.filePath(index)
        if self.model.isDir(index):
            self.tree_view.setExpanded(index, not self.tree_view.isExpanded(index))
        else:
            # Emit signal or handle file opening
            print(f"Opening file: {path}")
            
    def delete_file(self, index):
        """Handle file deletion"""
        path = self.model.filePath(index)
        if self.model.remove(index):
            print(f"Deleted: {path}")
        else:
            print(f"Failed to delete: {path}")
            
    def set_root_path(self, path):
        """Set the root path for the file explorer"""
        self.tree_view.setRootIndex(self.model.index(path))
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events"""
        mime_data = event.mimeData()
        if mime_data and mime_data.hasUrls():
            event.acceptProposedAction()
            
    def dragMoveEvent(self, event: QDragEnterEvent):
        """Handle drag move events"""
        mime_data = event.mimeData()
        if mime_data and mime_data.hasUrls():
            event.acceptProposedAction()
        
    def dropEvent(self, event: QDropEvent):
        """Handle drop events"""
        mime_data = event.mimeData()
        if mime_data and mime_data.hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            
            # Get the target directory
            index = self.tree_view.indexAt(event.position().toPoint())
            target_dir = self.model.filePath(index) if index.isValid() else self.model.rootPath()
            
            # Process each dropped file
            for url in mime_data.urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    self.handle_dropped_file(file_path, target_dir)
                    
    def handle_dropped_file(self, file_path: str, target_dir: str):
        """Handle a single dropped file"""
        import os
        import shutil
        
        try:
            file_name = os.path.basename(file_path)
            destination = os.path.join(target_dir, file_name)
            
            if os.path.isdir(file_path):
                # Handle directory
                if os.path.exists(destination):
                    QMessageBox.warning(self, "Directory Exists", 
                        f"Directory '{file_name}' already exists in target location")
                else:
                    shutil.copytree(file_path, destination)
            else:
                # Handle file
                if os.path.exists(destination):
                    reply = QMessageBox.question(self, "File Exists",
                        f"File '{file_name}' already exists. Overwrite?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    
                    if reply == QMessageBox.StandardButton.Yes:
                        shutil.copy2(file_path, destination)
                else:
                    shutil.copy2(file_path, destination)
                    
            # Refresh the view by resetting root path
            current_path = self.model.rootPath()
            self.model.setRootPath('')
            self.model.setRootPath(current_path)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process file: {str(e)}")

    def create_file(self, index):
        """Create a new file in the selected directory"""
        parent_dir = self.model.filePath(index) if self.model.isDir(index) else os.path.dirname(self.model.filePath(index))
        
        file_name, ok = QInputDialog.getText(self, "New File", "Enter file name:")
        if ok and file_name:
            try:
                file_path = os.path.join(parent_dir, file_name)
                with open(file_path, 'w') as f:
                    pass
                self.file_created.emit(file_path)
                self.model.setRootPath('')  # Refresh view
                self.model.setRootPath(self.model.rootPath())
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create file: {str(e)}")

    def create_folder(self, index):
        """Create a new folder in the selected directory"""
        parent_dir = self.model.filePath(index) if self.model.isDir(index) else os.path.dirname(self.model.filePath(index))
        
        folder_name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and folder_name:
            try:
                folder_path = os.path.join(parent_dir, folder_name)
                os.makedirs(folder_path, exist_ok=True)
                self.file_created.emit(folder_path)
                self.model.setRootPath('')  # Refresh view
                self.model.setRootPath(self.model.rootPath())
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create folder: {str(e)}")

    def copy_file(self, index):
        """Copy file path to clipboard"""
        path = self.model.filePath(index)
        app = QApplication.instance() or QApplication([])
        clipboard = app.clipboard()
        if clipboard:
            clipboard.setText(path)
            QMessageBox.information(self, "Copied", f"Copied path to clipboard:\n{path}")

    def cut_file(self, index):
        """Cut file path to clipboard"""
        path = self.model.filePath(index)
        app = QApplication.instance() or QApplication([])
        clipboard = app.clipboard()
        if clipboard:
            clipboard.setText(path)
            self.cut_path = path
            QMessageBox.information(self, "Cut", f"Cut path to clipboard:\n{path}")

    def paste_file(self, index):
        """Paste file from clipboard"""
        if not hasattr(self, 'cut_path'):
            return
            
        target_dir = self.model.filePath(index) if self.model.isDir(index) else os.path.dirname(self.model.filePath(index))
        try:
            shutil.move(self.cut_path, os.path.join(target_dir, os.path.basename(self.cut_path)))
            del self.cut_path
            self.model.setRootPath('')  # Refresh view
            self.model.setRootPath(self.model.rootPath())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to paste file: {str(e)}")

    def show_properties(self, index):
        """Show file properties dialog"""
        path = self.model.filePath(index)
        stats = os.stat(path)
        
        properties = f"""
        Path: {path}
        Size: {stats.st_size} bytes
        Created: {stats.st_ctime}
        Modified: {stats.st_mtime}
        """
        
        QMessageBox.information(self, "Properties", properties)
