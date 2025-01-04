import pytest
import os
from unittest.mock import patch, MagicMock, AsyncMock
from src.api.client import (
    MultiInstanceClient,
    generate_cache_key,
    multi_client,
    stream_openai_response,
    calculate_cost,
    guess_files_in_message
)

def test_multi_instance_client_initialization():
    client = MultiInstanceClient()
    assert isinstance(client.instances, dict)
    assert isinstance(client.roles, dict)
    assert hasattr(client, 'encryption_key')

def test_add_instance():
    client = MultiInstanceClient()
    with patch('src.api.client.OpenAI') as mock_openai:
        client.add_instance("test1", "test_role", "test_key")
        assert "test1" in client.instances
        assert "test1" in client.roles
        assert client.roles["test1"] == "test_role"

def test_add_duplicate_instance():
    client = MultiInstanceClient()
    with patch('src.api.client.OpenAI'):
        client.add_instance("test1", "test_role", "test_key")
        with pytest.raises(ValueError):
            client.add_instance("test1", "test_role", "test_key")

def test_get_instance():
    client = MultiInstanceClient()
    with patch('src.api.client.OpenAI') as mock_openai:
        client.add_instance("test1", "test_role", "test_key")
        instance = client.get_instance("test1")
        assert instance is not None

def test_get_nonexistent_instance():
    client = MultiInstanceClient()
    with pytest.raises(ValueError):
        client.get_instance("nonexistent")

def test_encryption_decryption():
    client = MultiInstanceClient()
    test_key = "test_api_key"
    encrypted = client._encrypt_api_key(test_key)
    decrypted = client._decrypt_api_key(encrypted)
    assert decrypted == test_key

def test_encryption_empty_key():
    client = MultiInstanceClient()
    with pytest.raises(ValueError):
        client._encrypt_api_key("")

def test_decryption_invalid_key():
    client = MultiInstanceClient()
    with pytest.raises(Exception):
        client._decrypt_api_key("invalid_encrypted_key")

def test_decryption_corrupted_key():
    client = MultiInstanceClient()
    test_key = "test_api_key"
    encrypted = client._encrypt_api_key(test_key)
    # Corrupt the encrypted key by removing the last character
    corrupted = encrypted[:-1]
    with pytest.raises(Exception):
        client._decrypt_api_key(corrupted)

def test_communicate_between_instances():
    client = MultiInstanceClient()
    with patch('src.api.client.OpenAI'):
        client.add_instance("sender", "sender_role", "key1")
        client.add_instance("receiver", "receiver_role", "key2")
        result = client.communicate_between_instances("sender", "receiver", "test message")
        assert "sender_role" in result
        assert "receiver_role" in result
        assert "test message" in result

def test_generate_cache_key():
    conversation_history = [
        {"role": "user", "content": "message1"},
        {"role": "assistant", "content": "response1"}
    ]
    key = generate_cache_key(conversation_history)
    assert isinstance(key, str)
    assert len(key) > 0

def test_generate_cache_key_empty_params():
    key = generate_cache_key([])
    assert isinstance(key, str)
    assert len(key) > 0

def test_generate_cache_key_special_chars():
    conversation_history = [
        {"role": "user", "content": "message@1"},
        {"role": "assistant", "content": "response#1"}
    ]
    key = generate_cache_key(conversation_history)
    assert isinstance(key, str)
    assert len(key) > 0

def test_generate_cache_key_mixed_params():
    history1 = [{"role": "user", "content": "message1"}]
    history2 = [{"role": "user", "content": "message2"}]
    history3 = [{"role": "assistant", "content": "response1"}]
    
    key1 = generate_cache_key(history1)
    key2 = generate_cache_key(history2)
    key3 = generate_cache_key(history3)
    
    assert key1 != key2
    assert key1 != key3
    assert key2 != key3

import pytest_asyncio

@pytest.mark.asyncio
async def test_stream_openai_response_success():
    with patch('src.api.client.OpenAI') as mock_openai:
        mock_instance = AsyncMock()
        
        # Test different streaming scenarios
        test_scenarios = [
            # Test sentence boundary yielding
            {
                "chunks": [
                    "This is a test sentence.",
                    " Here's another sentence!",
                    " And a final one?"
                ],
                "expected_chunks": 3
            },
            # Test newline immediate yielding
            {
                "chunks": [
                    "First line\n",
                    "Second line\n",
                    "Third line"
                ],
                "expected_chunks": 3
            },
            # Test buffer size yielding
            {
                "chunks": ["a" * 10 for _ in range(6)],  # 60 chars total, should yield at least once
                "expected_chunks": 2
            }
        ]
        
        for scenario in test_scenarios:
            # Create async generator for current scenario
            async def mock_aiter():
                for chunk in scenario["chunks"]:
                    yield {"choices": [{"delta": {"content": chunk}}]}
            
            mock_stream = AsyncMock()
            mock_stream.__aiter__.return_value = mock_aiter()
            mock_instance.chat.completions.create = AsyncMock(return_value=mock_stream)
            
            # Clear any existing test instances
            if "test" in multi_client.instances:
                del multi_client.instances["test"]
            if "test" in multi_client.roles:
                del multi_client.roles["test"]
                
            # Add test instance
            multi_client.add_instance("test", "role", "key")
            multi_client.instances["test"] = mock_instance
            
            # Test the streaming
            response = []
            async for chunk in stream_openai_response("test", [{"role": "user", "content": "test"}], "test"):
                response.append(chunk)
            
            # Verify we received the expected number of chunks
            assert len(response) >= scenario["expected_chunks"], f"Expected at least {scenario['expected_chunks']} chunks, got {len(response)}"
            
            # Verify all content was received
            full_content = "".join(scenario["chunks"])
            received_content = "".join(chunk.assistant_reply for chunk in response)
            assert full_content.strip() == received_content.strip(), "Content mismatch in received chunks"

@pytest.mark.asyncio
async def test_stream_openai_response_error():
    with patch('src.api.client.OpenAI') as mock_openai:
        mock_instance = AsyncMock()
        mock_instance.chat.completions.create = AsyncMock(side_effect=Exception("API error"))
        
        # Clear any existing test instances
        if "test" in multi_client.instances:
            del multi_client.instances["test"]
        if "test" in multi_client.roles:
            del multi_client.roles["test"]
            
        # Add test instance
        multi_client.add_instance("test", "role", "key")
        multi_client.instances["test"] = mock_instance
        
        # Test error handling
        with pytest.raises(Exception, match="API error"):
            mock_instance.chat.completions.create = AsyncMock(side_effect=Exception("API error"))
            async for _ in stream_openai_response("test", [{"role": "user", "content": "test"}], "test"):
                pass

@pytest.fixture(autouse=True)
def cleanup_instances():
    """Fixture to clean up test instances after each test"""
    yield
    if "test" in multi_client.instances:
        del multi_client.instances["test"]
    if "test" in multi_client.roles:
        del multi_client.roles["test"]


def test_encryption_decryption_special_chars():
    client = MultiInstanceClient()
    test_key = "test@api#key$123"
    encrypted = client._encrypt_api_key(test_key)
    decrypted = client._decrypt_api_key(encrypted)
    assert decrypted == test_key

def test_encryption_decryption_long_key():
    client = MultiInstanceClient()
    test_key = "a" * 1000
    encrypted = client._encrypt_api_key(test_key)
    decrypted = client._decrypt_api_key(encrypted)
    assert decrypted == test_key

def test_generate_encryption_key():
    client = MultiInstanceClient()
    key = client._generate_encryption_key()
    assert isinstance(key, bytes)
    assert len(key) == 44  # Fernet keys are 44 bytes long
    # Verify key file was created
    assert os.path.exists(".encryption_key")
    # Clean up
    os.remove(".encryption_key")

def test_calculate_cost():
    # Test with cache hit
    cost = calculate_cost(1000, 500, True)
    assert cost == (1000/1_000_000)*0.014 + (500/1_000_000)*1.10
    
    # Test with cache miss
    cost = calculate_cost(1000, 500, False)
    assert cost == (1000/1_000_000)*0.27 + (500/1_000_000)*1.10
    
    # Test with zero tokens
    cost = calculate_cost(0, 0, True)
    assert cost == 0.0
    
    # Test with large numbers
    cost = calculate_cost(1_000_000, 500_000, False)
    assert cost == 0.27 + 0.55

def test_guess_files_in_message():
    # Test with simple file path
    message = "Please check the file src/main.py"
    files = guess_files_in_message(message)
    assert "src/main.py" in files
    
    # Test with multiple files
    message = "Look at index.html and styles.css"
    files = guess_files_in_message(message)
    assert "index.html" in files
    assert "styles.css" in files
    
    # Test with quoted paths
    message = 'Check "config/settings.json"'
    files = guess_files_in_message(message)
    assert "config/settings.json" in files
    
    # Test with backtick paths
    message = "See `docs/README.md`"
    files = guess_files_in_message(message)
    assert "docs/README.md" in files
    
    # Test with invalid paths
    message = "This is not a file path"
    files = guess_files_in_message(message)
    assert len(files) == 0
    
    # Test with mixed content
    message = "Check these files: `src/main.py`, 'config.json', and README.md"
    files = guess_files_in_message(message)
    assert len(files) == 3
    assert "src/main.py" in files
    assert "config.json" in files
    assert "README.md" in files
