# AI Code Instructions

This file provides guidance to AI tools when working with code in this repository.

## Workspace Structure
```
/lab/user/
├── bricks/                # Directory containing all bricks (libraries)
├── data/                  # Data directory
└── notebooks/             # Jupyter notebooks
```

Each brick has its own `CLAUDE.md` for brick-specific guidance. 

## Development Commands


### Server Management
- Start server: `gws server run`
- Start server with debug logging: `gws server run --log-level=DEBUG`

### Testing
- **Run all tests**: `gws server test all`
- **Run specific test**: `gws server test [TEST_FILE_NAME]` (without `.py` extension, run from the brick directory)
- Tests are located in each brick's `tests/` directory
- Example: `cd bricks/gws_ai_toolkit && gws server test test_table_copilot`

### Development Apps
- Run Streamlit app in dev mode: `gws streamlit run [CONFIG_FILE_PATH]`
- Run Reflex app in dev mode: `gws reflex run [CONFIG_FILE_PATH]`

### Brick Management
- **Generate new brick**: `gws brick generate [NAME]`
- **Generate task class**: `gws task generate`
- **Install dependencies**: Dependencies are defined in each brick's `settings.json`

### Constellab Chat Expert
- **Ask a question**: `gws community ask-chatbot "My question?"`
- This is a RAG-powered assistant that can answer:
  - Product questions about the Constellab platform (features, concepts, workflows)
  - Technical questions about developing on the platform (tasks, resources, protocols)
  - Questions about the gws_core library (classes, methods, patterns, best practices)
  - API usage, conventions, and coding guidelines
- Use this tool BEFORE writing code if you have any doubt about how something works on Constellab

### Best Practices

#### General Rules
- Always read files before editing them. Never assume file contents — use the Read tool first to understand current state
- Don't over-explore the codebase. When the task is clear (e.g., write documentation, create a file), start working immediately rather than reading unrelated files
- Follow existing coding conventions and styles. When implementing new features, look for similar existing implementations and match their approach (e.g., file storage patterns, SDK object usage, import styles)
- Write comprehensive docstrings for classes and methods
- Do not export classes in the __init__.py files unless necessary
- Always place import statements at the top of the file (module level). Never import inside functions, methods, or other non-top-level scopes

#### Refactoring Rules
- When refactoring or restructuring files, verify all existing functionality is preserved. After moving/rewriting code, check that no functions, imports, or features were accidentally removed
- After large refactors, grep for references to functions from the original file to catch anything broken

#### UI/Styling Rules
- When asked to remove a color or style, remove the property entirely rather than replacing with another explicit value. Prefer framework defaults over explicit alternatives

