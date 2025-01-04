#!/usr/bin/env python3

import os
import json
import time
import hashlib
from typing import List, Dict, AsyncGenerator
from openai import OpenAI
from aioitertools.builtins import iter as aiter
from rich.console import Console
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from ..models.schemas import AssistantResponse, FileToCreate, FileToEdit
from ..utils.helpers import count_tokens, chunk_messages, normalize_path
from ..file_ops.operations import read_local_file, ensure_file_in_context
from ..utils.state_manager import get_state_manager

# Create dedicated consoles for different outputs
status_console = Console(stderr=True)  # For status messages
chat_console = Console()  # For chat messages


class MultiInstanceClient:
    def __init__(self):
        self.instances: Dict[str, OpenAI] = {}
        self.roles: Dict[str, str] = {}
        self.encryption_key = self._generate_encryption_key()
        load_dotenv()

    def _generate_encryption_key(self) -> bytes:
        """Generate a secure encryption key for API key storage"""
        key = Fernet.generate_key()
        with open(".encryption_key", "wb") as f:
            f.write(key)
        return key

    def _encrypt_api_key(self, api_key: str) -> str:
        """Encrypt API key using Fernet symmetric encryption"""
        if not api_key:
            raise ValueError("API key cannot be empty")
        fernet = Fernet(self.encryption_key)
        return fernet.encrypt(api_key.encode()).decode()

    def _decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypt API key using Fernet symmetric encryption"""
        fernet = Fernet(self.encryption_key)
        return fernet.decrypt(encrypted_key.encode()).decode()

    def add_instance(self, instance_id: str, role: str, api_key: str) -> None:
        """Add a new API instance with a specific role"""
        if instance_id in self.instances:
            raise ValueError(f"Instance {instance_id} already exists")

        encrypted_key = self._encrypt_api_key(api_key)
        os.environ[f"DEEPSEEK_API_KEY_{instance_id}"] = encrypted_key

        try:
            client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
            self.instances[instance_id] = client
            self.roles[instance_id] = role
            status_console.print(
                f"[green]✓[/green] Successfully added instance {instance_id} with role {role}",
                style="green",
            )
        except Exception as e:
            status_console.print(
                f"[red]✗[/red] Failed to initialize instance {instance_id}: {e}",
                style="red",
            )
            raise

    def get_instance(self, instance_id: str) -> OpenAI:
        """Get an API instance by ID"""
        if instance_id not in self.instances:
            raise ValueError(f"Instance {instance_id} does not exist")
        return self.instances[instance_id]

    def communicate_between_instances(
        self, sender_id: str, receiver_id: str, message: str
    ) -> str:
        """Facilitate communication between instances"""
        if sender_id not in self.instances or receiver_id not in self.instances:
            raise ValueError("Both instances must exist")

        # Add role context to the message
        message = f"Message from {self.roles[sender_id]}:\n{message}"

        # Simulate communication (this could be enhanced with actual API calls)
        return f"Message received by {self.roles[receiver_id]}:\n{message}"


# Initialize multi-instance client and add default instance
from dotenv import load_dotenv

load_dotenv(override=True)  # Force reload environment variables

multi_client = MultiInstanceClient()
default_api_key = os.getenv("DEEPSEEK_API_KEY")
if not default_api_key:
    raise ValueError("DEEPSEEK_API_KEY environment variable is not set")

# Debug output
status_console.print(f"[blue]Debug: API Key found: {bool(default_api_key)}[/blue]")

multi_client.add_instance("default", "Primary Assistant", default_api_key)


def generate_cache_key(conversation_history: list) -> str:
    """Generate a cache key based on conversation history"""
    key_data = json.dumps(conversation_history, sort_keys=True)
    return hashlib.sha256(key_data.encode()).hexdigest()


def calculate_cost(input_tokens: int, output_tokens: int, cache_hit: bool) -> float:
    """Calculate API cost based on token usage and cache status"""
    # DeepSeek V3 pricing (per 1M tokens)
    input_price = 0.014 if cache_hit else 0.27  # USD
    output_price = 1.10  # USD

    # Calculate costs
    input_cost = (input_tokens / 1_000_000) * input_price
    output_cost = (output_tokens / 1_000_000) * output_price
    return input_cost + output_cost


async def generate_cost_report(usage_stats) -> str:
    """Generate a detailed cost report with cache metrics"""
    # Calculate cache efficiency metrics
    cache_hit_rate = (
        (usage_stats.cache_hits / usage_stats.total_requests * 100)
        if usage_stats.total_requests > 0
        else 0
    )
    estimated_cache_savings = (
        usage_stats.cache_hits * 0.126
    )  # $0.14 (miss) - $0.014 (hit) per 1M tokens

    # Get Redis cache info if available
    state_manager = get_state_manager()
    cache_info = {}
    if state_manager.redis_client:
        try:
            # Make Redis info call async
            cache_info = await state_manager.redis_client.info("memory")
        except Exception:
            cache_info = {}

    report = f"""
    Cost Report:
    -------------
    Total Requests: {usage_stats.total_requests}
    Cache Hits: {usage_stats.cache_hits} ({cache_hit_rate:.1f}% hit rate)
    Cache Misses: {usage_stats.cache_misses}
    Total Tokens: {usage_stats.total_tokens}
    Tokens Saved by Cache: {usage_stats.cache_hits * usage_stats.total_tokens / usage_stats.total_requests if usage_stats.total_requests > 0 else 0:.0f}
    Total Cost: ${usage_stats.total_cost:.4f}
    Estimated Cache Savings: ${estimated_cache_savings:.4f}
    Cache Memory Usage: {cache_info.get('used_memory_human', 'N/A')}
    Last Request Time: {usage_stats.last_request_time}
    """
    return report


async def show_cost_report():
    """Display the current cost report"""
    state_manager = get_state_manager()
    usage_stats = state_manager.get_usage_stats()
    report = await generate_cost_report(usage_stats)
    status_console.print(report)


from openai.types.chat import ChatCompletionMessageParam

async def stream_openai_response(
    instance_id: str, messages: List[ChatCompletionMessageParam], model: str
) -> AsyncGenerator[AssistantResponse, None]:
    """Stream OpenAI response from the specified instance
    
    Args:
        instance_id: ID of the API instance to use
        messages: List of messages in the conversation
        model: Model to use for the completion
        
    Yields:
        AssistantResponse: Streamed response chunks
        
    Raises:
        Exception: If there is an error with the API call
    """
    instance = multi_client.get_instance(instance_id)
    
    try:
        # Create the completion stream
        response = instance.chat.completions.create(
            model=model,
            messages=messages,
            stream=True
        )
        
        # Process each chunk in the stream
        buffer = ""
        min_buffer_size = 50  # Reduced minimum for more responsive streaming
        max_buffer_size = 500  # Reduced maximum to prevent large chunks
        last_yield_time = time.time()
        sentence_boundaries = ('.', '!', '?', '\n', ':', ';')  # Added more natural break points
        
        async for chunk in aiter(response):
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                buffer += content
                
                current_time = time.time()
                # More responsive yielding logic
                should_yield = (
                    # Yield on reasonable chunk size with natural break
                    (len(buffer) >= min_buffer_size and any(buffer.rstrip().endswith(b) for b in sentence_boundaries)) or
                    # Force yield on max size
                    len(buffer) >= max_buffer_size or
                    # Yield on shorter timeout
                    current_time - last_yield_time > 0.5 or
                    # Yield immediately on newlines for more natural breaks
                    content.endswith('\n')
                )
                
                if should_yield:
                    yield AssistantResponse(
                        assistant_reply=buffer.strip(),
                        files_to_create=[],
                        files_to_edit=[]
                    )
                    buffer = ""
                    last_yield_time = current_time
        
        # Yield any remaining content in the buffer
        if buffer.strip():
            yield AssistantResponse(
                assistant_reply=buffer.strip(),
                files_to_create=[],
                files_to_edit=[]
            )
    except Exception as e:
        raise Exception(f"API error: {str(e)}")


def guess_files_in_message(user_message: str) -> List[str]:
    """Guess which files the user might be referencing."""
    if not user_message or not isinstance(user_message, str):
        return []

    recognized_extensions = [".css", ".html", ".js", ".py", ".json", ".md"]
    potential_paths = []
    for word in user_message.split():
        # Remove backticks, quotes, and other common delimiters
        word = word.strip("',\"`")
        if any(ext in word for ext in recognized_extensions) or "/" in word:
            try:
                normalized_path = normalize_path(word)
                potential_paths.append(normalized_path)
            except (OSError, ValueError):
                continue
    return potential_paths
