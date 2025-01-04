from typing import Dict, Any, Optional
from dataclasses import dataclass
import hashlib
import json
from datetime import datetime
from .basic_tools import BASIC_TOOLS
from .extended_tools import EXTENDED_TOOLS, ExtendedTool

@dataclass
class BasicTool:
    func: Any
    description: str
    editable: bool = False
from src.file_ops.operations import (
    read_local_file,
    apply_diff_edit,
    create_file,
    ensure_file_in_context,
    execute_system_command,
    search_files_regex,
    list_directory_contents,
    list_code_definitions,
    ask_user_question,
    complete_task
)


@dataclass
class ToolVersion:
    version: str
    timestamp: str
    checksum: str
    description: str


class ToolManager:
    def __init__(self):
        # Map basic tools to their implementations with descriptions
        self.tools = {
            "read_file": BasicTool(read_local_file, "Read the contents of a file"),
            "write_to_file": BasicTool(create_file, "Write content to a file"),
            "replace_in_file": BasicTool(apply_diff_edit, "Make targeted edits to a file"),
            "ensure_file_in_context": BasicTool(ensure_file_in_context, "Ensure file is in context"),
            "execute_command": BasicTool(execute_system_command, "Execute CLI commands on the system"),
            "search_files": BasicTool(search_files_regex, "Perform regex search across files"),
            "list_files": BasicTool(list_directory_contents, "List files and directories"),
            "list_code_definition_names": BasicTool(list_code_definitions, "List source code definitions"),
            "ask_followup_question": BasicTool(ask_user_question, "Ask the user a follow-up question"),
            "attempt_completion": BasicTool(complete_task, "Present the result of a task"),
            "add_tool": BasicTool(self.add_tool, "Add a new tool"),
            "update_tool": BasicTool(self.update_tool, "Update an existing tool"),
            "remove_tool": BasicTool(self.remove_tool, "Remove an existing tool"),
            **EXTENDED_TOOLS
        }
        
        # Add descriptions to tool functions
        read_local_file.description = "Read the contents of a file"
        create_file.description = "Write content to a file"
        apply_diff_edit.description = "Make targeted edits to a file"
        execute_system_command.description = "Execute CLI commands on the system"
        search_files_regex.description = "Perform regex search across files"
        list_directory_contents.description = "List files and directories"
        list_code_definitions.description = "List source code definitions"
        ask_user_question.description = "Ask the user a follow-up question"
        complete_task.description = "Present the result of a task"
        self.tool_versions: Dict[str, list[ToolVersion]] = {}
        self.load_tool_versions()

    def get_tool(self, name: str) -> Optional[Any]:
        """Get a tool by name with error handling"""
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' not found")
        return self.tools.get(name)

    def get_all_tools(self) -> Dict[str, Any]:
        """Get all available tools"""
        return self.tools

    def add_tool(self, name: str, description: str, code: str) -> None:
        """Add a new extended tool with validation"""
        if name in self.tools:
            raise ValueError(f"Tool '{name}' already exists")

        # Validate tool code
        self._validate_tool_code(code)

        # Create new tool
        new_tool = ExtendedTool(name=name, description=description)
        self.tools[name] = new_tool
        EXTENDED_TOOLS[name] = new_tool

        # Track version
        self._create_new_version(name, code, description)

    def update_tool(self, name: str, code: str, description: str) -> None:
        """Update an existing tool with validation"""
        if name not in EXTENDED_TOOLS:
            raise ValueError(f"Tool '{name}' is not an extended tool")

        # Validate tool code
        self._validate_tool_code(code)

        # Update tool
        self.tools[name].description = description
        EXTENDED_TOOLS[name].description = description

        # Track version
        self._create_new_version(name, code, description)

    def remove_tool(self, name: str) -> None:
        """Remove an extended tool"""
        if name not in EXTENDED_TOOLS:
            raise ValueError(f"Tool '{name}' is not an extended tool")

        del self.tools[name]
        del EXTENDED_TOOLS[name]
        if name in self.tool_versions:
            del self.tool_versions[name]

    def get_tool_versions(self, name: str) -> list[ToolVersion]:
        """Get version history for a tool"""
        return self.tool_versions.get(name, [])

    def _create_new_version(self, name: str, code: str, description: str) -> None:
        """Create a new version entry for a tool"""
        checksum = hashlib.md5(code.encode()).hexdigest()
        version = ToolVersion(
            version=str(len(self.tool_versions.get(name, [])) + 1),
            timestamp=datetime.now().isoformat(),
            checksum=checksum,
            description=description,
        )
        if name not in self.tool_versions:
            self.tool_versions[name] = []
        self.tool_versions[name].append(version)

    def _validate_tool_code(self, code: str) -> None:
        """Validate tool code for security and syntax"""
        # Basic security checks
        if "import os" in code or "import sys" in code:
            raise ValueError("Tool code cannot import restricted modules")
        if "subprocess" in code:
            raise ValueError("Tool code cannot use subprocess")

    def load_tool_versions(self) -> None:
        """Load tool versions from storage"""
        # TODO: Implement persistent storage
        pass

    def save_tool_versions(self) -> None:
        """Save tool versions to storage"""
        # TODO: Implement persistent storage
        pass

    def generate_documentation(self) -> str:
        """Generate comprehensive documentation for all tools"""
        docs = "# Tool Documentation\n\n"

        # Add usage guidelines
        docs += "## Tool Usage Guidelines\n"
        docs += "### When to Use Existing Tools\n"
        docs += "- Use existing tools when they directly match your task requirements\n"
        docs += "- Prefer basic tools for core functionality as they are more stable\n"
        docs += "- Check tool descriptions to find the most appropriate tool\n\n"

        docs += "### When to Create New Tools\n"
        docs += "- When you need functionality not provided by existing tools\n"
        docs += "- When you need to encapsulate complex or repetitive operations\n"
        docs += "- When you need to integrate with external systems or APIs\n\n"

        docs += "### How to Create New Tools\n"
        docs += (
            "1. Use `add_tool` method with name, description, and implementation code\n"
        )
        docs += "2. Ensure code follows security guidelines (no OS/sys imports)\n"
        docs += "3. Test the tool thoroughly before using in production\n"
        docs += "4. Document the tool's purpose and usage\n\n"

        docs += "### Tool Management Best Practices\n"
        docs += "- Use version control to track tool changes\n"
        docs += "- Update documentation when modifying tools\n"
        docs += "- Remove unused tools to maintain system cleanliness\n\n"

        # Add individual tool documentation
        docs += "## Available Tools\n"
        for name, tool in self.tools.items():
            docs += f"### {name}\n"
            docs += f"- Description: {tool.description}\n"
            if name in self.tool_versions:
                docs += f"- Versions: {len(self.tool_versions[name])}\n"
            if name in EXTENDED_TOOLS:
                docs += "- Type: Extended (modifiable)\n"
            else:
                docs += "- Type: Basic (immutable)\n"
            docs += "\n"

        return docs
