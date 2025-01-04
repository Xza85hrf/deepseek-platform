import pytest
import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.models.schemas import ToolUse, AssistantResponse
from src.tools.tool_manager import ToolManager


def test_tool_use_model():
    tool = ToolUse(name="test_tool", params={"key": "value"})
    assert tool.name == "test_tool"
    assert tool.params == {"key": "value"}


def test_assistant_response_with_tools():
    tool_use = ToolUse(name="test_tool", params={"key": "value"})
    response = AssistantResponse(assistant_reply="Test reply", tool_uses=[tool_use])

    assert response.tool_uses is not None
    assert len(response.tool_uses) == 1
    assert response.tool_uses[0].name == "test_tool"


def test_serialization_with_tools():
    tool_use = ToolUse(name="test_tool", params={"key": "value"})
    response = AssistantResponse(assistant_reply="Test reply", tool_uses=[tool_use])

    serialized = response.model_dump()
    assert "tool_uses" in serialized
    assert serialized["tool_uses"][0]["name"] == "test_tool"
    assert serialized["tool_uses"][0]["params"] == {"key": "value"}


def test_tool_manager_basic_tools():
    manager = ToolManager()
    tools = manager.get_all_tools()
    
    # Verify core basic tools exist
    assert "read_file" in tools
    assert "write_to_file" in tools
    assert "replace_in_file" in tools
    assert "execute_command" in tools
    
    # Verify tool management functions exist as basic tools
    assert "add_tool" in tools
    assert "update_tool" in tools
    assert "remove_tool" in tools
    
    # Verify basic tools are not editable
    assert not tools["read_file"].editable
    assert not tools["add_tool"].editable
    
    # Verify tool descriptions
    assert tools["add_tool"].description == "Add a new tool"
    assert tools["update_tool"].description == "Update an existing tool"
    assert tools["remove_tool"].description == "Remove an existing tool"


def test_tool_manager_extended_tools():
    manager = ToolManager()

    # Test adding a new tool
    manager.add_tool("test_tool", "lambda x: x", "Test tool")
    assert "test_tool" in manager.get_all_tools()
    assert manager.get_all_tools()["test_tool"].editable

    # Test updating a tool
    manager.update_tool("test_tool", "lambda x: x*2", "Updated test tool")
    assert manager.get_all_tools()["test_tool"].description == "Updated test tool"

    # Test removing a tool
    manager.remove_tool("test_tool")
    assert "test_tool" not in manager.get_all_tools()

def test_execute_command_tool():
    manager = ToolManager()
    tool = manager.get_tool("execute_command")
    assert tool is not None
    assert tool.description == "Execute CLI commands on the system"

def test_read_file_tool():
    manager = ToolManager()
    tool = manager.get_tool("read_file")
    assert tool is not None
    assert tool.description == "Read the contents of a file"

def test_write_to_file_tool():
    manager = ToolManager()
    tool = manager.get_tool("write_to_file")
    assert tool is not None
    assert tool.description == "Write content to a file"

def test_replace_in_file_tool():
    manager = ToolManager()
    tool = manager.get_tool("replace_in_file")
    assert tool is not None
    assert tool.description == "Make targeted edits to a file"

def test_search_files_tool():
    manager = ToolManager()
    tool = manager.get_tool("search_files")
    assert tool is not None
    assert tool.description == "Perform regex search across files"

def test_list_files_tool():
    manager = ToolManager()
    tool = manager.get_tool("list_files")
    assert tool is not None
    assert tool.description == "List files and directories"

def test_list_code_definition_names_tool():
    manager = ToolManager()
    tool = manager.get_tool("list_code_definition_names")
    assert tool is not None
    assert tool.description == "List source code definitions"

def test_ask_followup_question_tool():
    manager = ToolManager()
    tool = manager.get_tool("ask_followup_question")
    assert tool is not None
    assert tool.description == "Ask the user a follow-up question"

def test_attempt_completion_tool():
    manager = ToolManager()
    tool = manager.get_tool("attempt_completion")
    assert tool is not None
    assert tool.description == "Present the result of a task"
