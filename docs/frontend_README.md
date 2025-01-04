# DeepSeek Engineer - Frontend Documentation

## Component Architecture

```sh
┌────────────────────────────────────────────────────────────┐
│                        Main Window                         │
├───────────────┬─────────────────────────┬──────────────────┤
│   Toolbar     │      Content Area       │   Status Bar     │
├───────────────┤                         ├──────────────────┤
│ ┌───────────┐ │ ┌───────────────────┐   │ ┌──────────────┐ │
│ │ Theme     │ │ │  File Explorer    │   │ │ Status       │ │
│ │ Toggle    │ │ │                   │   │ │ Indicators   │ │
│ └───────────┘ │ └───────────────────┘   │ └──────────────┘ │
│ ┌───────────┐ │ ┌───────────────────┐   │                  │
│ │ Language  │ │ │  Code Editor      │   │                  │
│ │ Selector  │ │ │                   │   │                  │
│ └───────────┘ │ └───────────────────┘   │                  │
└───────────────┴─────────────────────────┴──────────────────┘
```

## UI Workflows

### File Editing Workflow

```sh
1. User Selects File
   │
   ▼
2. File Explorer
   │
   ▼
3. Backend API
   │
   ▼
4. File System
   │
   ▼
5. Code Editor
   │
   ▼
6. User Edits
   │
   ▼
7. Save Changes
   │
   ▼
8. User Confirmation
```

### Chat Interaction Workflow

```sh
1. User Query
   │
   ▼
2. Chat Interface
   │
   ▼
3. Backend API
   │
   ▼
4. DeepSeek API
   │
   ▼
5. Response Processing
   │
   ▼
6. Chat Display
   │
   ▼
7. User
```

## Technology Stack

- PyQt6 6.5+
- qasync
- Rich
- Pygments

## Development Setup

1. Install Dependencies:

   ```bash
   pip install PyQt6 qasync rich pygments
   ```

2. Development Tools:

   ```bash
   pip install pytest-qt mypy black
   ```

3. Environment Variables:

   ```bash
   export QT_SCALE_FACTOR=1.0
   export QT_AUTO_SCREEN_SCALE_FACTOR=1
   ```

## Component Responsibilities

1. **MainWindow**
   - Manages overall layout
   - Handles window events
   - Coordinates components

2. **Toolbar**
   - Provides quick access controls
   - Manages theme and language
   - Toggles view modes

3. **FileExplorer**
   - Displays file structure
   - Handles file selection
   - Manages file operations

4. **CodeEditor**
   - Displays and edits code
   - Provides syntax highlighting
   - Manages editor state

5. **Terminal**
   - Executes commands
   - Displays output
   - Manages shell interaction

6. **Chat**
   - Handles user queries
   - Displays responses
   - Manages conversation history
