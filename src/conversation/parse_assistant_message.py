from typing import List, Dict, Union, Optional

# Define types for content blocks
AssistantMessageContent = Union['TextContent', 'ToolUse']
ToolParamName = str
ToolUseName = str

class TextContent:
    def __init__(self, content: str, partial: bool):
        self.type: str = "text"
        self.content: str = content
        self.partial: bool = partial

class ToolUse:
    def __init__(self, name: ToolUseName, params: Dict[ToolParamName, str], partial: bool):
        self.type: str = "tool_use"
        self.name: ToolUseName = name
        self.params: Dict[ToolParamName, str] = params
        self.partial: bool = partial

def parse_assistant_message(assistant_message: str) -> List[AssistantMessageContent]:
    content_blocks: List[AssistantMessageContent] = []
    i = 0
    n = len(assistant_message)
    
    while i < n:
        # Check for tool use start
        if i < n and assistant_message[i] == '<':
            tool_start = i
            tool_end = assistant_message.find('>', tool_start)
            if tool_end == -1:
                # Treat as plain text since tool use is incomplete
                text_content = assistant_message[tool_start:].strip()
                if text_content:
                    content_blocks.append(TextContent(
                        content=text_content,
                        partial=True
                    ))
                break
            
            else:
                # Complete tool use
                tool_name = assistant_message[tool_start+1:tool_end]
                tool_close_tag = f"</{tool_name}>"
                tool_close_pos = assistant_message.find(tool_close_tag, tool_end)
                
                if tool_close_pos == -1:
                    # Treat as plain text since tool use is incomplete
                    text_content = assistant_message[tool_start:].strip()
                    if text_content:
                        content_blocks.append(TextContent(
                            content=text_content,
                            partial=True
                        ))
                    break
                else:
                    # Complete tool use with parameters
                    params = {}
                    param_start = tool_end + 1
                    while param_start < tool_close_pos:
                        param_open = assistant_message.find('<', param_start, tool_close_pos)
                        if param_open == -1:
                            break
                            
                        param_close = assistant_message.find('>', param_open)
                        if param_close == -1:
                            break
                            
                        param_name = assistant_message[param_open+1:param_close]
                        param_end_tag = f"</{param_name}>"
                        param_end = assistant_message.find(param_end_tag, param_close)
                        
                        if param_end == -1:
                            break
                            
                        param_value = assistant_message[param_close+1:param_end].strip()
                        params[param_name] = param_value
                        param_start = param_end + len(param_end_tag)
                    
                    # Validate all parameters have values
                    if all(v.strip() for v in params.values()):
                        content_blocks.append(ToolUse(
                            name=tool_name,
                            params=params,
                            partial=False
                        ))
                    else:
                        # Treat as plain text if any parameters are empty
                        text_content = assistant_message[tool_start:tool_close_pos + len(tool_close_tag)].strip()
                        if text_content:
                            content_blocks.append(TextContent(
                                content=text_content,
                                partial=False
                            ))
                    i = tool_close_pos + len(tool_close_tag)
        else:
            # Handle text content
            text_start = i
            text_end = assistant_message.find('<', text_start)
            if text_end == -1:
                # No more tool uses, rest is text
                text_content = assistant_message[text_start:].strip()
                if text_content:
                    # Text at the end of message is considered partial unless it ends with a period
                    content_blocks.append(TextContent(
                        content=text_content,
                        partial=not text_content.strip().endswith('.')
                    ))
                break
            else:
                # Text before next tool use
                text_content = assistant_message[text_start:text_end].strip()
                if text_content:
                    # Text between tool uses is complete
                    partial = False
                    content_blocks.append(TextContent(
                        content=text_content,
                        partial=partial
                    ))
                i = text_end

    return content_blocks
