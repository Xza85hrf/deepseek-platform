import json
import os
import mimetypes
import subprocess
import re
import fnmatch
from pathlib import Path
from typing import Union, Optional, List, Dict
from pypdf import PdfReader
from docx import Document
from difflib import unified_diff

class FileTextExtractor:
    @staticmethod
    async def extract_text_from_file(file_path: Union[str, Path]) -> str:
        """Extract text from various file types including PDF, DOCX, and IPYNB."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        file_type = mimetypes.guess_type(file_path)[0]
        
        if file_type == 'application/pdf':
            return await FileTextExtractor._extract_text_from_pdf(file_path)
        elif (file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' or 
              file_path.suffix.lower() == '.docx'):
            return await FileTextExtractor._extract_text_from_docx(file_path)
        elif file_path.suffix.lower() == '.ipynb':
            return await FileTextExtractor._extract_text_from_ipynb(file_path)
        else:
            if not FileTextExtractor._is_binary(file_path):
                return await FileTextExtractor._read_text_file(file_path)
            raise ValueError(f"Cannot read text for file type: {file_path.suffix}")

    @staticmethod
    async def _extract_text_from_pdf(file_path: Path) -> str:
        from pypdf import PdfReader
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
        except PermissionError:
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to extract text from PDF: {e}")

    @staticmethod
    async def _extract_text_from_docx(file_path: Path) -> str:
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    @staticmethod
    async def _extract_text_from_ipynb(file_path: Path) -> str:
        with open(file_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
        
        extracted_text = ""
        for cell in notebook.get('cells', []):
            if cell.get('cell_type') in ('markdown', 'code') and cell.get('source'):
                extracted_text += "".join(cell['source']) + "\n"
        return extracted_text

    @staticmethod
    async def _read_text_file(file_path: Path) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError as e:
            raise RuntimeError(f"Failed to decode file {file_path}: {str(e)}")
        except OSError as e:
            if isinstance(e, PermissionError) or e.errno == 13:  # Permission denied
                raise PermissionError(f"Permission denied: {file_path}") from e
            raise RuntimeError(f"Error reading file: {e}") from e

    @staticmethod
    def _is_binary(file_path: Path) -> bool:
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\x00' in chunk
        except:
            return False

def ensure_file_in_context(file_path: Union[str, Path]) -> Path:
    """Ensure a file exists in the working context."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return path.absolute()

def read_local_file(file_path: Union[str, Path]) -> str:
    """Read content from a local file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
        
    # Check if we have read permissions
    try:
        if not os.access(path, os.R_OK):
            raise PermissionError(f"Permission denied: {path}")
            
        # Try opening the file
        with open(path, 'r', encoding='utf-8') as f:
            f.read(1)  # Try reading a single byte
            f.seek(0)  # Reset file pointer
            return f.read()
    except PermissionError as e:
        raise PermissionError(f"Permission denied: {path}") from e
    except OSError as e:
        if e.errno == 13:  # Permission denied
            raise PermissionError(f"Permission denied: {path}") from e
        raise RuntimeError(f"Error reading file: {e}") from e

def create_file(file_path: Union[str, Path], content: str, conversation_history: Optional[list] = None) -> None:
    """Create a new file with the specified content."""
    path = Path(file_path)
    
    # Validate path before attempting to create file
    try:
        # Check if parent directory exists
        if not path.parent.exists():
            raise ValueError(f"Invalid path: {path.parent}")
            
        # Check write permissions on parent directory
        if not os.access(path.parent, os.W_OK):
            raise PermissionError(f"Permission denied: {path.parent}")
            
        # Validate path components
        resolved_path = path.resolve(strict=False)
        # Check for invalid characters in path (Windows)
        if any(char in str(resolved_path) for char in ['<', '>', '"', '|', '?', '*']):
            raise ValueError(f"Invalid path: {resolved_path}")
            
        # Create parent directories if needed
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            raise PermissionError(f"Permission denied: {path.parent}") from e
            
        # Create the file
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    except PermissionError as e:
        raise PermissionError(f"Permission denied: {path}") from e
    except OSError as e:
        if e.errno == 13:  # Permission denied
            raise PermissionError(f"Permission denied: {path}") from e
        raise RuntimeError(f"Error creating file: {e}") from e

def apply_diff_edit(file_path: Union[str, Path], diff_content: str, original_snippet: Optional[str] = None, conversation_history: Optional[list] = None) -> None:
    """Apply diff changes to a file using unified diff format."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
        
    with open(path, 'r', encoding='utf-8') as f:
        original_lines = f.readlines()
        
    diff_lines = diff_content.splitlines()
    if not diff_lines[0].startswith('---') or not diff_lines[1].startswith('+++'):
        raise ValueError("Invalid unified diff format")
        
    changes = []
    for line in diff_lines[2:]:
        if line.startswith('@@'):
            match = re.match(r'@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@', line)
            if not match:
                raise ValueError("Invalid diff hunk header")
            old_start = int(match.group(1))
            old_len = int(match.group(2)) if match.group(2) else 1
            new_start = int(match.group(3))
            new_len = int(match.group(4)) if match.group(4) else 1
            changes.append((old_start, old_len, new_start, new_len))
        elif line.startswith('+'):
            changes.append(('add', line[1:]))
        elif line.startswith('-'):
            changes.append(('remove', line[1:]))
        elif line.startswith(' '):
            changes.append(('keep', line[1:]))
        else:
            raise ValueError(f"Invalid diff line: {line}")
            
    new_lines = []
    current_line = 0
    for change in changes:
        if isinstance(change, tuple):
            old_start, old_len, new_start, new_len = change
            while current_line < old_start - 1:
                new_lines.append(original_lines[current_line])
                current_line += 1
            current_line += old_len
        elif change[0] == 'add':
            new_lines.append(change[1] + '\n')
        elif change[0] == 'remove':
            current_line += 1
        elif change[0] == 'keep':
            new_lines.append(change[1] + '\n')
            current_line += 1
            
    while current_line < len(original_lines):
        new_lines.append(original_lines[current_line])
        current_line += 1
        
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

def execute_system_command(command: str, requires_approval: bool = True) -> str:
    """Execute a system command and return the output."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            text=True,
            capture_output=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Command failed with error: {e.stderr}")

def search_files_regex(directory: str, pattern: str, file_pattern: str = "*") -> List[Dict[str, str]]:
    """Search files in a directory using regex pattern."""
    results = []
    compiled_pattern = re.compile(pattern)
    for root, _, files in os.walk(directory):
        for file in files:
            if not fnmatch.fnmatch(file, file_pattern):
                continue
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if compiled_pattern.search(line):
                            results.append({
                                'file': file_path,
                                'line': line_num,
                                'match': line.strip()
                            })
            except UnicodeDecodeError:
                continue
    return results

def list_directory_contents(directory: str, recursive: bool = False) -> List[str]:
    """List contents of a directory."""
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    if recursive:
        return [os.path.join(root, f) for root, _, files in os.walk(directory) for f in files]
    else:
        return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

def list_code_definitions(directory: str) -> List[Dict[str, str]]:
    """List code definitions in source files."""
    definitions = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Simple regex to find class and function definitions
                        class_matches = re.finditer(r'class\s+(\w+)', content)
                        func_matches = re.finditer(r'def\s+(\w+)', content)
                        for match in class_matches:
                            definitions.append({
                                'file': file_path,
                                'type': 'class',
                                'name': match.group(1)
                            })
                        for match in func_matches:
                            definitions.append({
                                'file': file_path,
                                'type': 'function',
                                'name': match.group(1)
                            })
                except UnicodeDecodeError:
                    continue
    return definitions

def ask_user_question(question: str) -> str:
    """Ask the user a question and return the response."""
    # This would be handled by the conversation system
    return f"User response to: {question}"

def complete_task(result: str, command: Optional[str] = None) -> None:
    """Complete a task and optionally execute a command."""
    # This would be handled by the conversation system
    if command:
        execute_system_command(command)
