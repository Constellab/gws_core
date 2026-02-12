# Python Code Review Guidelines

Use these guidelines to review Python code. For each violation found, report the rule ID, severity, file, line number, and a brief explanation.

## Severity Levels

- **CRITICAL**: Must fix before merge. Security issues, data loss risks, crashes.
- **HIGH**: Should fix before merge. Bugs, significant maintainability issues.
- **MEDIUM**: Fix recommended. Style violations, minor design issues.
- **LOW**: Optional improvement. Suggestions for readability or best practices.

---

## 1. Code Style & Formatting


### PY-STYLE-001: Naming conventions
**Severity: MEDIUM**
- `snake_case` for functions, methods, variables, and modules.
- `PascalCase` for classes.
- `UPPER_SNAKE_CASE` for constants.
- Prefix private attributes with a single underscore `_`.
- Avoid single-character names except for counters (`i`, `j`) or coordinates (`x`, `y`).

### PY-STYLE-002: Import organization
**Severity: MEDIUM**
- Use absolute imports over relative imports.
- Avoid wildcard imports (`from module import *`).
- Don't use imports inside functions or methods unless necessary to avoid circular dependencies or reduce startup time.

### PY-STYLE-003: String formatting
**Severity: LOW**
- Prefer f-strings over `str.format()` or `%` formatting (Python 3.6+).
- Use f-strings for simple expressions only; extract complex logic to variables first.

---

## 2. Functions & Methods

### PY-FUNC-001: Function size and complexity
**Severity: HIGH**
- Functions should do one thing and do it well.
- Flag functions longer than 100 lines (excluding docstrings).
- Flag cyclomatic complexity above 10.

### PY-FUNC-002: Function arguments
**Severity: MEDIUM**
- Do not use mutable default arguments (`def f(items=[])`). Use `None` and initialize inside the function.
- Use type hints for all function signatures.

### PY-FUNC-003: Return consistency
**Severity: HIGH**
- A function should return a consistent type. Avoid returning `str` in one branch and `None` in another unless the return type is explicitly `str | None`.
- Avoid bare `return` mixed with `return value` in the same function.

---

## 3. Error Handling

### PY-ERR-001: Exception specificity
**Severity: HIGH**
- Never use bare `except:` or `except Exception:` without re-raising or logging.
- Catch the most specific exception possible.
- Bad: `except Exception: pass`
- Good: `except ValueError as e: logger.error("Invalid input: %s", e)`

### PY-ERR-002: Exception handling patterns
**Severity: HIGH**
- Do not use exceptions for flow control in expected paths.
- Use `try/except` blocks around the minimal code that can raise.
- Always include meaningful context in raised exceptions.

### PY-ERR-003: Avoid silent failures
**Severity: CRITICAL**
- Never swallow exceptions silently (`except: pass`).
- At minimum, log the exception before continuing.

---

## 4. Security

### PY-SEC-001: No hardcoded secrets
**Severity: CRITICAL**
- No passwords, API keys, tokens, or secrets in source code.
- Use environment variables or a secrets manager.

### PY-SEC-002: Dangerous functions
**Severity: CRITICAL**
- Do not use `eval()`, `exec()`, or `compile()` with untrusted input.
- Avoid `pickle.load()` on untrusted data; prefer `json` for serialization.
- Avoid `os.system()` and `subprocess.run(..., shell=True)` with user-provided input.

### PY-SEC-003: Path traversal
**Severity: CRITICAL**
- Validate file paths to prevent directory traversal attacks.
- Use `pathlib.Path.resolve()` and verify the result is within the expected directory.

---

## 5. Data Structures & Types

### PY-TYPE-001: Type hints
**Severity: MEDIUM**
- Use type hints for function signatures (parameters and return types).
- Use `typing` module constructs for complex types (`list[str]`, `dict[str, int]`, `T | None`, `A | B`).
- Prefer built-in generics (`list`, `dict`, `set`, `tuple`) over `typing.List`, `typing.Dict` etc. (Python 3.9+).

### PY-TYPE-002: Appropriate data structures
**Severity: MEDIUM**
- Use dataclasses or named tuples instead of plain dicts for structured data with known fields.

---

## 6. Resource Management

### PY-RES-001: Context managers
**Severity: HIGH**
- Always use `with` statements for file I/O, database connections, locks, and network sockets.
- Bad: `f = open("file.txt"); data = f.read(); f.close()`
- Good: `with open("file.txt") as f: data = f.read()`

---

## 7. Logging & Observability

### PY-LOG-001: Use the logging module
**Severity: MEDIUM**
- Use `Logger` from `gws_core` instead of `print()` for any output that should persist beyond development.
---

## 8. Constellab specific guidelines

### PY-CONST-001: Brick structure
**Severity: HIGH**
Recommended project structure for bricks:
```
/my_brick/
├── src/              # Source code
├── tests/            # tests
└── settings.json/    # Brick configuration and dependencies
```

- in `settings.json`, it is not recommended to have many dependencies of standard dependencies like `pandas`, `numpy`... unless using version range. If multiple dependencies are needed, consider using a virtual environment.
- always import from other bricks using top level imports (e.g. `from gws_core import some_function`) rather lower level imports (e.g. `from .gws_core.my_function import some_function`)

### PY-CONST-002: App code
- code for `streamlit` or `reflex` apps must be in a folder prefixed with `_` (e.g. `/_streamlit_app/`) to indicate that it is not meant to be run on lab startup.
- imports from `gws_reflex_main` and `gws_reflex_env_main` are only allowed inside `reflex` app code.
- imports from `gws_streamlit_main` and `gws_streamlit_env_main` are only allowed inside `streamlit` app code.
- inside app code, use relative imports for modules within the same app folder (e.g. `from .utils import some_function`) and absolute imports for external bricks or packages (e.g. `from gws_core import some_function`).

### PY-CONST-003: Shell
- when running shell commands it is recommended to use `ShellProxy` class from `gws_core` instead of `subprocess` or `os.system` to ensure better security and error handling.
- when a virtual environment is required, it is recommended to use `MambaShellProxy`, `CondaShellProxy` or `PipShellProxy` from `gws_core` instead of manually activating the environment in the shell command.
- if there are some python scripts meant to be run inside a virtual environment, the script or parent folder must be named with a `_` prefix to indicate that it is not meant to be run on lab startup (e.g. `/_scripts/run_in_venv.py`).

### PY-CONST-004: Specific code
- if the code is related to a Constellab task, refer to the [gws-task-expert.md](./gws-task-expert.md) guidelines.
- if the code is related to a streamlit app, refer to the [gws-streamlit-app-developer.md](./gws-streamlit-app-developer.md) guidelines.
- if the code is related to a reflex app, refer to the [gws-reflex-app-developer.md](./gws-reflex-app-developer.md) guidelines.