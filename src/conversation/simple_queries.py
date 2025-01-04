"""Module for handling simple queries without requiring API calls."""

from typing import Dict, Optional
from ..models.schemas import AssistantResponse


class SimpleQueryHandler:
    """Handler for simple queries that don't require API calls."""

    # Define partial matches as a class variable
    _partial_matches = {
        "version": ["version", "what version", "which version", "what's your version", "current version", "running version"],
        "capabilities": ["capabilities", "what can you do", "what are your capabilities", 
                       "show me your capabilities", "tell me your capabilities", "what do you support",
                       "what are you able to do", "what functions do you have"],
        "commands": ["commands", "show commands", "list commands", "what commands", "available commands",
                    "supported commands", "what can I run"],
        "features": ["features", "what features", "what features do you have", "what functionality",
                    "what options", "what tools"],
        "status": ["status", "what is your status", "how are you", "are you working", "are you online",
                  "are you available", "are you ready"],
        "hello": ["hello", "hi", "hello!", "hi there", "hey", "greetings", "good day"],
        "help": ["help", "need help", "can you help", "assist me", "support", "guidance", "advice"],
        "info": ["info", "information", "details", "tell me about", "explain", "describe"]
    }

    _queries: Dict[str, str] = {
        # Identity and capabilities
        "who are you": "I am DeepSeek Engineer, a software engineering assistant specializing in programming, debugging, and development tasks.",
        "what can you do": "I can help with:\n- Writing and reviewing code\n- Debugging and testing\n- Creating new projects\n- Improving existing code\n- Following best practices\n- Using various programming languages and frameworks",
        "help": "I can help you with programming tasks, code reviews, debugging, and software development. Just describe what you need help with, and I'll assist you using my tools and capabilities.",
        # Greetings
        "hello": "Hello! I'm DeepSeek Engineer, ready to assist you with your software development tasks.",
        "hi": "Hi! I'm DeepSeek Engineer, ready to help you with programming and development tasks.",
        # Features and capabilities
        "capabilities": "I can help with:\n- Code writing and review\n- Debugging and testing\n- Project creation\n- Code improvements\n- Best practices\n- Multiple languages",
        "features": "Key features:\n- Code generation/editing\n- File operations\n- Testing tools\n- Browser automation\n- Response streaming",
        # Commands and system info
        "commands": "Available commands:\n- /add path/to/file - Include a file in the conversation\n- /create_instance ID ROLE API_KEY - Create new API instance\n- /list_instances - Show active instances\n- /select_instance ID - Switch to specific instance\n- /communicate SENDER_ID RECEIVER_ID MESSAGE - Send message between instances",
        "version": "I am running the latest version of DeepSeek Engineer with streaming support and structured output capabilities.",
        "status": "I am operational and ready to assist you with your software development tasks.",
        # Exit and thank you responses
        "exit": "Goodbye! Feel free to return when you need assistance with software development.",
        "quit": "Goodbye! Feel free to return when you need assistance with software development.",
        "thanks": "You're welcome! Let me know if you need any further assistance with your development tasks.",
        "thank you": "You're welcome! Let me know if you need any further assistance with your development tasks.",
        # Additional variations
        "show commands": "Available commands:\n- /add path/to/file - Include a file in the conversation\n- /create_instance ID ROLE API_KEY - Create new API instance\n- /list_instances - Show active instances\n- /select_instance ID - Switch to specific instance\n- /communicate SENDER_ID RECEIVER_ID MESSAGE - Send message between instances",
        "what version": "I am running the latest version of DeepSeek Engineer with streaming support and structured output capabilities.",
        "your status": "I am operational and ready to assist you with your software development tasks.",
        # New entries
        "what do you support": "I support various programming languages and frameworks including Python, JavaScript, TypeScript, React, Node.js, and more. I can help with code writing, debugging, testing, and project setup.",
        "what are you able to do": "I can assist with:\n- Writing and reviewing code\n- Debugging and testing\n- Creating new projects\n- Improving existing code\n- Following best practices\n- Using various programming languages and frameworks",
        "what functions do you have": "My main functions include:\n- Code generation and editing\n- File operations\n- Testing tools\n- Browser automation\n- Response streaming\n- Project setup and configuration",
        "available commands": "Available commands:\n- /add path/to/file - Include a file in the conversation\n- /create_instance ID ROLE API_KEY - Create new API instance\n- /list_instances - Show active instances\n- /select_instance ID - Switch to specific instance\n- /communicate SENDER_ID RECEIVER_ID MESSAGE - Send message between instances",
        "supported commands": "Supported commands:\n- /add path/to/file - Include a file in the conversation\n- /create_instance ID ROLE API_KEY - Create new API instance\n- /list_instances - Show active instances\n- /select_instance ID - Switch to specific instance\n- /communicate SENDER_ID RECEIVER_ID MESSAGE - Send message between instances",
        "what can I run": "You can run these commands:\n- /add path/to/file - Include a file in the conversation\n- /create_instance ID ROLE API_KEY - Create new API instance\n- /list_instances - Show active instances\n- /select_instance ID - Switch to specific instance\n- /communicate SENDER_ID RECEIVER_ID MESSAGE - Send message between instances",
        "are you working": "Yes, I am operational and ready to assist you with your software development tasks.",
        "are you online": "Yes, I am online and available to help with your development needs.",
        "are you available": "Yes, I am available and ready to assist you with your software development tasks.",
        "are you ready": "Yes, I am ready to help with your programming and development tasks.",
        "greetings": "Greetings! I'm DeepSeek Engineer, ready to assist you with your software development tasks.",
        "good day": "Good day! I'm DeepSeek Engineer, ready to help you with programming and development tasks.",
        "support": "I can help you with programming tasks, code reviews, debugging, and software development. Just describe what you need help with, and I'll assist you using my tools and capabilities.",
        "guidance": "I can provide guidance on programming tasks, code reviews, debugging, and software development. Let me know what you need help with.",
        "advice": "I can offer advice on programming best practices, code structure, debugging techniques, and development workflows. What would you like advice on?",
        "info": "I can provide information about programming languages, frameworks, development tools, and best practices. What would you like to know?",
        "information": "I can provide information about programming languages, frameworks, development tools, and best practices. What would you like to know?",
        "details": "I can provide detailed information about programming concepts, code implementation, debugging techniques, and development workflows. What would you like details about?",
        "tell me about": "I can tell you about programming languages, frameworks, development tools, and best practices. What would you like to know about?",
        "explain": "I can explain programming concepts, code implementation, debugging techniques, and development workflows. What would you like me to explain?",
        "describe": "I can describe programming concepts, code implementation, debugging techniques, and development workflows. What would you like me to describe?"
    }

    @staticmethod
    def handle_query(query: str) -> Optional[AssistantResponse]:
        """
        Handle a simple query if possible.

        Args:
            query: The user's query string

        Returns:
            AssistantResponse if query can be handled, None otherwise
        """
        # Normalize query
        normalized_query = query.lower().strip("?!. ")

        # Check for exact matches first
        if normalized_query in SimpleQueryHandler._queries:
            response = SimpleQueryHandler._queries[normalized_query]
            return AssistantResponse(
                assistant_reply=response,
                files_to_create=[],
                files_to_edit=[],
                tool_uses=[],
            )

        # Check for partial matches with word boundaries
        for base_query, variations in SimpleQueryHandler._partial_matches.items():
            if any(f" {variation} " in f" {normalized_query} " for variation in variations):
                response = SimpleQueryHandler._queries.get(base_query)
                if response:
                    return AssistantResponse(
                        assistant_reply=response,
                        files_to_create=[],
                        files_to_edit=[],
                        tool_uses=[]
                    )
        
        # No match found
        return None

    @staticmethod
    def is_simple_query(query: str) -> bool:
        """
        Check if a query can be handled without API calls.

        Args:
            query: The user's query string

        Returns:
            bool: True if query can be handled locally, False otherwise
        """
        # Only return True for exact matches and specific partial matches
        normalized_query = query.lower().strip("?!. ")
        
        # Check exact matches
        if normalized_query in SimpleQueryHandler._queries:
            return True
            
        # Check specific partial matches with word boundaries
        for variations in SimpleQueryHandler._partial_matches.values():
            if any(f" {variation} " in f" {normalized_query} " for variation in variations):
                return True
                
        return False
