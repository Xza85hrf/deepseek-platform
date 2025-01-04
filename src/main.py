#!/usr/bin/env python3

import os
import sys
import json

# Add project root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path
from textwrap import dedent
from rich.console import Console
from rich.panel import Panel
from src.api.client import stream_openai_response, show_cost_report
from src.utils.state_manager import EngineerState, get_state_manager
from themes.icon_animation import get_icon_animation
from src.conversation.handler import try_handle_add_command, show_diff_table
from src.conversation.simple_queries import SimpleQueryHandler
from src.file_ops.operations import apply_diff_edit, create_file
from src.models.schemas import AssistantResponse
from src.tools.tool_manager import ToolManager

# Initialize Rich consoles for different outputs
status_console = Console(stderr=True)  # For status messages
chat_console = Console()  # For chat messages

# Initialize ToolManager
tool_manager = ToolManager()

def load_prompt_instructions():
    """Load and format prompt instructions from JSON file."""
    try:
        with open(
            "src/conversation/prompt_instructions.json", "r", encoding="utf-8"
        ) as f:
            instructions = json.load(f)
            formatted_instructions = "\n".join(
                [
                    f"{phase['Action']}\nConfirmation: {phase['Confirmation']}"
                    for phase in instructions["Phase-wise Instructions"]
                ]
            )
            return formatted_instructions
    except Exception as e:
        status_console.print(
            f"[yellow]⚠[/yellow] Could not load prompt instructions: {e}",
            style="yellow",
        )
        return "Default instructions"

# System prompt with integrated instructions
system_PROMPT = dedent(
    """\
    You are DeepSeek Engineer, a highly skilled software engineer with extensive knowledge in many programming languages, frameworks, design patterns, and best practices.

    When given a task:
    1. First analyze the task and break it down into clear steps
    2. For each step, use the most appropriate tool from your available tools
    3. Wait for confirmation after each tool use before proceeding
    4. Use <thinking></thinking> tags to explain your reasoning
    5. Be direct and technical in your responses
    6. When complete, use attempt_completion to present the result

    Available tools:
    - execute_command: Run CLI commands
    - read_file: Read file contents
    - write_to_file: Create or overwrite files
    - replace_in_file: Make targeted edits to files
    - search_files: Search for patterns across files
    - list_files: List directory contents
    - list_code_definition_names: List code definitions
    - browser_action: Control browser for testing
    - ask_followup_question: Ask user for clarification
    - attempt_completion: Present final result

    Guidelines:
    1. Use one tool at a time and wait for confirmation
    2. Think carefully about which tool is most appropriate
    3. Be precise and thorough in your solutions
    4. Follow best practices for the specific technology
    5. Consider edge cases and error handling
    6. Write clear, maintainable code
    7. Test your work when appropriate

    Remember: You're a senior engineer - be methodical, precise, and thoughtful in your solutions.
"""
)


def handle_instruction_update(user_input: str, conversation_history: list) -> bool:
    """Handle requests to update or improve instructions."""
    if user_input.lower().startswith("/update_instructions"):
        try:
            # Ask user for the specific improvements
            chat_console.print(
                "[bold cyan]What improvements would you like to make to the instructions?[/bold cyan]"
            )
            improvements = chat_console.input(
                "[bold green]Improvements>[/bold green] "
            ).strip()

            # Confirm with user
            confirm = (
                chat_console.input(
                    "\nAre you sure you want to update the instructions? ([green]y[/green]/[red]n[/red]): "
                )
                .strip()
                .lower()
            )

            if confirm == "y":
                # Update the instructions file
                with open(
                    "src/conversation/prompt_instructions.json", "r+", encoding="utf-8"
                ) as f:
                    instructions = json.load(f)
                    instructions["Improvements"].append(improvements)
                    f.seek(0)
                    json.dump(instructions, f, indent=2)
                    f.truncate()

                status_console.print(
                    "[green]✓[/green] Instructions updated successfully!"
                )
                return True
        except Exception as e:
            status_console.print(
                f"[red]✗[/red] Failed to update instructions: {e}", style="red"
            )
            return True
    return False


async def handle_instance_commands(user_input: str, multi_client) -> bool:
    """Handle instance management commands."""
    if user_input.lower().startswith("/create_instance"):
        try:
            parts = user_input.split()
            if len(parts) < 4:
                chat_console.print("[red]Usage: /create_instance ID ROLE API_KEY[/red]")
                return True

            instance_id = parts[1]
            role = parts[2]
            api_key = parts[3]

            multi_client.add_instance(instance_id, role, api_key)
            return True
        except Exception as e:
            status_console.print(f"[red]Error creating instance: {e}[/red]")
            return True

    elif user_input.lower().startswith("/list_instances"):
        show_instance_panel(multi_client)
        return True

    elif user_input.lower().startswith("/select_instance"):
        try:
            instance_id = user_input.split()[1]
            multi_client.get_instance(instance_id)  # Will raise error if invalid
            chat_console.print(f"[green]Switched to instance {instance_id}[/green]")
            return True
        except Exception as e:
            status_console.print(f"[red]Error selecting instance: {e}[/red]")
            return True

    elif user_input.lower().startswith("/communicate"):
        try:
            parts = user_input.split()
            if len(parts) < 4:
                chat_console.print(
                    "[red]Usage: /communicate SENDER_ID RECEIVER_ID MESSAGE[/red]"
                )
                return True

            sender_id = parts[1]
            receiver_id = parts[2]
            message = " ".join(parts[3:])

            response = multi_client.communicate_between_instances(
                sender_id, receiver_id, message
            )
            chat_console.print(f"[blue]Communication Result:[/blue]\n{response}")
            return True
        except Exception as e:
            status_console.print(
                f"[red]Error communicating between instances: {e}[/red]"
            )
            return True

    elif user_input.lower().startswith("/cost"):
        try:
            await show_cost_report()
            return True
        except Exception as e:
            status_console.print(f"[red]Error showing cost report: {e}[/red]")
            return True

    return False


def show_instance_panel(multi_client):
    """Display a panel showing active instances and their roles."""
    if not multi_client.instances:
        chat_console.print("[yellow]No active instances[/yellow]")
        return

    panel_content = []
    for instance_id, role in multi_client.roles.items():
        panel_content.append(f"[bold]{instance_id}[/bold]: {role}")

    chat_console.print(
        Panel.fit(
            "\n".join(panel_content), title="Active Instances", border_style="blue"
        )
    )


async def main():
    """Main interactive loop."""
    try:
        # Prompt user for workspace directory
        console = Console()
        workspace_path = console.input(
            "[bold green]Please enter the workspace directory path: [/bold green]"
        ).strip()

        # Initialize workspace tracker
        console.print("[blue]Debug: Initializing workspace tracker...[/blue]")
        from src.file_ops.workspace_tracker import WorkspaceTracker

        def workspace_update_callback(files: list):
            console.print(f"[blue]Workspace updated: {len(files)} files[/blue]")

        workspace_tracker = WorkspaceTracker(workspace_path, workspace_update_callback)
        console.print(f"[green]✓[/green] Workspace set to: {workspace_path}")
        console.print("[blue]Debug: Workspace tracker initialized[/blue]")

        # Initialize state manager
        console.print("[blue]Debug: Initializing state manager...[/blue]")
    except Exception as e:
        console.print(f"[red]Error initializing workspace: {e}[/red]")
        return

    # Initialize state manager, Redis, and icon animation
    state_manager = get_state_manager()
    console.print("[blue]Debug: State manager created[/blue]")

    await state_manager.init_redis()
    console.print("[blue]Debug: Redis initialized[/blue]")

    icon_animation = get_icon_animation()
    console.print("[blue]Debug: Icon animation created[/blue]")

    icon_animation.start()
    console.print("[blue]Debug: Icon animation started[/blue]")

    # Initialize multi-instance client
    from src.api.client import multi_client

    # Load and format prompt instructions
    prompt_instructions = load_prompt_instructions()
    system_prompt = system_PROMPT.format(prompt_instructions=prompt_instructions)

    chat_console.print(
        Panel.fit(
            "[bold blue]Welcome to Deep Seek Engineer with Structured Output[/bold blue] [green](and streaming)[/green]!🐋",
            border_style="blue",
        )
    )
    chat_console.print(
        "Available commands:\n"
        "  [bold magenta]/add path/to/file[/bold magenta] - Include a file in the conversation\n"
        "  [bold magenta]/create_instance ID ROLE API_KEY[/bold magenta] - Create new API instance\n"
        "  [bold magenta]/list_instances[/bold magenta] - Show active instances\n"
        "  [bold magenta]/select_instance ID[/bold magenta] - Switch to specific instance\n"
        "  [bold magenta]/communicate SENDER_ID RECEIVER_ID MESSAGE[/bold magenta] - Send message between instances\n"
        "Type '[bold red]exit[/bold red]' or '[bold red]quit[/bold red]' to end.\n"
    )

    conversation_history = [{"role": "system", "content": system_prompt}]
    current_instance = "default"

    while True:
        try:
            user_input = chat_console.input(
                f"[bold green]You ({current_instance})>[/bold green] "
            ).strip()
            if not user_input:
                continue
            
            # Add user input to conversation history
            conversation_history.append({
                "role": "user",
                "content": user_input
            })
        except EOFError:
            chat_console.print("\n[yellow]End of input detected. Exiting.[/yellow]")
            break
        except KeyboardInterrupt:
            chat_console.print("\n[yellow]Interrupt received. Exiting.[/yellow]")
            break
        except Exception as e:
            status_console.print(f"[red]Error reading input: {e}[/red]")
            continue

        if user_input.lower() in ["exit", "quit"]:
            chat_console.print("[yellow]Goodbye![/yellow]")
            break

        if try_handle_add_command(
            user_input, conversation_history
        ) or handle_instruction_update(user_input, conversation_history):
            continue

        if await handle_instance_commands(user_input, multi_client):
            if user_input.lower().startswith("/select_instance"):
                current_instance = user_input.split()[1]
            continue

        # Check if this is a simple query first
        simple_response = SimpleQueryHandler.handle_query(user_input)
        if simple_response:
            chat_console.print("\nAssistant> ", style="bold blue", end="")
            chat_console.print(simple_response.assistant_reply)
            continue

        # Set thinking state while processing
        state_manager.state = EngineerState.THINKING
        try:
            from typing import List
            from openai.types.chat import ChatCompletionMessageParam
            
            # Convert conversation history to proper type
            from typing import cast
            typed_messages: List[ChatCompletionMessageParam] = [
                cast(ChatCompletionMessageParam, {
                    "role": msg["role"],
                    "content": msg["content"]
                })
                for msg in conversation_history
            ]
            
            try:
                response_data = None
                first_chunk = True
                full_response = ""
                
                async for chunk in stream_openai_response(
                    current_instance, typed_messages, "deepseek-chat"
                ):
                    response_data = chunk
                    if response_data.assistant_reply:
                        # Only print the prefix once at the start
                        if first_chunk:
                            chat_console.print("\nAssistant> ", style="bold blue", end="")
                            first_chunk = False
                        # Print just the chunk content
                        chat_console.print(response_data.assistant_reply, end="")
                        # Accumulate the full response
                        full_response += response_data.assistant_reply
                
                # Print a newline after streaming is complete
                if not first_chunk:  # Only if we printed something
                    chat_console.print()
                
                # Add the complete response to conversation history
                if full_response.strip():
                    conversation_history.append({
                        "role": "assistant",
                        "content": full_response.strip()
                    })
                
                state_manager.state = EngineerState.WORKING
            except Exception as e:
                state_manager.state = EngineerState.ERROR
                status_console.print(f"[red]Error processing response: {e}[/red]")
                continue
        except Exception as e:
            state_manager.state = EngineerState.ERROR
            status_console.print(f"[red]Error: {e}[/red]")
            continue

        if response_data:
            # Process tool uses through the ToolManager
            if response_data.tool_uses:
                for tool_use in response_data.tool_uses:
                    tool = tool_manager.get_tool(tool_use.name)
                    if tool:
                        try:
                            result = tool(**tool_use.params)
                            if result:
                                chat_console.print(
                                    Panel.fit(
                                        f"[bold green]Tool {tool_use.name} executed successfully[/bold green]\n"
                                        f"Result: {result}",
                                        title="Tool Execution",
                                        border_style="green"
                                    )
                                )
                            else:
                                chat_console.print(
                                    Panel.fit(
                                        f"[bold green]Tool {tool_use.name} executed successfully[/bold green]",
                                        title="Tool Execution",
                                        border_style="green"
                                    )
                                )
                        except Exception as e:
                            status_console.print(
                                Panel.fit(
                                    f"[red]Error executing tool {tool_use.name}: {e}[/red]",
                                    title="Tool Error",
                                    border_style="red"
                                )
                            )
                    else:
                        status_console.print(
                            Panel.fit(
                                f"[yellow]Unknown tool: {tool_use.name}[/yellow]",
                                title="Tool Warning",
                                border_style="yellow"
                            )
                        )

            # Execute tests if test_output is present in the response
            if response_data.test_output:
                try:
                    try:
                        import pytest
                    except ImportError:
                        status_console.print(
                            "[yellow]pytest is not installed. Run 'pip install pytest' to enable testing.[/yellow]"
                        )
                        continue
                    import subprocess

                    # Run pytest and capture output
                    result = subprocess.run(
                        ["pytest", "-v"],
                        capture_output=True,
                        text=True,
                        cwd=os.getcwd(),
                    )

                    # Display test results
                    if result.returncode == 0:
                        status_console.print(
                            "[green]✓[/green] Tests passed successfully!"
                        )
                    else:
                        status_console.print("[red]✗[/red] Tests failed")

                    # Show test output
                    chat_console.print("\n[bold blue]Test Results:[/bold blue]")
                    chat_console.print(result.stdout)

                    if result.stderr:
                        status_console.print("\n[red]Test Errors:[/red]")
                        status_console.print(result.stderr)

                except Exception as e:
                    status_console.print(f"[red]Error running tests: {e}[/red]")
        else:
            status_console.print(
                "[yellow]⚠[/yellow] No response data received", style="yellow"
            )

    # Clean up animation
    icon_animation.stop()
    chat_console.print("[blue]Session finished.[/blue]")


if __name__ == "__main__":
    import asyncio

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram terminated gracefully")
    except Exception as e:
        print(f"Error: {e}")
