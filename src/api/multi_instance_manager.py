"""
DeepSeek API Multi-Instance Manager

This module implements a system with three distinct DeepSeek API instances:
1. Organizer/Manager/Overseer
2. Task Delegation and Error Checking
3. Coding

The system facilitates communication between instances and dynamic agent generation.
"""

from datetime import datetime
from typing import Dict, List, Optional, Union, TypedDict
from dataclasses import dataclass
import tiktoken
import requests
from src.models.schemas import TaskSchema, AgentSchema
from src.utils.state_manager import StateManager


def num_tokens_from_messages(
    messages: List[Dict[str, str]], model: str = "deepseek-v3"
) -> int:
    """Calculate the number of tokens used by a list of messages."""
    encoding = tiktoken.encoding_for_model(model)

    # DeepSeek V3 specific tokenization
    total_tokens = 0
    for message in messages:
        # Role and content tokens
        total_tokens += len(encoding.encode(message["role"])) + 3  # role + colon
        total_tokens += len(encoding.encode(message["content"]))

        # Message separator tokens
        total_tokens += len(encoding.encode("\n"))

    # Add system message overhead
    if any(msg["role"] == "system" for msg in messages):
        total_tokens += 50  # Additional tokens for system message formatting

    return total_tokens


def validate_task(task: TaskSchema) -> bool:
    """Validate task structure and content"""
    return bool(task.task_id) and task.complexity >= 0


@dataclass
class DeepSeekInstance:
    """Base class for DeepSeek API instances"""

    instance_id: str
    role: str
    agents: List[AgentSchema]
    state_manager: StateManager

    def generate_agents(self, num_agents: int) -> List[AgentSchema]:
        """Generate agents based on task complexity"""
        return [
            AgentSchema(agent_id=f"{self.instance_id}_agent_{i}")
            for i in range(num_agents)
        ]


class OrganizerInstance(DeepSeekInstance):
    """Instance responsible for organizing and managing tasks"""

    def __init__(self):
        super().__init__(
            instance_id="organizer",
            role="Organizer/Manager/Overseer",
            agents=[],
            state_manager=StateManager(),
        )

    def determine_agents_required(self, task: TaskSchema) -> int:
        """Determine number of agents needed based on task complexity"""
        complexity = task.complexity
        return min(max(1, complexity // 10), 5)  # Scale agents based on complexity


class TaskDelegatorInstance(DeepSeekInstance):
    """Instance responsible for task delegation and error checking"""

    def __init__(self):
        super().__init__(
            instance_id="delegator",
            role="Task Delegation and Error Checking",
            agents=[],
            state_manager=StateManager(),
        )

    def delegate_task(
        self, task: TaskSchema, agents: List[AgentSchema]
    ) -> Dict[str, TaskSchema]:
        """Delegate subtasks to agents"""
        return {agent.agent_id: task.create_subtask() for agent in agents}

    def check_errors(self, results: Dict[str, TaskSchema]) -> bool:
        """Check for errors in task execution"""
        return all(result.is_valid() for result in results.values())


class CodingInstance(DeepSeekInstance):
    """Instance responsible for executing coding tasks"""

    def __init__(self):
        super().__init__(
            instance_id="coder", role="Coding", agents=[], state_manager=StateManager()
        )

    def execute_task(self, task: TaskSchema) -> TaskSchema:
        """Execute coding task and return result"""
        if not validate_task(task):
            raise ValueError("Invalid task format")

        # Execute task logic here
        task.result = self._process_task(task)
        return task

    def _process_task(self, task: TaskSchema) -> str:
        """Internal task processing logic"""
        # Implementation specific to coding tasks
        return f"Processed task: {task.task_id}"


class APIStatus(TypedDict, total=False):
    """Type definition for API status response"""
    status: str
    components: List[Dict[str, str]]
    updated_at: str
    error: Optional[str]

class MultiInstanceManager:
    """Manager for coordinating multiple DeepSeek instances"""
    
    def check_api_status(self) -> APIStatus:
        """Check the current status of the DeepSeek API"""
        try:
            response = requests.get("https://status.deepseek.com/api/v2/status.json")
            response.raise_for_status()
            data = response.json()
            
            return {
                "status": data.get("status", {}).get("description", "unknown"),
                "components": [
                    {
                        "name": component.get("name", "unknown"),
                        "status": component.get("status", "unknown")
                    }
                    for component in data.get("components", [])
                ],
                "updated_at": data.get("page", {}).get("updated_at", "unknown"),
                "error": None
            }
        except requests.RequestException as e:
            return {
                "status": "error",
                "components": [],
                "updated_at": datetime.now().isoformat(),
                "error": str(e)
            }

    def __init__(self):
        self.organizer = OrganizerInstance()
        self.delegator = TaskDelegatorInstance()
        self.coder = CodingInstance()
        self.communication_queue = []

    def process_task(self, task: TaskSchema) -> TaskSchema:
        """Process a task through the multi-instance system"""
        # Step 1: Determine required agents
        num_agents = self.organizer.determine_agents_required(task)
        agents = self.organizer.generate_agents(num_agents)

        # Step 2: Delegate task
        subtasks = self.delegator.delegate_task(task, agents)

        # Step 3: Execute tasks
        results = {}
        for agent_id, subtask in subtasks.items():
            results[agent_id] = self.coder.execute_task(subtask)

        # Step 4: Error checking
        if not self.delegator.check_errors(results):
            raise RuntimeError("Task execution failed validation")

        # Step 5: Consolidate results
        task.result = self._consolidate_results(results)
        return task

    def _consolidate_results(self, results: Dict[str, TaskSchema]) -> str:
        """Combine results from multiple agents"""
        return "\n".join(result.result for result in results.values() if result.result)

    def communicate(self, message: str, sender: str, receiver: str) -> None:
        """Handle communication between instances with token monitoring"""
        # Add new message to queue
        self.communication_queue.append(
            {
                "sender": sender,
                "receiver": receiver,
                "message": message,
                "timestamp": datetime.now(),
            }
        )

        # Check token usage
        if self._should_start_new_chat():
            self._handle_token_limit()

    def _should_start_new_chat(self) -> bool:
        """Determine if we need to start a new chat due to token limits"""
        messages = [
            {"role": msg["sender"], "content": msg["message"]}
            for msg in self.communication_queue
        ]

        return num_tokens_from_messages(messages) > 0.9 * 65536

    def _handle_token_limit(self) -> None:
        """Handle token limit by summarizing and starting new chat"""
        summary = self._generate_summary()
        self._save_summary(summary)
        self._start_new_chat(summary)

    def _generate_summary(self) -> str:
        """Generate summary of current conversation"""
        summary = "Conversation Summary:\n"
        for msg in self.communication_queue:
            summary += f"{msg['sender']} -> {msg['receiver']}: {msg['message']}\n"
        return summary

    def _save_summary(self, summary: str) -> None:
        """Save summary to file"""
        try:
            with open("conversation_summary.md", "a") as f:
                f.write(summary + "\n")
        except IOError as e:
            print(f"Error saving summary: {e}")

    def _start_new_chat(self, summary: str) -> None:
        """Start new chat with summary as context"""
        self.communication_queue = [
            {
                "sender": "system",
                "receiver": "all",
                "message": f"Previous conversation summary:\n{summary}",
                "timestamp": datetime.now(),
            }
        ]
