import pytest
from src.conversation.parse_assistant_message import parse_assistant_message, ToolUse

def test_parse_tool_use():
    # Test a simple tool use message
    message = '''<read_file>
<path>src/main.py</path>
</read_file>'''
    
    result = parse_assistant_message(message)
    
    assert len(result) == 1
    assert isinstance(result[0], ToolUse)
    assert result[0].name == 'read_file'
    assert result[0].params == {'path': 'src/main.py'}
    assert result[0].partial is False

def test_parse_multiple_tool_uses():
    # Test multiple tool uses in one message
    message = '''<read_file>
<path>src/main.py</path>
</read_file>
<execute_command>
<command>npm run dev</command>
<requires_approval>false</requires_approval>
</execute_command>'''
    
    result = parse_assistant_message(message)
    
    assert len(result) == 2
    assert isinstance(result[0], ToolUse)
    assert result[0].name == 'read_file'
    assert result[0].params == {'path': 'src/main.py'}
    
    assert isinstance(result[1], ToolUse)
    assert result[1].name == 'execute_command'
    assert result[1].params == {
        'command': 'npm run dev',
        'requires_approval': 'false'
    }

def test_parse_incomplete_tool_use():
    # Test incomplete tool use
    message = '''<read_file>
<path>src/main.py'''
    
    result = parse_assistant_message(message)
    
    assert len(result) == 1
    assert result[0].type == 'text'
    assert result[0].partial is True

def test_parse_mixed_content():
    # Test mixed text and tool uses
    message = '''Here is my response:
<read_file>
<path>src/main.py</path>
</read_file>
Please review the file contents.'''
    
    result = parse_assistant_message(message)
    
    assert len(result) == 3
    assert result[0].type == 'text'
    assert isinstance(result[1], ToolUse)
    assert result[2].type == 'text'

def test_parse_empty_params():
    # Test tool use with empty parameters
    message = '''<read_file>
<path></path>
</read_file>'''
    
    result = parse_assistant_message(message)
    
    assert len(result) == 1
    assert result[0].type == 'text'  # Should fall back to text since params are empty

if __name__ == '__main__':
    pytest.main()
