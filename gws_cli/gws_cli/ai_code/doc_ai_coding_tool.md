# AI Coding Tools Setup Guide

This guide explains how to configure AI coding assistants (Claude Code and GitHub Copilot) to work effectively with the GWS Core development environment.

## Overview

The GWS Core environment provides specialized commands and instructions that help AI coding assistants understand the unique architecture of this platform. These commands enable AI assistants to:

- Generate Constellab Tasks (data processing components)
- Create Streamlit web applications
- Build Reflex web applications
- Convert Nextflow pipelines to Constellab Tasks
- Follow GWS Core best practices and conventions

**What are AI coding tools?**

AI coding tools like Claude Code and GitHub Copilot are AI assistants that help you write code faster. They can:
- Generate code based on your descriptions
- Explain existing code
- Debug issues
- Suggest improvements
- Follow project-specific guidelines

---

## Custom Commands & Instructions

### What are Custom Commands?

Custom commands are specialized instructions that teach AI assistants about your project's specific requirements, architecture, and best practices. They act as expert guides that help the AI:

1. **Understand your environment** - GWS Core architecture, file structure, and conventions
2. **Generate correct code** - Following established patterns and best practices
3. **Use the right tools** - CLI commands, testing frameworks, and development workflows
4. **Avoid common mistakes** - By encoding domain expertise into reusable prompts

### How Commands Work

When you invoke a command (e.g., `/gws-task-expert Create a table transformer`), the AI assistant:

1. Loads the specialized instruction file
2. Receives context about GWS Core architecture
3. Understands what you're trying to build
4. Generates code following best practices
5. Knows how to test and validate the result

### Benefits of Using Custom Commands

- **Faster development** - No need to explain GWS Core concepts every time
- **Consistent code quality** - AI follows the same patterns across your codebase
- **Reduced errors** - Built-in knowledge of common pitfalls
- **Better documentation** - AI generates properly formatted docstrings and comments
- **Easier onboarding** - New developers get AI assistance that knows your project

---

## Claude Code Setup

[Claude Code](https://docs.claude.com/en/docs/claude-code/overview) is Anthropic's official AI coding assistant that runs in your terminal or editor.

### Prerequisites

- Claude AI account

### Installation

To install Claude Code and configure it with all available GWS commands: `gws claude init`

This command installs Claude Code and configures it with the available commands.

### Using Claude Code

Open claude code in your terminal (`claude`) or claude code extension in your editor.

Use the `/` prefix to invoke commands: `/gws-<command-name> [your detailed description]`

### Verifying Installation

Check installed commands: `gws claude commands --list`

Check Claude Code version: `claude --version`

---

## GitHub Copilot Setup

[GitHub Copilot](https://github.com/features/copilot) is GitHub's AI coding assistant integrated into popular editors.

### Prerequisites

- GitHub account with Copilot access
- GitHub Copilot extension installed in VSCode.

### Installation

Pull GWS commands to the global GitHub Copilot prompts folder: `gws copilot commands --pull`

This command will copy GWS commands to `/lab/user/.github/prompts/`.


### Using GitHub Copilot

In the Copilot chat window, use the `/` prefix to invoke commands: `/gws-<command-name> [your detailed description]`

⚠️ Note: ensure that VsCode is opened in folder `/lab/user` to allow Copilot to have access to commands.

### Verifying Installation

List available GWS commands: `gws copilot commands --list`

## Available Commands

### 1. Task Expert (`/gws-task-expert`)

**Description:** Create or modify a Constellab Task that processes data resources

**Use Cases:**
- Creating new data processing tasks
- Modifying existing tasks
- Adding inputs/outputs/configuration
- Writing task tests

**Example:**
```
/gws-task-expert Create a TableTransposer task that takes a Table as input and returns the transposed Table as output
```

**What it provides:**
- Task decorator setup
- Input/output specifications
- Configuration parameters
- Run method implementation
- Logging and progress tracking
- Unit tests with TaskRunner
- Documentation in markdown

### 2. Streamlit App Developer (`/gws-streamlit-app-developer`)

**Description:** Create, develop, modify, or debug a Streamlit web application

**Use Cases:**
- Building interactive data apps
- Creating dashboards
- Implementing data visualization
- Adding UI components

**Example:**
```
/gws-streamlit-app-developer Create an app that allows users to upload a CSV file, display it in a table, and generate basic statistics
```

**What it provides:**
- Complete app structure
- State management with session_state
- Custom GWS Core components
- Development configuration
- Testing instructions
- Best practices for caching and performance

### 3. Reflex App Developer (`/gws-reflex-app-developer`)

**Description:** Create, develop, modify, or debug a Reflex web application

**Use Cases:**
- Building full-stack Python web apps
- Creating multi-page applications
- Implementing complex state management
- Adding routing and navigation

**Example:**
```
/gws-reflex-app-developer Create a multi-page app with a home page, data upload page, and visualization page
```

**What it provides:**
- Reflex app structure
- State management classes
- Page routing
- Component composition
- Development workflow
- Testing and debugging guidance

### 4. Agent Expert (`/gws-agent-expert`)

**Description:** Create or modify a Constellab Agent that processes data resources

**Use Cases:**
- Creating Python or R code snippets that process resources
- Quick data transformations without formal task structure
- Prototyping data analysis workflows
- Working with custom dependencies in virtual environments

**Example:**
```
/gws-agent-expert Create a Python agent that reads a CSV file, filters rows where sales > 1000, and outputs the result
```

**What it provides:**
- Basic Python agent structure
- Virtual environment agent configuration (Mamba/Conda/Pip)
- Input/output handling (sources, targets)
- Parameter management
- Environment files (environment.yml, Pipfile)
- Script conversion guidance

### 5. Nextflow to Task Converter (`/gws-nextflow-to-task`)

**Description:** Convert a Nextflow pipeline or process to Constellab Tasks

**Use Cases:**
- Migrating Nextflow workflows to Constellab
- Converting bioinformatics pipelines
- Translating container-based processes
- Preserving existing workflow logic in a new environment

**Example:**
```
/gws-nextflow-to-task Convert the nextflow/main.nf pipeline to Constellab tasks
```

**What it provides:**
- One task per Nextflow process
- Nextflow parameter mapping to config_specs
- Channel mapping to input/output specs
- Script block conversion to Python
- Container/dependency handling with virtual environments
- References to task-expert.md for detailed task information
- Complete conversion examples

---

## Best Practices

### When Using AI Coding Tools

1. **Be Specific in Your Requests**
   - ❌ "Create a task"
   - ✅ "Create a task that filters a Table resource based on a column value threshold"

2. **Mention Inputs and Outputs**
   - Specify resource types (Table, File, etc.)
   - Describe expected output format
   - Include any configuration parameters needed

3. **Reference Existing Patterns**
   - "Similar to TableTransposer in gws_core"
   - "Following the pattern in impl/table/tasks"

4. **Request Tests**
   - Ask for unit tests explicitly if not generated
   - Specify test scenarios to cover

5. **Iterate and Refine**
   - Review generated code
   - Ask for modifications or improvements
   - Request explanations for unclear parts


### Keeping Commands Up to Date

Commands are automatically updated on lab startup.
You can manually update them as needed.

```bash
# For Claude Code
gws claude update

# For GitHub Copilot
gws copilot update
```
---
