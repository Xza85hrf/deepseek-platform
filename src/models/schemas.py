from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ToolUse(BaseModel):
    name: str
    params: Dict[str, Any]

class FileToCreate(BaseModel):
    path: str
    content: str

class FileToEdit(BaseModel):
    path: str
    original_snippet: str
    new_snippet: str

class AssistantResponse(BaseModel):
    assistant_reply: str
    files_to_create: Optional[List[FileToCreate]] = None
    files_to_edit: Optional[List[FileToEdit]] = None
    test_output: Optional[str] = None
    tool_uses: Optional[List[ToolUse]] = None

    def dict(self, *args, **kwargs):
        """Convert the model to a dictionary for JSON serialization"""
        d = super().dict(*args, **kwargs)
        if self.test_output is not None:
            d["test_output"] = self.test_output
        return d

class TaskSchema(BaseModel):
    task_id: str
    complexity: int
    result: Optional[str] = None
    
    def create_subtask(self) -> 'TaskSchema':
        """Create a subtask from this task"""
        return TaskSchema(
            task_id=f"{self.task_id}_sub",
            complexity=self.complexity
        )
    
    def is_valid(self) -> bool:
        """Validate task results"""
        return self.result is not None and len(self.result) > 0

class AgentSchema(BaseModel):
    agent_id: str
