# Task Process Creator Expert

This command specializes in creating and modifying Constellab Tasks following best practices and conventions.

## What is a Constellab Task?

A task is a special function that works with Constellab object. It contains a run method to execute any code. It takes resources as inputs and resources as outputs. It also takes a configuration object. 

For example, the object `TableTransposer` is a task that takes a `Table` as input, transpose it and return the transposed `Table` as output.

## Creating New Tasks

### Task Generation Command

```bash
gws task generate [PascalCase name] --human-name "Human readable name" --short-description "What the task does"
```

## Modifying Existing Tasks

When modifying an existing task, the agent should:

1. **Read the task file** to understand current implementation
2. **Identify the change request** (add input, modify logic, add config param, etc.)
3. **Assess backward compatibility**:
   - **NEVER change unique_name** in @task_decorator (breaks all existing protocols)
   - Avoid removing inputs/outputs or changing their types
   - Avoid removing config parameters
4. **Make the modifications**:
   - Update human_name/short_description as needed
   - Add/modify input_specs, output_specs, config_specs
   - Update run method implementation
   - Add proper logging and error handling
5. **Update tests**:
   - Modify existing tests to cover changes
   - Add new test cases for new functionality
6. **Update documentation** in docstrings

### Safe Modifications (Non-Breaking)
- ✅ Add optional inputs/outputs (`optional=True`)
- ✅ Add config parameters with default values
- ✅ Enhance run method logic (maintaining output compatibility)
- ✅ Add logging, progress updates, error handling
- ✅ Update human_name, short_description, docstrings
- ✅ Implement check_before_run() or run_after_task()
- ✅ Improve performance or code quality

### Breaking Changes (Avoid or Warn User)
- ❌ Changing unique_name in decorator
- ❌ Removing existing inputs/outputs
- ❌ Changing resource_types of existing inputs/outputs
- ❌ Removing config parameters
- ❌ Changing output dictionary keys
- ❌ Changing output resource structure (if other tasks depend on it)

### Modification Workflow
1. Search for task file using Glob or Grep
2. Read task file to understand current structure
3. Read associated test file (if exists)
4. Make required changes to task
5. Update or create tests
6. Verify all specs are consistent

## Task Structure Requirements

A Constellab Task must:

1. **Extend the Task class** (imported from gws_core)
2. **Use @task_decorator** with:
   - `unique_name`: Never change after release (used for task identification)
   - `human_name`: Display name in playground
   - `short_description`: Brief explanation of task purpose
   - Optional: `hide=True` to hide from UI

3. **Define input_specs**: Dictionary of InputSpec objects
   - Keys identify inputs in the run method
   - InputSpec parameters:
     - `resource_types`: Resource class or list of classes
     - `human_name`: Display name
     - `short_description`: Input description
     - `optional`: Allow None or disconnected input

4. **Define output_specs**: Dictionary of OutputSpec objects
   - Keys must match return dictionary keys
   - OutputSpec parameters:
     - `resource_types`: Resource class or list of classes
     - `human_name`: Display name
     - `short_description`: Output description
     - `optional`: Can return None
     - `constant`: Output not modified from input
     - `sub_class`: Accept child classes

5. **Define config_specs**: Dictionary of Param objects
   - Keys used to retrieve values via `params.get_value('key')`
   - Common Param types:
     - `StrParam`: String with optional min/max length, allowed_values
     - `IntParam` / `FloatParam`: Numeric with optional min/max
     - `BoolParam`: Checkbox
     - `ListParam`: Multiple string values
     - `TagsParam`: Tag selection
     - `ParamSet`: Grouped parameters with multiple occurrences
     - `DictParam`: For hidden parameters only
   - Common Param options:
     - `default_value`: Default (makes optional=True)
     - `optional`: Allow None value
     - `visibility`: 'public', 'protected', 'private'
     - `allowed_values`: Restrict choices (list)
     - `unit`: Measurement unit
   - When the param is a choice from a list of values, use `allowed_values` to restrict choices (usually for StrParam). This should be a list of objects of the same type as the param (e.g. list of strings for StrParam).

6. **Implement run method**:
   ```python
   def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
       # Retrieve inputs
       my_input = inputs['input_key']

       # Get config values
       my_param = params.get_value('param_key')

       # Process and return outputs
       return {'output_key': output_resource}
   ```

## Task Methods

### Logging
- `self.log_info_message('message')`: Info log
- `self.log_success_message('message')`: Success log
- `self.log_warning_message('message')`: Warning log
- `self.log_error_message('message')`: Error log
- `self.update_progress_value(value, 'message')`: Progress (0-100)

### Optional Overrides
- `check_before_run()`: Return CheckBeforeTaskResult to validate before execution
- `run_after_task()`: Cleanup after task completion
- `create_tmp_dir()`: Create auto-deleted temporary directory

### External Data
```python
from gws_core import TaskFileDownloader

file_downloader = TaskFileDownloader(self.get_brick_name(), self.message_dispatcher)
file_path = file_downloader.download_file_if_missing("url", "filename.ext")
```

## File Organization

- **One task per file**, named in snake_case matching task name
- Example: `RobotMove` class → `robot_move.py`
- Test file: `tests/test_robot_move.py` (must start with `test_`)

## Unit Testing

Create tests in `tests/` folder using TaskRunner:

```python
from gws_core import TaskRunner
from unittest import TestCase

class TestMyTask(TestCase):
    def test_my_task(self):
        # Create input resources
        input_resource = MyResource()

        # Configure and run task
        runner = TaskRunner(
            task_type=MyTask,
            params={'param_key': value},
            inputs={'input_key': input_resource}
        )
        outputs = runner.run()

        # Validate outputs
        result = outputs['output_key']
        self.assertEqual(result.some_value, expected_value)
```

For tests requiring database, extend `BaseTestCase` instead of `TestCase`.

## Documentation

Add markdown docstrings to task class:

```python
@task_decorator("MyTask", human_name="My Task")
class MyTask(Task):
    """
    This task performs **important** operations.

    ## Usage
    - Input: Description
    - Output: Description

    ## Notes
    Additional information...
    """
```

## Best Practices

ALWAYS START THE CLASS DOCSTRING WITH : '[Generated by Task Expert Agent]'

1. **Never change unique_name** after release
2. **Use absolute imports** in test files
3. **Validate outputs** match output_specs keys
4. **Provide helpful descriptions** for all specs
5. **Write unit tests** for all tasks
6. **Document with markdown** in docstrings
7. **Use TaskFileDownloader** for external data
8. **Log progress** for long-running tasks
9. **Clean up** in run_after_task()
10. **Test in dev environment** after unit tests pass

## Reference

The Task class implementation is available at [${GWS_CORE_SRC}/task/task.py](${GWS_CORE_SRC}/task/task.py).
Example for task manipulating tables is available at [${GWS_CORE_SRC}/impl/table/tasks](${GWS_CORE_SRC}/impl/table/tasks) Example for Table transformers : [${GWS_CORE_SRC}/impl/table/transformers](${GWS_CORE_SRC}/impl/table/transformers).
Basic resources and tasks examples are available at [${GWS_CORE_SRC}/impl](${GWS_CORE_SRC}/impl)

## Online Documentation Resources


When additional information is needed, the agent can reference these Constellab documentation pages:

### 1. Task Documentation (Complete Reference)
**URL**: https://constellab.community/bricks/gws_core/latest/doc/developer-guide/task/task/6eb34e1c-6ae2-41bc-ae22-dc5cf962ee23

**Contains**:
- What is a task and how tasks work in workflows
- Complete guide to creating tasks (decorator, specs, run method)
- Detailed inputs/outputs specifications (InputSpec, OutputSpec parameters)
- Configuration system (all Param types: StrParam, IntParam, FloatParam, BoolParam, ListParam, TagsParam, ParamSet, DictParam)
- Task special methods (logging, progress, check_before_run, run_after_task, create_tmp_dir)
- Testing with TaskRunner and unit tests
- Documentation best practices with markdown docstrings
- Deploying tasks
- Using external data with TaskFileDownloader

### 2. Create Your First Task (Tutorial)
**URL**: https://constellab.community/bricks/gws_core/latest/doc/developer-guide/task/create-your-first-task/3be4ac25-2591-417f-b246-26b5b5495281

**Contains**:
- Step-by-step tutorial for creating a TableFactor task
- Specifying task inputs, outputs, and configuration
- Writing the run method with practical example
- Creating unit tests with TaskRunner
- Running and debugging tests
- Testing tasks in the dev environment interface
- Uploading CSV files and creating scenarios

### 3. Virtual Environment and Command Line (ShellProxy)
**URL**: https://constellab.community/bricks/gws_core/latest/doc/developer-guide/task/virtual-environment-and-command-line/527bc4c0-094d-47f0-8e4a-5578d004cf8f

**Contains**:
- ShellProxy classes for running shell commands from tasks
- PipShellProxy for pip virtual environments
- CondaShellProxy and MambaShellProxy for conda/mamba environments
- Creating and managing virtual environments with unique names
- Environment storage location and management through Monitoring page
- Running commands within environments and logging outputs
- Recreating environments when dependencies change
- Example code for executing shell commands in tasks

### 4. More Advanced Task (BLAST Example)
**URL**: https://constellab.community/bricks/gws_core/latest/doc/developer-guide/task/more-advanced-task/4c063ff1-8bef-49f0-985a-205edfeadeda

**Contains**:
- Advanced task example executing BLAST bioinformatics tool
- Downloading external data files with TaskFileDownloader
- Creating Conda environments for specialized tools
- Using CondaShellProxy to run commands in isolated environments
- Data preparation techniques (unzipping, file size limiting)
- Running complex command-line tools with parameters
- Resource cleanup with run_after_task method
- Multi-stage data processing workflows
- Error handling for command-line operations

**Usage**: The agent should use WebFetch to retrieve specific information from these URLs when encountering complex scenarios or needing detailed examples beyond the basic documentation in this file.

## Task

$ARGUMENTS
