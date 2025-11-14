---
communityLink: https://constellab.community/bricks/gws_core/latest/doc/cli/introduction/df41517e-21ec-46d0-8693-72ee3470f454
---

# GWS CLI Documentation

## Overview
GWS CLI is a command-line interface for managing the Genestack Workspace (GWS) environment, including server operations, brick management, task generation, and application development.

## Introduction
```bash
gws [COMMAND] [OPTIONS]
```

## Global Options
- `--log-level [INFO|DEBUG|ERROR]` - Set global logging level for all commands (default: INFO)
- `-h, --help` - Show help message

---

## Commands

### server - Server Operations
Manage server operations including running the server, testing, and executing scenarios/processes.

#### server run
Start the development server.

**Options:**
- `--port TEXT` - Server port (default: "3000")
- `--settings-path TEXT` - Path to main settings file
- `--show-sql` - Log SQL queries in console (flag)
- `--allow-dev-app-connections` - Allow connections from apps running in dev mode (flag, dev mode only)

**Example:**
```bash
gws server run --port 3000 --log-level DEBUG
```

#### server test
Run tests for a specific brick or all bricks.

**Arguments:**
- `TEST_NAME` - Test file name(s) to launch (regex) or 'all' for all tests

**Options:**
- `--brick-name TEXT` - Brick name to test (uses current folder if omitted)
- `--show-sql` - Log SQL queries (flag)

**Example:**
```bash
gws server test test_table_copilot
gws server test all --brick-name gws_ai_toolkit
```

#### server run-scenario
Execute a specific scenario by ID.

**Options:**
- `--scenario-id TEXT` - Scenario ID (required)
- `--user-id TEXT` - User ID that runs the scenario (required)
- `--settings-path TEXT` - Path to main settings file
- `--show-sql` - Log SQL queries (flag)
- `--test` - Run in test mode (flag)

#### server run-process
Execute a specific process within a scenario.

**Options:**
- `--scenario-id TEXT` - Scenario ID (required)
- `--protocol-model-id TEXT` - Protocol model ID (required)
- `--process-instance-name TEXT` - Process instance name (required)
- `--user-id TEXT` - User ID (required)
- `--settings-path TEXT` - Path to main settings file
- `--show-sql` - Log SQL queries (flag)
- `--test` - Run in test mode (flag)

---

### brick - Brick Management
Generate and manage bricks (reusable data processing components).

#### brick generate
Generate a new brick with boilerplate code and structure.

**Arguments:**
- `NAME` - Brick name (snake_case recommended)

**Example:**
```bash
gws brick generate my_custom_brick
```

#### brick install-deps
Install pip dependencies from a brick's settings.json file.

**Arguments:**
- `SETTINGS_PATH` - Path to settings.json file

**Example:**
```bash
gws brick install-deps ./bricks/my_brick/settings.json
```

---

### task - Task Generation
Generate task classes for data processing workflows.

#### task generate
Generate a new task class with boilerplate code.

**Arguments:**
- `NAME` - Task class name (PascalCase)

**Options:**
- `--human-name TEXT` - Human-readable task name
- `--short-description TEXT` - Short description of the task

**Example:**
```bash
gws task generate MyDataProcessor --human-name "Data Processor" --short-description "Processes data files"
```

---

### streamlit - Streamlit Applications
Generate and run Streamlit applications.

#### streamlit run
Run a Streamlit app in development mode.

**Arguments:**
- `CONFIG_FILE_PATH` - Path to JSON config file

**Options:**
- `--enable-debugger` - Enable debugger in Streamlit app (flag)

**Example:**
```bash
gws streamlit run ./config.json --enable-debugger
```

#### streamlit generate
Generate a new Streamlit app with boilerplate code.

**Arguments:**
- `NAME` - App name (snake_case)

**Example:**
```bash
gws streamlit generate my_dashboard
```

---

### reflex - Reflex Applications
Generate and run Reflex applications.

#### reflex run
Run a Reflex app in development mode.

**Arguments:**
- `CONFIG_FILE_PATH` - Path to JSON config file

**Example:**
```bash
gws reflex run ./dev-config.json
```

#### reflex generate
Generate a new Reflex app.

**Arguments:**
- `NAME` - App name (snake_case)

**Options:**
- `--enterprise` - Generate enterprise Reflex app (flag)

**Example:**
```bash
gws reflex generate my_app --enterprise
```

#### reflex init
Alias for reflex generate.

---

### dev-env - Development Environment
Manage development environment data and settings.

#### dev-env reset
Reset development environment data (WARNING: irreversible).

**Interactive:** Prompts for confirmation before deleting data.

**Example:**
```bash
gws dev-env reset
```

---

### claude - Claude Code Integration
Manage Claude Code integration and configuration.

#### claude install
Install Claude Code CLI tool (automatically installs Node.js if needed).

**Example:**
```bash
gws claude install
```

#### claude update
Update Claude Code configuration for GWS (commands and settings). Only runs if Claude Code is already installed.

**Example:**
```bash
gws claude update
```

#### claude commands
Manage Claude Code commands.

**Options:**
- `--pull` - Copy GWS commands to `~/.claude/commands/gws-commands` (flag)
- `--list` - List all available GWS commands (flag)

**Example:**
```bash
gws claude commands --pull
gws claude commands --list
```

---

### copilot - GitHub Copilot Integration
Manage GitHub Copilot integration and configuration.

#### copilot update
Update GitHub Copilot configuration for GWS (instructions and settings).

**Example:**
```bash
gws copilot update
```

#### copilot instructions
Manage GitHub Copilot instructions.

**Options:**
- `--pull` - Copy GWS instructions to `~/.github/copilot/instructions/gws-instructions` (flag)
- `--list` - List all available GWS commands (flag)

**Example:**
```bash
gws copilot instructions --pull
gws copilot instructions --list
```

#### copilot commands
Alias for copilot instructions.

---

### utils - Utility Commands
Utility commands for development environment setup.

#### utils install node
Install Node.js using NVM (Node Version Manager).

**Example:**
```bash
gws utils install node
```

#### utils screenshot
Take a screenshot of a web application using Playwright.

**Options:**
- `--url, -u TEXT` - Base URL of the application (default: "http://localhost:8511")
- `--route, -r TEXT` - Route to navigate to (default: "/")
- `--output, -o TEXT` - Output path for screenshot (default: /lab/user/app_screenshot.png)
- `--no-logs` - Don't save console logs (flag)
- `--headless/--no-headless` - Run browser in headless mode (default: headless)

**Example:**
```bash
gws utils screenshot --route /dashboard --output ./screenshots/dashboard.png
gws utils screenshot --url http://localhost:3000 --no-headless
```

