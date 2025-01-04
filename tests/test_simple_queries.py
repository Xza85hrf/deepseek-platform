import pytest
from src.conversation.simple_queries import SimpleQueryHandler
from src.models.schemas import AssistantResponse

def test_handle_exact_query():
    """Test handling of exact query matches."""
    response = SimpleQueryHandler.handle_query("who are you")
    assert isinstance(response, AssistantResponse)
    assert "DeepSeek Engineer" in response.assistant_reply
    assert not response.files_to_create
    assert not response.files_to_edit
    assert not response.tool_uses

def test_handle_query_with_punctuation():
    """Test handling of queries with punctuation."""
    response = SimpleQueryHandler.handle_query("who are you?")
    assert isinstance(response, AssistantResponse)
    assert "DeepSeek Engineer" in response.assistant_reply

def test_handle_partial_query():
    """Test handling of partial query matches."""
    response = SimpleQueryHandler.handle_query("what version are you running")
    assert isinstance(response, AssistantResponse)
    assert "version" in response.assistant_reply.lower()

def test_handle_unknown_query():
    """Test handling of unknown queries."""
    response = SimpleQueryHandler.handle_query("unknown query")
    assert response is None

def test_is_simple_query():
    """Test query detection."""
    assert SimpleQueryHandler.is_simple_query("who are you")
    assert SimpleQueryHandler.is_simple_query("who are you?")
    assert SimpleQueryHandler.is_simple_query("what version")
    assert not SimpleQueryHandler.is_simple_query("create a new file")

def test_handle_greeting():
    """Test handling of greeting queries."""
    response = SimpleQueryHandler.handle_query("hello")
    assert isinstance(response, AssistantResponse)
    assert "DeepSeek Engineer" in response.assistant_reply

def test_handle_capabilities():
    """Test handling of capabilities query."""
    response = SimpleQueryHandler.handle_query("what are your capabilities")
    assert isinstance(response, AssistantResponse)
    assert "help with" in response.assistant_reply.lower()

def test_handle_thanks():
    """Test handling of thank you messages."""
    response = SimpleQueryHandler.handle_query("thank you")
    assert isinstance(response, AssistantResponse)
    assert "welcome" in response.assistant_reply.lower()

def test_handle_exit():
    """Test handling of exit commands."""
    response = SimpleQueryHandler.handle_query("exit")
    assert isinstance(response, AssistantResponse)
    assert "Goodbye" in response.assistant_reply

def test_case_insensitivity():
    """Test case-insensitive query handling."""
    response1 = SimpleQueryHandler.handle_query("WHO ARE YOU")
    response2 = SimpleQueryHandler.handle_query("who are you")
    assert response1 is not None and response2 is not None
    assert isinstance(response1, AssistantResponse)
    assert isinstance(response2, AssistantResponse)
    assert response1.assistant_reply == response2.assistant_reply

def test_none_response():
    """Test that unknown queries return None."""
    response = SimpleQueryHandler.handle_query("this is not a known query")
    assert response is None

def test_empty_query():
    """Test handling of empty queries."""
    response = SimpleQueryHandler.handle_query("")
    assert response is None
    response = SimpleQueryHandler.handle_query("   ")
    assert response is None

def test_query_with_extra_whitespace():
    """Test handling of queries with extra whitespace."""
    response1 = SimpleQueryHandler.handle_query("who are you")
    response2 = SimpleQueryHandler.handle_query("   who are you   ")
    assert isinstance(response1, AssistantResponse)
    assert isinstance(response2, AssistantResponse)
    assert response1.assistant_reply == response2.assistant_reply

def test_partial_match_variations():
    """Test various partial match scenarios."""
    queries = [
        "tell me your capabilities",
        "what are your capabilities",
        "show me your capabilities",
        "capabilities please"
    ]
    responses = [SimpleQueryHandler.handle_query(q) for q in queries]
    
    # Verify all queries returned valid responses
    for response in responses:
        assert isinstance(response, AssistantResponse)
        assert "help with" in response.assistant_reply.lower()
    
    # Verify consistent responses
    first_response = responses[0]
    assert isinstance(first_response, AssistantResponse)
    for response in responses[1:]:
        assert isinstance(response, AssistantResponse)
        assert response.assistant_reply == first_response.assistant_reply

def test_greeting_variations():
    """Test different greeting formats."""
    greetings = ["hello", "hi", "hello!", "hi there"]
    responses = [SimpleQueryHandler.handle_query(g) for g in greetings]
    for response in responses:
        assert isinstance(response, AssistantResponse)
        assert "DeepSeek Engineer" in response.assistant_reply

def test_command_queries():
    """Test handling of command-related queries."""
    response = SimpleQueryHandler.handle_query("show me the commands")
    assert isinstance(response, AssistantResponse)
    assert "/add" in response.assistant_reply
    assert "/create_instance" in response.assistant_reply

def test_feature_queries():
    """Test handling of feature-related queries."""
    response = SimpleQueryHandler.handle_query("what features do you have")
    assert isinstance(response, AssistantResponse)
    assert "features" in response.assistant_reply.lower()
    assert "programming language" in response.assistant_reply.lower()

def test_status_query():
    """Test handling of status query."""
    response = SimpleQueryHandler.handle_query("what is your status")
    assert isinstance(response, AssistantResponse)
    assert "operational" in response.assistant_reply.lower()

def test_version_query():
    """Test handling of version query."""
    response = SimpleQueryHandler.handle_query("which version are you")
    assert isinstance(response, AssistantResponse)
    assert "version" in response.assistant_reply.lower()
    assert "DeepSeek Engineer" in response.assistant_reply
