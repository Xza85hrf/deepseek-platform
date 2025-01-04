from pathlib import Path
import difflib
from typing import List, Optional, Union
from dataclasses import dataclass

@dataclass
class TextBlock:
    text: str
    type: str = "text"

@dataclass
class ImageSource:
    media_type: str
    data: str
    type: str = "base64"

@dataclass
class ImageBlock:
    source: ImageSource
    type: str = "image"

class FormatResponse:
    @staticmethod
    def tool_denied() -> str:
        return "The user denied this operation."

    @staticmethod
    def tool_denied_with_feedback(feedback: Optional[str] = None) -> str:
        if feedback:
            return f"The user denied this operation and provided the following feedback:\n<feedback>\n{feedback}\n</feedback>"
        return "The user denied this operation."

    @staticmethod
    def tool_error(error: Optional[str] = None) -> str:
        if error:
            return f"The tool execution failed with the following error:\n<error>\n{error}\n</error>"
        return "The tool execution failed."

    @staticmethod
    def no_tools_used() -> str:
        return """[ERROR] You did not use a tool in your previous response! Please retry with a tool use.

# Reminder: Instructions for Tool Use

Tool uses are formatted using XML-style tags. The tool name is enclosed in opening and closing tags, and each parameter is similarly enclosed within its own set of tags. Here's the structure:

<tool_name>
<parameter1_name>value1</parameter1_name>
<parameter2_name>value2</parameter2_name>
...
</tool_name>

For example:

<attempt_completion>
<result>
I have completed the task...
</result>
</attempt_completion>

Always adhere to this format for all tool uses to ensure proper parsing and execution.

# Next Steps

If you have completed the user's task, use the attempt_completion tool. 
If you require additional information from the user, use the ask_followup_question tool. 
Otherwise, if you have not completed the task and do not need additional information, then proceed with the next step of the task. 
(This is an automated message, so do not respond to it conversationally.)"""

    @staticmethod
    def too_many_mistakes(feedback: Optional[str] = None) -> str:
        if feedback:
            return f"You seem to be having trouble proceeding. The user has provided the following feedback to help guide you:\n<feedback>\n{feedback}\n</feedback>"
        return "You seem to be having trouble proceeding."

    @staticmethod
    def missing_tool_parameter_error(param_name: str) -> str:
        return f"Missing value for required parameter '{param_name}'. Please retry with complete response.\n\n# Reminder: Instructions for Tool Use\n\nTool uses are formatted using XML-style tags. The tool name is enclosed in opening and closing tags, and each parameter is similarly enclosed within its own set of tags. Here's the structure:\n\n<tool_name>\n<parameter1_name>value1</parameter1_name>\n<parameter2_name>value2</parameter2_name>\n...\n</tool_name>\n\nFor example:\n\n<attempt_completion>\n<result>\nI have completed the task...\n</result>\n</attempt_completion>\n\nAlways adhere to this format for all tool uses to ensure proper parsing and execution."

    @staticmethod
    def invalid_mcp_tool_argument_error(server_name: str, tool_name: str) -> str:
        return f"Invalid JSON argument used with {server_name} for {tool_name}. Please retry with a properly formatted JSON argument."

    @staticmethod
    def tool_result(text: str, images: Optional[List[str]] = None) -> Union[str, List[Union[TextBlock, ImageBlock]]]:
        if images and len(images) > 0:
            text_block = TextBlock(text=text)
            image_blocks = FormatResponse._format_images_into_blocks(images)
            return [text_block, *image_blocks]
        return text

    @staticmethod
    def image_blocks(images: Optional[List[str]] = None) -> List[ImageBlock]:
        return FormatResponse._format_images_into_blocks(images)

    @staticmethod
    def format_files_list(absolute_path: str, files: List[str], did_hit_limit: bool) -> str:
        base_path = Path(absolute_path)
        sorted_files = sorted(
            (str(Path(file).relative_to(base_path).as_posix()) + ("/" if file.endswith("/") else "") for file in files),
            key=lambda x: (x.count("/"), x)
        )
        
        if did_hit_limit:
            return f"{'\n'.join(sorted_files)}\n\n(File list truncated. Use list_files on specific subdirectories if you need to explore further.)"
        elif not sorted_files or (len(sorted_files) == 1 and sorted_files[0] == ""):
            return "No files found."
        return "\n".join(sorted_files)

    @staticmethod
    def create_pretty_patch(filename: str = "file", old_str: Optional[str] = None, new_str: Optional[str] = None) -> str:
        patch = difflib.unified_diff(
            (old_str or "").splitlines(),
            (new_str or "").splitlines(),
            fromfile=filename,
            tofile=filename,
            lineterm=""
        )
        return "\n".join(patch)

    @staticmethod
    def _format_images_into_blocks(images: Optional[List[str]] = None) -> List[ImageBlock]:
        if not images:
            return []
        
        return [
            ImageBlock(
                source=ImageSource(
                    media_type=data_url.split(":")[1].split(";")[0],
                    data=data_url.split(",")[1]
                )
            )
            for data_url in images
        ]
