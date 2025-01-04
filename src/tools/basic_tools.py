from typing import Dict, Any


class BasicTool:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.editable = False


# Basic tools that cannot be modified
BASIC_TOOLS = {
    "read_file": BasicTool(name="read_file", description="Read the contents of a file"),
    "write_to_file": BasicTool(
        name="write_to_file", description="Write content to a file"
    ),
    "replace_in_file": BasicTool(
        name="replace_in_file", description="Make targeted edits to a file"
    ),
    "execute_command": BasicTool(
        name="execute_command", description="Execute CLI commands on the system"
    ),
    "search_files": BasicTool(
        name="search_files", description="Perform regex search across files"
    ),
    "list_files": BasicTool(
        name="list_files", description="List files and directories"
    ),
    "list_code_definition_names": BasicTool(
        name="list_code_definition_names", description="List source code definitions"
    ),
    "ask_followup_question": BasicTool(
        name="ask_followup_question", description="Ask the user a follow-up question"
    ),
    "attempt_completion": BasicTool(
        name="attempt_completion", description="Present the result of a task"
    ),
    "execute_code": BasicTool(name="execute_code", description="Execute code snippets"),
    "format_code": BasicTool(
        name="format_code", description="Format code according to standards"
    ),
    "lint_code": BasicTool(
        name="lint_code", description="Check code quality and style"
    ),
    "manage_dependencies": BasicTool(
        name="manage_dependencies", description="Manage project dependencies"
    ),
    "run_tests": BasicTool(name="run_tests", description="Run project tests"),
    "add_tool": BasicTool(name="add_tool", description="Add a new extended tool"),
    "update_tool": BasicTool(
        name="update_tool", description="Update an existing extended tool"
    ),
    "remove_tool": BasicTool(name="remove_tool", description="Remove an extended tool"),
}
