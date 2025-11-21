# Agent Code Expert

This command specializes in creating and modifying Constellab Agents following best practices and conventions.

## Code Generation Requirements

When generating agent code, follow these rules:

1. **Language Selection**:
   - **Python**: Default language unless user explicitly requests R
   - **R**: Only when user explicitly asks for R code (ALWAYS requires Mamba R Virtual Environment Agent)

2. **Agent Type Selection**:
   - **Basic Python Agent**: Use by default when all dependencies are pre-installed
   - **Mamba Virtual Environment Agent**: Use when custom Python dependencies needed
   - **Mamba R Virtual Environment Agent**: REQUIRED for ALL R code

3. **Environment Files** (Critical for Virtual Agents):
   - **ALWAYS generate environment.yml** alongside virtual environment agent code
   - **Prefer Mamba/Conda** (environment.yml) over Pip (Pipfile)
   - **For R agents**: ALWAYS use environment.yml with R dependencies

4. **Output Paths** (Virtual Agents Only):
   - **ALWAYS use RELATIVE paths** in target_paths
   - **Example**: `target_paths = ['output.csv', 'results.png']` ✓
   - **NEVER use absolute paths or target_folders**: `target_paths = ['/abs/path/output.csv']` ✗

## What is a Constellab Agent?

An agent is an executable Python or R code snippet that processes resources dynamically within a task. Agents allow you to execute any Python or R code on the fly without creating a formal Task class. They can modify data structures like tables, generate visualizations, or invoke external libraries directly.

Agents are particularly useful for:
- Quick data transformations and analysis
- Prototyping before creating formal tasks
- One-off operations that don't require a reusable task
- Working with external libraries and dependencies in isolated environments

## Agent Types

### 1. Basic Python Agent
- **Purpose**: Execute Python code with pre-installed packages
- **Best for**: Simple operations on existing resources without external dependencies
- **Environment**: Runs in the standard task environment
- **Inputs/Outputs**: Can work with any resource type (Table, File, Folder, etc.)
- **Default choice**: Use this by default unless custom dependencies are needed

### 2. Virtual Environment Agent (Mamba/Conda/Pip)
- **Purpose**: Execute code in isolated environments with custom dependencies
- **Best for**: Tasks requiring specific packages, versions, or complex dependency trees
- **Environment**: Isolated virtual environment (prefer Mamba, then Conda, then Pip)
- **Inputs/Outputs**: **Only File or Folder resources** (runs outside normal task context)
- **Types**:
  - **Mamba Environment Agent** (PREFERRED): Uses environment.yml for mamba dependencies - fastest and most reliable
  - **Conda Environment Agent**: Uses environment.yml for conda dependencies
  - **Pip Environment Agent**: Uses Pipfile for dependency management - use only if packages unavailable in conda/mamba
  - **Mamba R Agent**: Runs R scripts with mamba environment - REQUIRED for all R code

### 3. Streamlit Agent
- **Purpose**: Generate interactive dashboards using Streamlit
- **Best for**: Data visualization, interactive reports, web-based interfaces
- **Environment**: Standard or virtual environment
- **Outputs**: Produces a Streamlit dashboard resource

## Converting Python Scripts to Agents

When converting an existing Python script to a Constellab agent, follow these steps:

### Step 1: Analyze Dependencies
1. Identify all import statements and external packages
2. Determine if packages are available in the standard environment
3. Choose agent type:
   - **Basic Python Agent**: All dependencies pre-installed (DEFAULT for Python)
   - **Mamba Virtual Environment Agent**: Custom dependencies needed (generate environment.yml)
   - **Mamba R Virtual Environment Agent**: ANY R code (REQUIRED - always generate environment.yml)

### Step 2: Adapt Input/Output Handling

#### For Basic Python Agent:
```python
# Original script with hardcoded paths
import pandas as pd
data = pd.read_csv('/path/to/input.csv')
result = data.groupby('category').sum()
result.to_csv('/path/to/output.csv')

# Converted to agent (assuming Table input/output)
# Configure 1 input (Table) and 1 output (Table) in Agent Dashboard

from gws_core import Table

# Access input from sources list
input_table = sources[0]
input_df = input_table.get_data()

# Process
result = input_df.groupby('category').sum()

# Set output as list
output_table = Table(result)
targets = [output_table]
```

#### For Virtual Environment Agent:
```python
# Original script with hardcoded paths
import pandas as pd
data = pd.read_csv('/path/to/input.csv')
result = data.groupby('category').sum()
result.to_csv('/path/to/output.csv')

# Converted to virtual environment agent
# Input: File resources connected to agent
# Output: File resources (must match targets array length)

import pandas as pd

# source_paths is provided by framework (list of input file paths)
input_file = source_paths[0]

# Process
data = pd.read_csv(input_file)
result = data.groupby('category').sum()

# target_folders is provided by framework (list of output folder paths)
output_file = f"{target_folders[0]}/result.csv"
result.to_csv(output_file)

# Set output paths
targets = [output_file]
```

### Step 3: Handle Parameters
```python
# Original script with hardcoded values
threshold = 100
column_name = 'sales'

# Converted to agent with parameters
# Create parameters in Agent Dashboard:
# - Name: "threshold", Type: Number, Default: 100
# - Name: "column_name", Type: String, Default: "sales"

# Access in code
threshold = params['threshold']
column_name = params['column_name']
```

### Step 4: Add Error Handling
```python
# Add robust error handling for agent execution
try:
    # Your agent code here
    result = process_data(input_data)
    targets['output'] = result
except Exception as e:
    # Log error (visible in agent execution logs)
    print(f"Error processing data: {str(e)}")
    raise
```

### Complete Conversion Example

#### Original Python Script:
```python
# analyze_sales.py
import pandas as pd
import matplotlib.pyplot as plt

# Hardcoded inputs
input_file = '/data/sales.csv'
output_dir = '/results/'
min_sales = 1000

# Process
df = pd.read_csv(input_file)
filtered = df[df['sales'] >= min_sales]
summary = filtered.groupby('region')['sales'].sum()

# Save results
summary.to_csv(f"{output_dir}/summary.csv")

# Create visualization
plt.figure(figsize=(10, 6))
summary.plot(kind='bar')
plt.savefig(f"{output_dir}/chart.png")
```

#### Converted to Basic Python Agent:
```python
# Agent with dynamic parameters and inputs/outputs
# Parameters (configured in Agent Dashboard):
# - "min_sales": Number, default=1000
# Inputs: 1 Table resource (configured in Agent Dashboard)
# Outputs: 2 resources - Table and File (configured in Agent Dashboard)

import pandas as pd
import matplotlib.pyplot as plt
import os
from gws_core import Table, File

# Get parameter
min_sales = params['min_sales']

# Get input from sources list
sales_data = sources[0]
df = sales_data.get_data()

# Process
filtered = df[df['sales'] >= min_sales]
summary = filtered.groupby('region')['sales'].sum()

# Create summary table output
summary_table = Table(summary.reset_index())

# Create chart output
chart_path = os.path.join(working_dir, 'chart.png')
plt.figure(figsize=(10, 6))
summary.plot(kind='bar')
plt.savefig(chart_path)
plt.close()
chart = File(chart_path)

# Set outputs as list (order must match output configuration)
targets = [summary_table, chart]
```

#### Converted to Virtual Environment Agent (Mamba):
```python
# Virtual Environment Agent (for custom dependencies)
# ALWAYS generate environment.yml file alongside the agent code

# Parameters (configured in Agent Dashboard):
# - "min_sales": Number, default=1000
# Inputs: File resources (CSV file)
# Outputs: 2 File resources (CSV summary + PNG chart)

import pandas as pd
import matplotlib.pyplot as plt
import os

# Get parameter
min_sales = params['min_sales']

# Get input file path
input_file = source_paths[0]

# Process
df = pd.read_csv(input_file)
filtered = df[df['sales'] >= min_sales]
summary = filtered.groupby('region')['sales'].sum()

# Save summary with RELATIVE paths (no target_folders)
output_csv = 'summary.csv'
summary.to_csv(output_csv)

# Create and save chart with RELATIVE paths
output_chart = 'chart.png'
plt.figure(figsize=(10, 6))
summary.plot(kind='bar')
plt.savefig(output_chart)
plt.close()

# Set output paths - use RELATIVE paths (must match number of outputs configured)
target_paths = [output_csv, output_chart]
```

**environment.yml** (ALWAYS generate this file):
```yaml
name: sales_analysis_agent
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.11
  - pandas>=2.0.0
  - matplotlib>=3.7.0
```

## Agent Structure Requirements

### Basic Python Agent
1. **Access inputs**: Use `sources` list (ordered by input configuration)
   ```python
   # If first input is a Table resource
   input_table = sources[0]
   df = input_table.get_data()
   ```

2. **Access parameters**: Use `params` dictionary
   ```python
   value = params['parameter_name']
   ```

3. **Set outputs**: Use `targets` list (must match output count and order)
   ```python
   # For outputs configured in order: output_table, output_file
   from gws_core import Table, File
   output_table = Table(result_df)
   output_file = File(file_path)
   targets = [output_table, output_file]
   ```

### Virtual Environment Agent
1. **Access input paths**: Use `source_paths` list
   ```python
   input_file = source_paths[0]  # First input
   ```

2. **Set output paths**: Assign list to `target_paths` with RELATIVE paths
   ```python
   # CORRECT - use relative paths
   target_paths = ['output1.csv', 'output2.png']

   # INCORRECT - do NOT use target_folders or absolute paths
   # target_paths = [os.path.join(target_folders[0], 'output.csv')]  # WRONG!
   ```

3. **Environment configuration** (ALWAYS generate alongside agent code):
   - **environment.yml** for Mamba/Conda environments (PREFERRED - use by default)
   - **Pipfile** for Pip environments (only if packages unavailable in conda/mamba)
   - For R agents: ALWAYS use Mamba with environment.yml

### Streamlit Agent
1. Use standard Streamlit syntax
2. Access inputs via agent context
3. Create interactive components (charts, filters, tables)
4. Output is automatically a Streamlit dashboard resource

## Parameter Types

When creating agent parameters through the Agent Dashboard:

- **String**: Text input (use for names, labels, file paths)
- **Number**: Numeric input (use for thresholds, counts, dimensions)
- **Boolean**: True/False checkbox
- **Code**: Multi-line code editor (use for code snippets, complex config)
- **JSON**: Structured data input

Access in code:
```python
param_value = params['Parameter Display Name']
```

## Common Patterns

### Pattern 1: Table Transformation
```python
# Basic Python Agent
# Configure in Agent Dashboard:
# - 1 input: Table
# - 1 output: Table
# - 1 parameter: "operation" (String)

from gws_core import Table

# Get input from sources list
input_table = sources[0]
df = input_table.get_data()

# Transform based on parameter
operation = params['operation']
if operation == 'transpose':
    result = df.T
elif operation == 'normalize':
    result = (df - df.mean()) / df.std()
else:
    result = df

# Create output
output_table = Table(result)
targets = [output_table]
```

### Pattern 2: File Processing with Virtual Environment
```python
# Virtual Environment Agent
# Input: File (JSON)
# Output: File (CSV)
# Parameter: encoding (String, default='utf-8')

import json
import pandas as pd

# Get inputs
input_file = source_paths[0]
encoding = params['encoding']

# Process
with open(input_file, 'r', encoding=encoding) as f:
    data = json.load(f)

df = pd.DataFrame(data)

# Save output with RELATIVE path
output_file = 'output.csv'
df.to_csv(output_file, index=False)

# Set target_paths (use RELATIVE paths)
target_paths = [output_file]
```

**environment.yml** (generate alongside):
```yaml
name: json_to_csv_agent
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.11
  - pandas>=2.0.0
```

### Pattern 3: Multiple Inputs and Outputs
```python
# Basic Python Agent
# Configure in Agent Dashboard:
# - 2 inputs: Table, Table
# - 2 outputs: Table, Table

from gws_core import Table
import pandas as pd

# Get inputs from sources list
table1 = sources[0]
table2 = sources[1]
df1 = table1.get_data()
df2 = table2.get_data()

# Merge tables
merged_df = pd.merge(df1, df2, on='id')

# Calculate statistics
stats_df = merged_df.describe()

# Create outputs as list (order matches output configuration)
merged_table = Table(merged_df)
stats_table = Table(stats_df)
targets = [merged_table, stats_table]
```


## Best Practices

### Agent Code
1. **Don't validate input** before processing, this is handled by the platform
2. **Handle errors gracefully** with try-except blocks
3. **Log meaningful messages** using print() (visible in execution logs)
4. **Close resources** (files, plots, connections) after use
5. **Use descriptive variable names** for clarity
6. **Comment complex logic** for maintainability

### Parameter Configuration
1. **Provide default values** for optional parameters
2. **Use descriptive names** that appear in the UI
3. **Document parameters** with clear descriptions
4. **Choose appropriate types** (String, Number, Boolean, etc.)

### Input/Output Management
1. **Match output count** to targets array length exactly
2. **Validate input types** before processing
3. **Create outputs in correct format** for downstream tasks
4. **Name outputs clearly** for workflow understanding

### Virtual Environment Agents
1. **ALWAYS generate environment.yml** (Mamba preferred) or Pipfile alongside agent code
2. **Use RELATIVE paths** for target_paths (e.g., 'output.csv', not '/path/to/output.csv')
3. **Prefer Mamba over Pip** - use environment.yml unless packages unavailable in conda/mamba
4. **For R code**: ALWAYS use Mamba R Agent with environment.yml
5. **Specify exact versions** in dependency files when needed
6. **Remember line number offset** when debugging (+ 2 + param count)

### Resource Cleanup
1. **Close matplotlib figures** with `plt.close()` after saving
2. **Close file handles** explicitly
3. **Delete temporary files** if not needed
4. **Use context managers** (`with` statements) when possible

## Migration from Task to Agent

When to use an Agent instead of a Task:

| Use Agent When | Use Task When |
|---------------|--------------|
| One-off analysis or transformation | Reusable process across multiple scenarios |
| Rapid prototyping | Production workflow component |
| Custom dependencies per scenario | Standard dependencies available |
| Exploratory data analysis | Well-defined inputs/outputs/configs |
| Quick visualization | Formal testing required |

To migrate a Task to an Agent:
1. Copy the `run()` method logic
2. Replace `inputs['name']` with `sources[i]` (Basic) or `source_paths[i]` (Virtual)
3. Replace `params.get_value('name')` with `params['name']`
4. Replace `return {'output': resource}` with `targets = [resource]` (Basic) or `target_paths = ['relative/path']` (Virtual)
5. Remove class structure, decorators, and specs


## Reference

### Core Documentation
- **Agent Getting Started**: https://constellab.community/bricks/gws_core/latest/doc/developer-guide/agent/getting-started/69820653-52e0-41ba-a5f3-4d9d54561779
- **Virtual Environment Agents**: https://constellab.community/bricks/gws_core/latest/doc/developer-guide/agent/virtual-env-agent/c6acb3c3-2a7c-44cd-8fb2-ea1beccdbdcc

### Related Resources
- **Task Documentation**: https://constellab.community/bricks/gws_core/latest/doc/developer-guide/task/task/6eb34e1c-6ae2-41bc-ae22-dc5cf962ee23
- **Virtual Environments in Tasks**: https://constellab.community/bricks/gws_core/latest/doc/developer-guide/task/virtual-environment-and-command-line/527bc4c0-094d-47f0-8e4a-5578d004cf8f

### Example Code
- Task examples: [${GWS_CORE_SRC}/impl](${GWS_CORE_SRC}/impl)
- Table tasks: [${GWS_CORE_SRC}/impl/table/tasks](${GWS_CORE_SRC}/impl/table/tasks)

## Task

$ARGUMENTS
