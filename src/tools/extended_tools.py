from typing import Dict, Any

class ExtendedTool:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.editable = True

# Extended tools that can be modified
EXTENDED_TOOLS = {}
