from typing import List, Dict, Any, AsyncGenerator, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from ..file_ops.operations import read_local_file
from ..utils.helpers import normalize_path
from ..conversation.simple_queries import SimpleQueryHandler

# Initialize Rich consoles for different outputs
status_console = Console(stderr=True)  # For status messages
chat_console = Console()  # For chat messages

class ConversationHandler:
    def __init__(self):
        self.message_history = []
        
    async def handle_user_message(self, message: str) -> AsyncGenerator[str, None]:
        """Handle an incoming user message and stream the response"""
        async for response in self.process_message(message):
            yield response

    async def process_message(self, message: str) -> AsyncGenerator[str, None]:
        """Process an incoming message and stream the response"""
        from typing import AsyncGenerator
        from src.api.client import stream_openai_response
        from rich.syntax import Syntax
        from rich.text import Text
        from rich.markdown import Markdown
        
        # First try to handle special commands
        if self._handle_special_commands(message):
            return
            
        # Check if it's a simple query
        simple_response = SimpleQueryHandler.handle_query(message)
        if simple_response is not None:
            self.message_history.append({
                'role': 'user',
                'content': message
            })
            
            # Format the response
            formatted_response = simple_response.assistant_reply
            if '```' in formatted_response:
                # Extract and format code blocks
                parts = formatted_response.split('```')
                formatted_response = ''
                for i, part in enumerate(parts):
                    if i % 2 == 1:  # Code block
                        lang = part.split('\n')[0] or 'python'
                        code = '\n'.join(part.split('\n')[1:])
                        formatted_response += f"\n```{lang}\n{code}\n```\n"
                    else:
                        formatted_response += part
            
            self.message_history.append({
                'role': 'assistant',
                'content': formatted_response
            })
            yield formatted_response
            return
            
        # Add message to history
        self.message_history.append({
            'role': 'user',
            'content': message
        })
        
        try:
            # Stream response from API
            response = ""
            async for chunk in stream_openai_response(
                instance_id="default",
                messages=self.message_history,
                model="deepseek-chat"
            ):
                response += chunk.assistant_reply
                yield response
                
            # Add final response to history
            self.message_history.append({
                'role': 'assistant',
                'content': response
            })
            
        except Exception as e:
            yield f"Error: {str(e)}"
        
    def _handle_special_commands(self, message: str) -> bool:
        """Handle special commands like /add"""
        if message.strip().lower().startswith("/add "):
            return self._handle_add_command(message)
        return False
        
    def _handle_add_command(self, message: str) -> bool:
        """Handle the /add command to include files in the conversation"""
        prefix = "/add "
        file_path = message[len(prefix):].strip()
        try:
            content = read_local_file(file_path)
            self.message_history.append({
                'role': 'system',
                'content': f"Content of file '{file_path}':\n\n{content}"
            })
            status_console.print(
                f"[green]✓[/green] Added file '[cyan]{file_path}[/cyan]' to conversation.\n"
            )
            return True
        except OSError as e:
            status_console.print(
                f"[red]✗[/red] Could not add file '[cyan]{file_path}[/cyan]': {e}\n",
                style="red",
            )
            return True

def try_handle_add_command(user_input: str, conversation_history: list) -> bool:
    """Handle the /add command to include files in the conversation."""
    prefix = "/add "
    if user_input.strip().lower().startswith(prefix):
        file_path = user_input[len(prefix) :].strip()
        try:
            content = read_local_file(file_path)
            conversation_history.append(
                {
                    "role": "system",
                    "content": f"Content of file '{file_path}':\n\n{content}",
                }
            )
            status_console.print(
                f"[green]✓[/green] Added file '[cyan]{file_path}[/cyan]' to conversation.\n"
            )
        except OSError as e:
            status_console.print(
                f"[red]✗[/red] Could not add file '[cyan]{file_path}[/cyan]': {e}\n",
                style="red",
            )
        return True
    return False

from ..models.schemas import FileToEdit

def show_diff_table(files_to_edit: List[FileToEdit]) -> None:
    """Display a table showing proposed file edits."""
    if not files_to_edit:
        return

    table = Table(
        title="Proposed Edits",
        show_header=True,
        header_style="bold magenta",
        show_lines=True,
    )
    table.add_column("File Path", style="cyan")
    table.add_column("Original", style="red")
    table.add_column("New", style="green")

    for edit in files_to_edit:
        table.add_row(edit.path, edit.original_snippet, edit.new_snippet)

    chat_console.print(table)
