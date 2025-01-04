# DeepSeek Engineer 🐋

## About This Version

This is an upgraded version of the original [DeepSeek Engineer](https://github.com/Doriandarko/deepseek-engineer.git) project with significant improvements and new features. See [Upgrade Documentation](upgrades.md) for a detailed comparison.

## System Architecture

```sh
┌────────────────────────────────────────────────────────────┐
│                     DeepSeek Engineer                      │
├───────────────┬─────────────────────────┬──────────────────┤
│   Frontend    │      Core Services      │     Backend      │
│   (PyQt6)     │                         │    (Python)      │
├───────────────┤                         ├──────────────────┤
│ ┌───────────┐ │ ┌───────────────────┐   │ ┌──────────────┐ │
│ │   GUI     │ │ │  Conversation     │   │ │ DeepSeek API │ │
│ │Components │◄┼─┤    Handler        │◄──┼─┤  Client      │ │
│ └───────────┘ │ └───────────────────┘   │ └──────────────┘ │
│ ┌───────────┐ │ ┌───────────────────┐   │ ┌──────────────┐ │
│ │  Theme    │ │ │   File Operations │   │ │    Redis     │ │
│ │ Manager   │ │ │     Manager       │   │ │    Cache     │ │
│ └───────────┘ │ └───────────────────┘   │ └──────────────┘ │
└───────────────┴─────────────────────────┴──────────────────┘
```

## Core Features

- **Code Assistance**: Intelligent code generation and analysis
- **File Operations**: Real-time file creation and editing
- **Conversation Handling**: Context-aware conversation management
- **Tool Management**: Comprehensive tool system for various operations
- **API Integration**: Multi-instance API support with role-based configuration
- **State Management**: Persistent state tracking and management
- **Workspace Tracking**: Real-time workspace monitoring

## Quick Start

1. Install Python 3.11+
2. Create virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements/requirements.txt
   ```

4. Set API key:

   ```bash
   export DEEPSEEK_API_KEY=your_api_key
   ```

5. Run:

   ```bash
   python -m src.main
   ```

## Documentation

- [API Documentation](backend_README.md)
- [Frontend Documentation](frontend_README.md)
- [Upgrade Documentation](upgrades.md)

## Tools

The system provides these core tools:

1. **File Operations**
   - Create/Edit files
   - Read file contents
   - Search across files
   - Workspace tracking

2. **Code Analysis**
   - Syntax highlighting
   - Code comparison
   - Error diagnostics

3. **Conversation Management**
   - Context tracking
   - Instruction updates
   - Multi-instance communication

4. **System Operations**
   - State management
   - Performance monitoring
   - Security controls

## Security

- API key encryption
- Input validation
- Secure file operations
- Role-based access control

## Performance

- Asynchronous operations
- Efficient resource management
- Lazy loading of components
- Redis caching

## License

MIT License - See [LICENSE](LICENSE) for details
