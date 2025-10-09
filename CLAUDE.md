# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Server Management
- Start server: `gws server run`
- Start server with debug logging: `gws server run --log-level=DEBUG`

### Testing
- Run all tests: `gws server test all`
- Run specific test: `gws server test [TEST_FILE_NAME]` (without `.py` extension)
- Tests are located in `tests/test_gws_core/` directory

### Development Apps
- Run Streamlit app in dev mode: `gws streamlit run [CONFIG_FILE_PATH]`
- Run Reflex app in dev mode: `gws reflex run [CONFIG_FILE_PATH]`

### CLI Structure
The main CLI entry point is `gws_cli/gws_cli/main_cli.py` which provides commands for:
- `server`: Server operations (run, test, execute scenarios/processes)
- `brick`: Generate and manage bricks
- `task`: Generate task classes
- `streamlit`: Generate and run Streamlit applications
- `reflex`: Generate and run Reflex applications
- `dev-env`: Manage development environment (reset data)

## Architecture Overview

### Core Structure
- **FastAPI Application**: Main server runs on FastAPI with uvicorn (`src/gws_core/app.py`)
- **Brick-based Architecture**: This is the core "brick" of the Constellab data lab platform
- **Settings Configuration**: Uses `settings.json` for package dependencies and configuration

### Key Directories
- `src/gws_core/`: Main source code
  - `core/`: Core infrastructure (DB, exceptions, utils, models)
  - `task/`: Task execution framework and decorators
  - `resource/`: Resource management system (files, tables, views)
  - `protocol/`: Protocol/pipeline management
  - `scenario/`: Scenario execution and management
  - `impl/`: Implementations of standard resources and tasks
  - `apps/`: Application framework (Streamlit, Reflex)
  - `user/`: User management and authentication
  - `space/`: Multi-tenant space management
- `tests/test_gws_core/`: Comprehensive test suite
- `gws_cli/`: Command-line interface

### Key Components

#### Resource System
- Base classes in `src/gws_core/resource/`
- Standard implementations: Table, File, Folder, PlotlyResource, Note, etc.
- Resources have views for visualization and can be exported/imported

#### Task Framework
- Tasks are decorated classes that process resources
- Support for dynamic I/O, parameter specifications, and converters
- Tasks must extend : `/lab/user/bricks/gws_core/src/gws_core/task/task.py` and define inputs, outputs and parameters
- Located in `src/gws_core/task/`
- Tasks should have a detailed docstring at the class level in markdown format to explain their purpose. It should also explain the inputs, outputs, and parameters if their descriptions are not self-explanatory.

#### Protocol/Pipeline System
- Protocols define workflows connecting tasks
- Support for dynamic ports and complex execution graphs
- Service layer handles execution and state management

#### Database Layer
- Peewee ORM with custom base models
- Migration system for schema updates
- Transaction decorators for consistency

#### Testing Framework
- Custom test base classes: `BaseTestCase`, `BaseTestCaseLight`, `GTest`
- Data providers for test data access
- Comprehensive test coverage across all components

### Environment Management
The codebase supports multiple Python environment agents:
- Conda, Mamba, Pipenv for Python
- R support via Conda/Mamba
- Environment-specific shell proxies

### Application Development
- Streamlit apps: Framework for data science applications
- Reflex apps: Modern web application framework  
- Both support development mode with auto-reload

## Development Notes

### Dependencies
Dependencies are managed via `settings.json` rather than traditional requirements files. Install packages listed in the pip section manually or use the installation scripts.

### Test Data
Test data is located in `tests/testdata/` and accessible via `DataProvider.get_testdata_dir()`.

### Code Organization
- Use the existing typing system and decorators when creating new tasks/resources
- Follow the established patterns for database models and services
- Resource views should extend the base view classes
- New implementations go in `src/gws_core/impl/`