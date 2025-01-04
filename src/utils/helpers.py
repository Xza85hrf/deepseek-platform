from dataclasses import dataclass
from typing import Optional
import tiktoken

@dataclass
class ModelInfo:
    """Represents information about an AI model including pricing and capabilities."""
    name: str
    provider: str
    max_tokens: int
    context_window: int
    supports_images: bool
    supports_computer_use: bool
    supports_prompt_cache: bool
    input_price: float  # Price per million input tokens
    output_price: float  # Price per million output tokens
    cache_writes_price: Optional[float] = None  # Price per million cache writes
    cache_reads_price: Optional[float] = None  # Price per million cache reads

def chunk_messages(messages: list[dict], max_tokens: int, model: str = "gpt-3.5-turbo") -> list[list[dict]]:
    """
    Split messages into chunks that don't exceed the specified token limit.
    
    Args:
        messages: List of message dictionaries to chunk
        max_tokens: Maximum number of tokens per chunk
        model: Model name to use for tokenization (default: gpt-3.5-turbo)
        
    Returns:
        List of message chunks, each containing one or more messages
    """
    chunks = []
    current_chunk = []
    current_tokens = 0
    
    for message in messages:
        if not isinstance(message, dict) or 'content' not in message:
            continue
            
        message_tokens = count_tokens(message['content'], model)
        
        # If adding this message would exceed the limit, start a new chunk
        if current_tokens + message_tokens > max_tokens:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = []
            current_tokens = 0
            
        current_chunk.append(message)
        current_tokens += message_tokens
    
    # Add the last chunk if it contains any messages
    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks

def count_tokens(text: str | bytes | None, model: str = "gpt-3.5-turbo") -> int:
    """
    Count the number of tokens in a text string using the specified model's tokenizer.
    
    Args:
        text: The text to count tokens for (string, bytes, or None)
        model: The model name to use for tokenization (default: gpt-3.5-turbo)
        
    Returns:
        Number of tokens in the text
    """
    if text is None:
        return 0
        
    # Convert bytes to string if necessary
    if isinstance(text, bytes):
        try:
            text = text.decode('utf-8')
        except UnicodeDecodeError:
            return 0
            
    # Ensure text is a string
    if not isinstance(text, str):
        try:
            text = str(text)
        except:
            return 0
    
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except KeyError:
        # Fallback to cl100k_base encoding if model not found
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))

def normalize_path(path: str) -> str:
    """
    Normalize a file path to use forward slashes and remove any redundant separators.
    
    Args:
        path: The path to normalize
        
    Returns:
        Normalized path string
    """
    # Convert backslashes to forward slashes
    path = path.replace('\\', '/')
    
    # Remove any duplicate slashes
    path = '/'.join(filter(None, path.split('/')))
    
    return path

def calculate_api_cost(
    model_info: ModelInfo,
    input_tokens: int,
    output_tokens: int,
    cache_creation_input_tokens: Optional[int] = None,
    cache_read_input_tokens: Optional[int] = None
) -> float:
    """
    Calculate the total API cost based on token counts and model pricing.
    
    Args:
        model_info: Model information including pricing
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        cache_creation_input_tokens: Optional number of cache creation input tokens
        cache_read_input_tokens: Optional number of cache read input tokens
        
    Returns:
        Total cost in dollars
    """
    # Calculate cache write cost if applicable
    cache_writes_cost = 0
    if cache_creation_input_tokens is not None and model_info.cache_writes_price is not None:
        cache_writes_cost = (model_info.cache_writes_price / 1_000_000) * cache_creation_input_tokens
        
    # Calculate cache read cost if applicable
    cache_reads_cost = 0
    if cache_read_input_tokens is not None and model_info.cache_reads_price is not None:
        cache_reads_cost = (model_info.cache_reads_price / 1_000_000) * cache_read_input_tokens
        
    # Calculate base input cost with null check
    base_input_cost = ((model_info.input_price or 0) / 1_000_000) * input_tokens
    
    # Calculate output cost with null check
    output_cost = ((model_info.output_price or 0) / 1_000_000) * output_tokens
        
    # Return total cost rounded to 6 decimal places
    return round(cache_writes_cost + cache_reads_cost + base_input_cost + output_cost, 6)
