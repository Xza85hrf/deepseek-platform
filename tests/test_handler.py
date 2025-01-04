import pytest
from unittest.mock import patch, MagicMock
from src.conversation.handler import try_handle_add_command, show_diff_table
from src.models.schemas import FileToEdit

@pytest.fixture
def mock_console():
    with patch('src.conversation.handler.status_console') as mock_status, \
         patch('src.conversation.handler.chat_console') as mock_chat:
        yield mock_status, mock_chat

def test_try_handle_add_command_valid_file(mock_console):
    """Test adding a valid file to conversation"""
    mock_status, _ = mock_console
    mock_read = MagicMock(return_value="file content")
    
    with patch('src.conversation.handler.read_local_file', mock_read):
        history = []
        result = try_handle_add_command("/add test.txt", history)
        
        assert result is True
        assert len(history) == 1
        assert "Content of file 'test.txt'" in history[0]['content']
        mock_status.print.assert_called_with(
            "[green]✓[/green] Added file '[cyan]test.txt[/cyan]' to conversation.\n"
        )

def test_try_handle_add_command_invalid_file(mock_console):
    """Test adding an invalid file to conversation"""
    mock_status, _ = mock_console
    mock_read = MagicMock(side_effect=OSError("File not found"))
    
    with patch('src.conversation.handler.read_local_file', mock_read):
        history = []
        result = try_handle_add_command("/add missing.txt", history)
        
        assert result is True
        assert len(history) == 0
        mock_status.print.assert_called_with(
            "[red]✗[/red] Could not add file '[cyan]missing.txt[/cyan]': File not found\n",
            style="red"
        )

def test_try_handle_add_command_invalid_input(mock_console):
    """Test invalid /add command format"""
    mock_status, _ = mock_console
    history = []
    result = try_handle_add_command("invalid command", history)
    
    assert result is False
    assert len(history) == 0
    mock_status.print.assert_not_called()

def test_show_diff_table_empty():
    """Test showing diff table with no edits"""
    with patch('src.conversation.handler.chat_console') as mock_console:
        show_diff_table([])
        mock_console.print.assert_not_called()

def test_show_diff_table_single_edit():
    """Test showing diff table with single edit"""
    with patch('src.conversation.handler.chat_console') as mock_console:
        edits = [
            FileToEdit(
                path="test.txt",
                original_snippet="old",
                new_snippet="new"
            )
        ]
        show_diff_table(edits)
        
        mock_console.print.assert_called_once()
        table = mock_console.print.call_args[0][0]
        assert table.row_count == 1
        assert table.columns[0].header == "File Path"
        assert table.columns[1].header == "Original"
        assert table.columns[2].header == "New"
        assert table.title == "Proposed Edits"
        assert table.show_header is True
        assert table.show_lines is True

def test_show_diff_table_multiple_edits():
    """Test showing diff table with multiple edits"""
    with patch('src.conversation.handler.chat_console') as mock_console:
        edits = [
            FileToEdit(
                path="test1.txt",
                original_snippet="old1",
                new_snippet="new1"
            ),
            FileToEdit(
                path="test2.txt",
                original_snippet="old2",
                new_snippet="new2"
            )
        ]
        show_diff_table(edits)
        
        mock_console.print.assert_called_once()
        table = mock_console.print.call_args[0][0]
        assert table.row_count == 2
        assert table.columns[0].header == "File Path"
        assert table.columns[1].header == "Original"
        assert table.columns[2].header == "New"

def test_show_diff_table_column_styles():
    """Test table column styles are correctly applied"""
    with patch('src.conversation.handler.chat_console') as mock_console:
        edits = [
            FileToEdit(
                path="test.txt",
                original_snippet="old",
                new_snippet="new"
            )
        ]
        show_diff_table(edits)
        
        mock_console.print.assert_called_once()
        table = mock_console.print.call_args[0][0]
        assert table.columns[0].style == "cyan"
        assert table.columns[1].style == "red"
        assert table.columns[2].style == "green"
