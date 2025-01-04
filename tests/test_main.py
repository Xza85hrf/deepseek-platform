import pytest
from unittest.mock import patch, MagicMock, mock_open
from src.main import (
    load_prompt_instructions,
    handle_instruction_update,
    handle_instance_commands,
    show_instance_panel,
    main
)

# Test load_prompt_instructions
def test_load_prompt_instructions_valid():
    with patch("builtins.open", mock_open(read_data='{"Phase-wise Instructions": [{"Action": "test", "Confirmation": "test"}]}')):
        result = load_prompt_instructions()
        assert "test\nConfirmation: test" in result

def test_load_prompt_instructions_missing_file():
    with patch("builtins.open", side_effect=FileNotFoundError):
        result = load_prompt_instructions()
        assert result == "Default instructions"

def test_load_prompt_instructions_invalid_json():
    with patch("builtins.open", mock_open(read_data="invalid json")):
        result = load_prompt_instructions()
        assert result == "Default instructions"

# Test handle_instruction_update
def test_handle_instruction_update_success():
    mock_console = MagicMock()
    mock_console.input.side_effect = ["test improvements", "y"]
    with patch("src.main.chat_console", mock_console), \
         patch("builtins.open", mock_open(read_data='{"Improvements": []}')):
        result = handle_instruction_update("/update_instructions", [])
        assert result is True

def test_handle_instruction_update_cancel():
    mock_console = MagicMock()
    mock_console.input.side_effect = ["test improvements", "n"]
    result = handle_instruction_update("/update_instructions", [])
    assert result is True

def test_handle_instruction_update_invalid():
    result = handle_instruction_update("invalid command", [])
    assert result is False

# Test handle_instance_commands
@pytest.mark.asyncio
async def test_handle_instance_commands_create():
    mock_client = MagicMock()
    result = await handle_instance_commands("/create_instance id role key", mock_client)
    assert result is True

@pytest.mark.asyncio
async def test_handle_instance_commands_list():
    mock_client = MagicMock()
    result = await handle_instance_commands("/list_instances", mock_client)
    assert result is True

@pytest.mark.asyncio
async def test_handle_instance_commands_select():
    mock_client = MagicMock()
    result = await handle_instance_commands("/select_instance id", mock_client)
    assert result is True

@pytest.mark.asyncio
async def test_handle_instance_commands_communicate():
    mock_client = MagicMock()
    result = await handle_instance_commands("/communicate s r msg", mock_client)
    assert result is True

@pytest.mark.asyncio
async def test_handle_instance_commands_cost():
    mock_client = MagicMock()
    result = await handle_instance_commands("/cost", mock_client)
    assert result is True

@pytest.mark.asyncio
async def test_handle_instance_commands_invalid():
    mock_client = MagicMock()
    result = await handle_instance_commands("invalid command", mock_client)
    assert result is False

# Test show_instance_panel
def test_show_instance_panel_with_instances():
    mock_client = MagicMock()
    mock_client.roles = {"id1": "role1", "id2": "role2"}
    mock_console = MagicMock()
    with patch("src.main.chat_console", mock_console):
        show_instance_panel(mock_client)
        mock_console.print.assert_called()

def test_show_instance_panel_no_instances():
    mock_client = MagicMock()
    mock_client.roles = {}
    mock_console = MagicMock()
    with patch("src.main.chat_console", mock_console):
        show_instance_panel(mock_client)
        # Check if any print was called since the exact format might vary
        mock_console.print.assert_called()

# Test main initialization
@pytest.mark.asyncio
async def test_main_initialization():
    mock_console = MagicMock()
    mock_console.input.return_value = "/test/path"
    with patch("src.main.chat_console", mock_console), \
         patch("src.main.WorkspaceTracker") as mock_tracker, \
         patch("src.main.get_state_manager") as mock_state_manager:
        await main()
        mock_tracker.assert_called()
        mock_state_manager.assert_called()
