# Snakemake to Task Converter

This command specializes in converting Snakemake workflow rules into Constellab Tasks following best practices.

## What is Snakemake?

Snakemake is a workflow management system that enables reproducible and scalable data analyses. It uses a Python-based language to define computational pipelines composed of rules that are connected via input/output file dependencies.

### Key Snakemake Concepts:
- **Rule**: An independent computational step that takes inputs, executes commands, and produces outputs
- **Input/Output**: File dependencies that determine execution order
- **Wildcards**: Pattern matching variables for processing multiple samples
- **Config**: Configuration parameters and settings
- **Directives**: Additional rule properties (threads, resources, conda, etc.)

## Conversion Strategy

When converting a Snakemake workflow to Constellab Tasks:

1. **One Rule = One Task**: Each Snakemake `rule` becomes a separate Constellab Task
2. **Input/Output Files = Task Inputs/Outputs**: Files in `input:` and `output:` become task input_specs and output_specs
3. **Params = Config Specs**: Snakemake `params:` become task config_specs
4. **Script/Shell/Run = Run Method**: The rule execution logic is implemented in the task's `run()` method
5. **Wildcards = Config Parameters**: Wildcards become config parameters or are handled via multiple task instances

## Conversion Workflow

### Step 0: Initial Analysis and User Validation (MANDATORY)

**IMPORTANT**: Before implementing any tasks, you MUST follow this validation workflow:

1. **Read the Snakemake Workflow File**: Locate and read the entire Snakefile (typically `Snakefile` or `*.smk`)

2. **Extract and Analyze All Rules**: Identify all `rule` blocks and extract:
   - Rule name
   - Input files/parameters (with types)
   - Output files
   - Brief description of what the rule does (based on the script/shell logic)
   - Configuration parameters used (config, params, wildcards)
   - Execution directive used (shell, script, run, notebook, wrapper, cwl)
   - Virtual environment requirements (conda, container)

3. **Present Summary to User**: Display a clear summary including:
   - **Configuration Parameters**: List all config values and wildcards
   - **Rules to Convert**: For each rule, show:
     - Rule name
     - Inputs and outputs
     - Execution directive type (shell, script, run, etc.)
     - Brief description of functionality
     - Virtual environment requirements (if any)
   - **Workflow Structure**: Show how rules are connected via file dependencies

4. **Ask for User Validation**: Before proceeding, ask the user:
   - **Should all rules be created?** Confirm which rules to convert
   - **Handle execution directives**: For each rule, confirm conversion strategy:
     - `shell:` - Convert to Python or keep as ShellProxy?
     - `script:` - Keep external script or inline in run()?
     - `run:` - Inline Python code (straightforward conversion)
     - `notebook:` - How to handle (convert to script or keep notebook)?
     - `wrapper:` - Custom implementation needed
     - `cwl:` - Custom implementation needed
   - **Wildcard handling**: How to handle wildcards (config params vs. multiple tasks)?
   - **Task naming**: Confirm the proposed task names (PascalCase conversion from snake_case)
   - **Brick location**: Ask where to create the tasks (which brick, or create a new one)

5. **Wait for User Confirmation**: Do NOT proceed with implementation until the user confirms all details

**Example Validation Output**:
```
## Snakemake Workflow Analysis

### Configuration
- Wildcards: {sample} - values: ["sample1", "sample2", "sample3"]
- Config: min_length = 10, quality_threshold = 20

### Rules to Convert

#### 1. quality_control
- **Input**: FASTQ file (`data/raw/{sample}.fastq`)
- **Output**: QC file (`results/qc/{sample}_qc.txt`), Stats file (`results/qc/{sample}_stats.txt`)
- **Execution**: `shell:` directive with quality control commands
- **Environment**: conda environment (`envs/qc.yaml`)
- **Description**: Performs quality control on raw sequencing data

#### 2. trim_reads
- **Input**: FASTQ file, QC file
- **Output**: Trimmed FASTQ (`data/trimmed/{sample}_trimmed.fastq`)
- **Params**: min_length = 10
- **Execution**: `shell:` directive with trimming commands
- **Description**: Trims low-quality reads based on minimum length

#### 3. analyze
- **Input**: Trimmed FASTQ file
- **Output**: Analysis results (`results/analysis/{sample}_analysis.txt`)
- **Threads**: 2
- **Execution**: `script:` directive → `scripts/analyze.py`
- **Environment**: conda environment (`envs/analysis.yaml`)
- **Description**: Analyzes trimmed data using external Python script

#### 4. generate_report
- **Input**: QC stats, Analysis results
- **Output**: Report (`results/reports/{sample}_report.txt`)
- **Execution**: `shell:` directive with report generation
- **Description**: Generates individual sample reports

### Workflow Structure
quality_control → trim_reads → analyze → generate_report

### Wildcards
- {sample}: Processes multiple samples (sample1, sample2, sample3)
  - **Conversion Strategy**: Create config parameter for sample name, or process multiple samples in a single task

---

**Questions for Validation:**
1. Should I create all 4 rules as tasks? (Yes/No or specify which ones)
2. For `shell:` directives, should I convert bash scripts to Python code? (Recommended: Yes for better maintainability)
3. For `script:` directives, should I inline the Python script or keep it external? (Recommended: Inline for single-file tasks)
4. How should I handle wildcards?
   - Option A: Config parameter (user specifies sample name)
   - Option B: Process multiple samples in one task (batch processing)
5. Confirm task names: `QualityControl`, `TrimReads`, `Analyze`, `GenerateReport`?
6. Where should I create these tasks? (brick name or create new brick)

Please confirm before I proceed with implementation.
```

### Step 1: Analyze the Snakemake Workflow

After user validation, read and understand the workflow structure in detail:
- Identify all `rule` blocks to convert
- Map input/output file dependencies between rules
- List all config values, params, and wildcards used
- Understand the workflow execution order
- Analyze execution blocks (shell, script, run, etc.) for implementation details
- Identify virtual environment requirements (conda, container)

### Step 2: Map Each Rule to a Task

For each Snakemake rule, create a corresponding Constellab Task based on its execution directive.

#### Snakemake Rule Structure (Shell Directive):
```python
rule quality_control:
    input:
        "data/raw/{sample}.fastq"
    output:
        qc="results/qc/{sample}_qc.txt",
        stats="results/qc/{sample}_stats.txt"
    params:
        quality_threshold=20
    threads: 2
    conda: "envs/qc.yaml"
    shell:
        """
        # Shell commands here
        fastqc {input} -o results/qc
        echo "Quality: {params.quality_threshold}" > {output.stats}
        """
```

#### Corresponding Constellab Task:
```python
from gws_core import Task, task_decorator, ConfigParams, TaskInputs, TaskOutputs, InputSpec, OutputSpec, InputSpecs, OutputSpecs, ConfigSpecs, File, StrParam, IntParam, MambaShellProxy
import os

@task_decorator(
    unique_name="QualityControl",
    human_name="Quality Control",
    short_description="Perform quality control on sequencing data"
)
class QualityControl(Task):
    """
    [Generated by Snakemake to Task Converter]

    Converted from Snakemake rule: quality_control

    ## Original Snakemake Rule
    This task replicates the functionality of the `quality_control` rule from the Snakemake workflow.

    ## Rule Description
    Performs quality control analysis on raw FASTQ files using FastQC.
    """

    input_specs = InputSpecs({
        'fastq_file': InputSpec(
            File,
            human_name="FASTQ file",
            short_description="Raw sequencing data file"
        )
    })

    output_specs = OutputSpecs({
        'qc_file': OutputSpec(
            File,
            human_name="QC file",
            short_description="Quality control results"
        ),
        'stats_file': OutputSpec(
            File,
            human_name="Stats file",
            short_description="Quality statistics"
        )
    })

    config_specs = ConfigSpecs({
        'sample_name': StrParam(
            human_name="Sample name",
            short_description="Name of the sample (from wildcard {sample})",
            default_value="sample1"
        ),
        'quality_threshold': IntParam(
            human_name="Quality threshold",
            short_description="Minimum quality score threshold",
            default_value=20
        )
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        # Get inputs
        fastq_file = inputs['fastq_file']
        input_path = fastq_file.path

        # Get parameters
        sample_name = params.get_value('sample_name')
        quality_threshold = params.get_value('quality_threshold')

        # Create output paths
        tmp_dir = self.create_tmp_dir()
        qc_path = os.path.join(tmp_dir, f"{sample_name}_qc.txt")
        stats_path = os.path.join(tmp_dir, f"{sample_name}_stats.txt")

        # Get conda environment file path
        env_file_path = os.path.join(os.path.dirname(__file__), "qc_env.yaml")

        # Execute with conda environment (if specified in original rule)
        mamba = MambaShellProxy(
            env_file_path=env_file_path,
            env_name="qc_env",
            message_dispatcher=self.message_dispatcher
        )

        self.log_info_message(f"Running quality control for {sample_name}...")

        # Option 1: Use ShellProxy for complex shell commands
        mamba.run(f"fastqc {input_path} -o {tmp_dir}")
        with open(stats_path, 'w') as f:
            f.write(f"Quality: {quality_threshold}\n")

        # Option 2: Use Python libraries for data processing (if user requested conversion)
        # [Implement the logic in Python if possible]

        self.log_success_message("Quality control completed successfully")

        # Return outputs
        return {
            'qc_file': File(qc_path),
            'stats_file': File(stats_path)
        }
```

### Step 3: Handle Different Execution Directives

Snakemake supports multiple execution directives. Each requires a different conversion strategy:

#### 1. `shell:` Directive
**Original Snakemake:**
```python
rule trim_reads:
    input: "data/{sample}.fastq"
    output: "trimmed/{sample}.fastq"
    params: min_length=10
    shell:
        "cutadapt -m {params.min_length} -o {output} {input}"
```

**Conversion Strategy:**
- Ask user: Convert to Python or keep as ShellProxy?
- **Option A (ShellProxy)**: Keep shell commands, use ShellProxy or MambaShellProxy
- **Option B (Python)**: Convert to Python using libraries (e.g., BioPython)

**Converted Task (ShellProxy approach):**
```python
def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
    input_file = inputs['fastq_file']
    min_length = params.get_value('min_length')

    tmp_dir = self.create_tmp_dir()
    output_path = os.path.join(tmp_dir, "trimmed.fastq")

    # Use MambaShellProxy if conda env is specified
    shell = MambaShellProxy(
        env_file_path=os.path.join(os.path.dirname(__file__), "trim_env.yaml"),
        env_name="trim_env",
        message_dispatcher=self.message_dispatcher
    )
    shell.run(f"cutadapt -m {min_length} -o {output_path} {input_file.path}")

    return {'trimmed_file': File(output_path)}
```

#### 2. `script:` Directive
**Original Snakemake:**
```python
rule analyze:
    input: "data/{sample}.txt"
    output: "results/{sample}_analysis.txt"
    params: threshold=0.05
    threads: 2
    script: "scripts/analyze.py"
```

**Conversion Strategy:**
- Ask user: Inline the script or keep it external?
- **Option A (Inline)**: Copy script logic into `run()` method (recommended for simple scripts)
- **Option B (External)**: Keep script external, call it via subprocess or import

**Converted Task (Inline approach):**
```python
def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
    input_file = inputs['input_file']
    threshold = params.get_value('threshold')

    # Copy logic from scripts/analyze.py
    with open(input_file.path, 'r') as f:
        data = f.read()

    # Perform analysis (from original script)
    result = analyze_data(data, threshold)

    tmp_dir = self.create_tmp_dir()
    output_path = os.path.join(tmp_dir, "analysis.txt")
    with open(output_path, 'w') as f:
        f.write(result)

    return {'analysis_file': File(output_path)}
```

#### 3. `run:` Directive
**Original Snakemake:**
```python
rule process_data:
    input: "data/{sample}.txt"
    output: "processed/{sample}.txt"
    run:
        with open(input[0], 'r') as f_in, open(output[0], 'w') as f_out:
            data = f_in.read().upper()
            f_out.write(data)
```

**Conversion Strategy:**
- Straightforward: Copy Python code directly into `run()` method
- Replace `input[0]` with `inputs['input_name'].path`
- Replace `output[0]` with output file path in tmp_dir
- Replace `wildcards.sample` with config parameter

**Converted Task:**
```python
def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
    input_file = inputs['input_file']
    sample_name = params.get_value('sample_name')

    tmp_dir = self.create_tmp_dir()
    output_path = os.path.join(tmp_dir, f"{sample_name}.txt")

    # Copy logic from run: block
    with open(input_file.path, 'r') as f_in, open(output_path, 'w') as f_out:
        data = f_in.read().upper()
        f_out.write(data)

    return {'output_file': File(output_path)}
```

#### 4. `notebook:` Directive
**Original Snakemake:**
```python
rule create_plots:
    input: "data/{sample}.csv"
    output: "plots/{sample}_plots.html"
    notebook: "notebooks/plotting.ipynb"
```

**Conversion Strategy:**
- Ask user: Convert notebook to script or keep as notebook?
- **Option A**: Convert notebook cells to Python code in `run()` method
- **Option B**: Execute notebook using nbconvert or papermill

**Converted Task (Execute notebook approach):**
```python
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
    input_file = inputs['input_file']

    # Load and execute notebook
    notebook_path = os.path.join(os.path.dirname(__file__), "plotting.ipynb")
    with open(notebook_path) as f:
        nb = nbformat.read(f, as_version=4)

    # Set notebook parameters
    nb.metadata['papermill'] = {
        'parameters': {
            'input_path': input_file.path,
            'sample_name': params.get_value('sample_name')
        }
    }

    # Execute notebook
    ep = ExecutePreprocessor(timeout=600)
    ep.preprocess(nb, {'metadata': {'path': os.path.dirname(notebook_path)}})

    # Save output
    tmp_dir = self.create_tmp_dir()
    output_path = os.path.join(tmp_dir, "plots.html")
    # Extract output from notebook or save executed notebook

    return {'plots': File(output_path)}
```

#### 5. `wrapper:` Directive
**Original Snakemake:**
```python
rule bwa_mem:
    input:
        reads=["reads/{sample}_1.fastq", "reads/{sample}_2.fastq"],
        idx="genome.fa"
    output: "mapped/{sample}.bam"
    wrapper: "v1.21.2/bio/bwa/mem"
```

**Conversion Strategy:**
- Wrapper-specific: Need to implement the wrapper's functionality
- Look up wrapper source code to understand what it does
- Implement equivalent logic in the task

**Converted Task:**
```python
def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
    reads_1 = inputs['reads_1']
    reads_2 = inputs['reads_2']
    reference = inputs['reference']

    tmp_dir = self.create_tmp_dir()
    output_path = os.path.join(tmp_dir, "aligned.bam")

    # Implement wrapper functionality
    # For bwa mem wrapper, this would be:
    mamba = MambaShellProxy(
        env_file_path=os.path.join(os.path.dirname(__file__), "bwa_env.yaml"),
        env_name="bwa_env",
        message_dispatcher=self.message_dispatcher
    )

    cmd = f"bwa mem {reference.path} {reads_1.path} {reads_2.path} | samtools view -Sb - > {output_path}"
    mamba.run(cmd)

    return {'aligned_bam': File(output_path)}
```

#### 6. `cwl:` Directive
**Original Snakemake:**
```python
rule run_tool:
    input: "data/{sample}.txt"
    output: "results/{sample}.out"
    cwl: "tools/custom_tool.cwl"
```

**Conversion Strategy:**
- Parse CWL file to understand tool inputs/outputs
- Implement tool execution in Constellab
- May require custom implementation based on CWL tool specification

### Step 4: Map Snakemake Types to Constellab Resources

| Snakemake Input/Output | Constellab Resource | Notes |
|------------------------|---------------------|-------|
| Single file path | `File` | Single file |
| Multiple file paths (list) | Multiple `File` inputs | Each file as separate input_spec |
| Directory | `Folder` | Folder resource |
| `params:` values | Config params | Use appropriate Param type |
| `wildcards.*` | Config params | Convert to `StrParam` or handle as batch processing |
| `threads` | Config param | `IntParam` for thread count |
| `resources.mem_mb` | Config param | `IntParam` for memory |
| Named outputs (`out=...`) | Named output_specs | Map to output_specs keys |

### Step 5: Convert Snakemake Parameters

Map Snakemake configuration to config_specs:

| Snakemake Parameter | Constellab Config Param |
|---------------------|-------------------------|
| `params.value = "text"` | `StrParam(default_value="text")` |
| `params.count = 5` | `IntParam(default_value=5)` |
| `params.threshold = 0.05` | `FloatParam(default_value=0.05)` |
| `params.enabled = True` | `BoolParam(default_value=True)` |
| `wildcards.sample` | `StrParam()` for sample name |
| `threads: 4` | `IntParam(default_value=4)` for thread count |
| `resources.mem_mb: 8000` | `IntParam(default_value=8000)` for memory |

### Step 6: Handle Wildcards

Wildcards in Snakemake represent pattern matching for processing multiple items. Convert them based on user preference:

**Strategy A: Config Parameter (Single Sample)**
```python
config_specs = ConfigSpecs({
    'sample_name': StrParam(
        human_name="Sample name",
        short_description="Name of the sample to process",
        default_value="sample1"
    )
})
```

**Strategy B: Batch Processing (Multiple Samples)**
```python
from gws_core import ListParam

config_specs = ConfigSpecs({
    'sample_names': ListParam(
        human_name="Sample names",
        short_description="List of sample names to process",
        default_value=["sample1", "sample2", "sample3"]
    )
})

def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
    sample_names = params.get_value('sample_names')

    # Process each sample
    for sample in sample_names:
        self.log_info_message(f"Processing {sample}...")
        # Process logic here
```

### Step 7: Handle Virtual Environments

Snakemake supports `conda:` and `container:` directives for environment management.

#### Conda Environment
**Original Snakemake:**
```python
rule analyze:
    input: "data.txt"
    output: "results.txt"
    conda: "envs/analysis.yaml"
    shell: "analyze.py {input} {output}"
```

**Conversion:**
1. Copy the conda environment YAML file to your task directory
2. Use `MambaShellProxy` (recommended) or `CondaShellProxy`

**Converted Task:**
```python
def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
    input_file = inputs['input_file']

    tmp_dir = self.create_tmp_dir()
    output_path = os.path.join(tmp_dir, "results.txt")

    # Get environment file path
    env_file_path = os.path.join(os.path.dirname(__file__), "analysis_env.yaml")

    # Create virtual environment
    mamba = MambaShellProxy(
        env_file_path=env_file_path,
        env_name="analysis_env",
        message_dispatcher=self.message_dispatcher
    )

    # Run command in environment
    mamba.run(f"analyze.py {input_file.path} {output_path}")

    return {'results': File(output_path)}
```

#### Container Support
**Original Snakemake:**
```python
rule align:
    input: "reads.fq"
    output: "aligned.bam"
    container: "docker://biocontainers/bwa:0.7.17"
    shell: "bwa mem ref.fa {input} > {output}"
```

**Conversion:**
Use `DockerService` for container-based execution. See the Nextflow to Task converter documentation (Step 6) for detailed Docker container implementation.

### Step 8: Handle Additional Directives

Map other Snakemake directives to Constellab equivalents:

| Snakemake Directive | Constellab Equivalent |
|---------------------|----------------------|
| `threads: 4` | `IntParam` config parameter |
| `resources: mem_mb=8000` | `IntParam` config parameter |
| `log: "logs/{sample}.log"` | Use `self.log_*_message()` methods |
| `benchmark: "bench.txt"` | Use `self.update_progress_*()` for timing |
| `message: "Processing..."` | Use `self.log_info_message("Processing...")` |
| `priority: 10` | Not directly applicable (handled by Constellab scheduler) |
| `shadow: "full"` | Use `self.create_tmp_dir()` for isolated execution |

## Complete Conversion Example

### Original Snakemake Workflow:
```python
# Snakefile
SAMPLES = ["sample1", "sample2", "sample3"]

rule all:
    input:
        expand("results/{sample}_report.txt", sample=SAMPLES)

rule quality_control:
    input:
        "data/raw/{sample}.fastq"
    output:
        qc="results/qc/{sample}_qc.txt",
        stats="results/qc/{sample}_stats.txt"
    params:
        quality_threshold=20
    threads: 2
    conda: "envs/qc.yaml"
    shell:
        """
        fastqc {input} -o results/qc
        echo "Quality: {params.quality_threshold}" > {output.stats}
        """

rule trim_reads:
    input:
        fastq="data/raw/{sample}.fastq",
        qc="results/qc/{sample}_qc.txt"
    output:
        "data/trimmed/{sample}_trimmed.fastq"
    params:
        min_length=10
    shell:
        """
        cutadapt -m {params.min_length} -o {output} {input.fastq}
        """

rule analyze:
    input:
        "data/trimmed/{sample}_trimmed.fastq"
    output:
        "results/analysis/{sample}_analysis.txt"
    params:
        threshold=0.05
    threads: 2
    conda: "envs/analysis.yaml"
    script:
        "scripts/analyze.py"

rule generate_report:
    input:
        qc="results/qc/{sample}_stats.txt",
        analysis="results/analysis/{sample}_analysis.txt"
    output:
        "results/{sample}_report.txt"
    run:
        with open(output[0], 'w') as f_out:
            f_out.write(f"Report for {wildcards.sample}\n")
            f_out.write("=" * 40 + "\n\n")

            with open(input.qc, 'r') as f:
                f_out.write("QC Statistics:\n")
                f_out.write(f.read() + "\n\n")

            with open(input.analysis, 'r') as f:
                f_out.write("Analysis Results:\n")
                f_out.write(f.read())
```

### Converted to Constellab Tasks:

#### Task 1: QualityControl
```python
import os
from gws_core import Task, task_decorator, ConfigParams, TaskInputs, TaskOutputs, InputSpec, OutputSpec, InputSpecs, OutputSpecs, ConfigSpecs, File, StrParam, IntParam, MambaShellProxy

@task_decorator(
    unique_name="QualityControl",
    human_name="Quality Control",
    short_description="Perform quality control on sequencing data"
)
class QualityControl(Task):
    """
    [Generated by Snakemake to Task Converter]

    Converted from Snakemake rule: quality_control

    ## Description
    Performs quality control analysis on raw FASTQ files using FastQC.
    """

    input_specs = InputSpecs({
        'fastq_file': InputSpec(
            File,
            human_name="FASTQ file",
            short_description="Raw sequencing data file"
        )
    })

    output_specs = OutputSpecs({
        'qc_file': OutputSpec(
            File,
            human_name="QC file",
            short_description="Quality control results"
        ),
        'stats_file': OutputSpec(
            File,
            human_name="Stats file",
            short_description="Quality statistics"
        )
    })

    config_specs = ConfigSpecs({
        'sample_name': StrParam(
            human_name="Sample name",
            short_description="Name of the sample (from wildcard {sample})",
            default_value="sample1"
        ),
        'quality_threshold': IntParam(
            human_name="Quality threshold",
            short_description="Minimum quality score threshold",
            default_value=20
        ),
        'threads': IntParam(
            human_name="Threads",
            short_description="Number of CPU threads to use",
            default_value=2,
            min_value=1
        )
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        fastq_file = inputs['fastq_file']
        sample_name = params.get_value('sample_name')
        quality_threshold = params.get_value('quality_threshold')
        threads = params.get_value('threads')

        tmp_dir = self.create_tmp_dir()
        qc_path = os.path.join(tmp_dir, f"{sample_name}_qc.txt")
        stats_path = os.path.join(tmp_dir, f"{sample_name}_stats.txt")

        # Use conda environment
        env_file_path = os.path.join(os.path.dirname(__file__), "qc_env.yaml")
        mamba = MambaShellProxy(
            env_file_path=env_file_path,
            env_name="qc_env",
            message_dispatcher=self.message_dispatcher
        )

        self.log_info_message(f"Running quality control for {sample_name} with {threads} threads...")

        mamba.run(f"fastqc {fastq_file.path} -o {tmp_dir} -t {threads}")

        with open(stats_path, 'w') as f:
            f.write(f"Quality: {quality_threshold}\n")

        self.log_success_message("Quality control completed successfully")

        return {
            'qc_file': File(qc_path),
            'stats_file': File(stats_path)
        }
```

#### Task 2: TrimReads
```python
import os
from gws_core import Task, task_decorator, ConfigParams, TaskInputs, TaskOutputs, InputSpec, OutputSpec, InputSpecs, OutputSpecs, ConfigSpecs, File, StrParam, IntParam, ShellProxy

@task_decorator(
    unique_name="TrimReads",
    human_name="Trim Reads",
    short_description="Trim low-quality reads from FASTQ file"
)
class TrimReads(Task):
    """
    [Generated by Snakemake to Task Converter]

    Converted from Snakemake rule: trim_reads

    ## Description
    Trims low-quality reads based on minimum length threshold using cutadapt.
    """

    input_specs = InputSpecs({
        'fastq_file': InputSpec(
            File,
            human_name="FASTQ file",
            short_description="Raw sequencing data file"
        ),
        'qc_file': InputSpec(
            File,
            human_name="QC file",
            short_description="Quality control file (dependency)"
        )
    })

    output_specs = OutputSpecs({
        'trimmed_file': OutputSpec(
            File,
            human_name="Trimmed FASTQ",
            short_description="Trimmed sequencing data"
        )
    })

    config_specs = ConfigSpecs({
        'sample_name': StrParam(
            human_name="Sample name",
            short_description="Name of the sample",
            default_value="sample1"
        ),
        'min_length': IntParam(
            human_name="Minimum length",
            short_description="Minimum read length to keep",
            default_value=10,
            min_value=1
        )
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        fastq_file = inputs['fastq_file']
        sample_name = params.get_value('sample_name')
        min_length = params.get_value('min_length')

        tmp_dir = self.create_tmp_dir()
        output_path = os.path.join(tmp_dir, f"{sample_name}_trimmed.fastq")

        shell = ShellProxy()

        self.log_info_message(f"Trimming reads with minimum length {min_length}...")
        shell.run(f"cutadapt -m {min_length} -o {output_path} {fastq_file.path}")

        self.log_success_message("Read trimming completed")

        return {'trimmed_file': File(output_path)}
```

#### Task 3: Analyze
```python
import os
from gws_core import Task, task_decorator, ConfigParams, TaskInputs, TaskOutputs, InputSpec, OutputSpec, InputSpecs, OutputSpecs, ConfigSpecs, File, StrParam, FloatParam, IntParam, MambaShellProxy

@task_decorator(
    unique_name="Analyze",
    human_name="Analyze",
    short_description="Analyze trimmed sequencing data"
)
class Analyze(Task):
    """
    [Generated by Snakemake to Task Converter]

    Converted from Snakemake rule: analyze

    ## Description
    Analyzes trimmed sequencing data using custom analysis script.
    """

    input_specs = InputSpecs({
        'trimmed_file': InputSpec(
            File,
            human_name="Trimmed FASTQ",
            short_description="Trimmed sequencing data"
        )
    })

    output_specs = OutputSpecs({
        'analysis_file': OutputSpec(
            File,
            human_name="Analysis results",
            short_description="Analysis output file"
        )
    })

    config_specs = ConfigSpecs({
        'sample_name': StrParam(
            human_name="Sample name",
            short_description="Name of the sample",
            default_value="sample1"
        ),
        'threshold': FloatParam(
            human_name="Threshold",
            short_description="Analysis threshold value",
            default_value=0.05
        ),
        'threads': IntParam(
            human_name="Threads",
            short_description="Number of CPU threads",
            default_value=2,
            min_value=1
        )
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        trimmed_file = inputs['trimmed_file']
        sample_name = params.get_value('sample_name')
        threshold = params.get_value('threshold')
        threads = params.get_value('threads')

        tmp_dir = self.create_tmp_dir()
        output_path = os.path.join(tmp_dir, f"{sample_name}_analysis.txt")

        # Inline the script logic from scripts/analyze.py
        # (or use MambaShellProxy if keeping script external)

        with open(trimmed_file.path, 'r') as f:
            data = f.read()

        # Analysis logic here (from original script)
        self.log_info_message(f"Analyzing {sample_name} with threshold {threshold}...")

        result = f"Analysis Results for {sample_name}\n"
        result += f"{'=' * 40}\n"
        result += f"Threshold: {threshold}\n"
        result += f"Threads used: {threads}\n"
        result += f"\nInput data preview:\n{data[:200]}\n"

        with open(output_path, 'w') as f:
            f.write(result)

        self.log_success_message("Analysis completed")

        return {'analysis_file': File(output_path)}
```

#### Task 4: GenerateReport
```python
import os
from gws_core import Task, task_decorator, ConfigParams, TaskInputs, TaskOutputs, InputSpec, OutputSpec, InputSpecs, OutputSpecs, ConfigSpecs, File, StrParam

@task_decorator(
    unique_name="GenerateReport",
    human_name="Generate Report",
    short_description="Generate analysis report from QC and analysis results"
)
class GenerateReport(Task):
    """
    [Generated by Snakemake to Task Converter]

    Converted from Snakemake rule: generate_report

    ## Description
    Combines QC statistics and analysis results into a comprehensive report.
    """

    input_specs = InputSpecs({
        'qc_stats': InputSpec(
            File,
            human_name="QC statistics",
            short_description="Quality control statistics file"
        ),
        'analysis_results': InputSpec(
            File,
            human_name="Analysis results",
            short_description="Analysis output file"
        )
    })

    output_specs = OutputSpecs({
        'report': OutputSpec(
            File,
            human_name="Report",
            short_description="Combined analysis report"
        )
    })

    config_specs = ConfigSpecs({
        'sample_name': StrParam(
            human_name="Sample name",
            short_description="Name of the sample",
            default_value="sample1"
        )
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        qc_stats = inputs['qc_stats']
        analysis_results = inputs['analysis_results']
        sample_name = params.get_value('sample_name')

        tmp_dir = self.create_tmp_dir()
        output_path = os.path.join(tmp_dir, f"{sample_name}_report.txt")

        # Logic from run: block
        with open(output_path, 'w') as f_out:
            f_out.write(f"Report for {sample_name}\n")
            f_out.write("=" * 40 + "\n\n")

            with open(qc_stats.path, 'r') as f:
                f_out.write("QC Statistics:\n")
                f_out.write(f.read() + "\n\n")

            with open(analysis_results.path, 'r') as f:
                f_out.write("Analysis Results:\n")
                f_out.write(f.read())

        self.log_success_message(f"Report generated for {sample_name}")

        return {'report': File(output_path)}
```

## Task Generation

After analyzing the Snakemake workflow, use the standard task generation command for each rule:

```bash
gws task generate QualityControl --human-name "Quality Control" --short-description "Perform quality control on sequencing data"
```

Then modify the generated task file with the converted logic.

## Task Information Reference

**IMPORTANT**: For detailed information about Constellab Tasks, their structure, configuration, testing, and best practices, refer to the [task-expert.md](task-expert.md) documentation.

Key topics covered in task-expert.md:
- Task structure and requirements (decorators, specs, run method)
- Input/Output specifications
- Configuration parameters (all Param types)
- Task methods (logging, progress, lifecycle methods)
- Unit testing with TaskRunner
- Best practices and conventions
- Virtual environments and shell commands

## Best Practices

### Pre-Implementation Workflow (CRITICAL)
1. **ALWAYS Start with Step 0**: Never skip the validation workflow described in Step 0
2. **Present Analysis First**: Show the user a complete analysis before writing any code
3. **Ask for Confirmation**: Wait for explicit user approval on:
   - Which rules to convert
   - How to handle each execution directive (shell, script, run, etc.)
   - Whether to convert shell commands to Python or keep as ShellProxy
   - Wildcard handling strategy (config params vs batch processing)
   - Task naming conventions
   - Target brick location
4. **Respect User Choices**: Follow the user's preferences for implementation strategy

### Conversion Guidelines
1. **Preserve Rule Logic**: Keep the original processing logic intact
2. **One Rule = One Task**: Don't combine multiple rules into a single task
3. **Use Meaningful Names**: Convert snake_case rule names to PascalCase task class names
4. **Document Origin**: Always mention the source Snakemake rule in docstrings
5. **Start Docstring Correctly**: Begin class docstring with `[Generated by Snakemake to Task Converter]`
6. **Handle All Execution Directives**: Support shell, script, run, notebook, wrapper, and cwl

### Implementation Guidelines
1. **Follow User's Conversion Choice**:
   - If user chose Python: Convert shell commands to Python using native libraries
   - If user chose ShellProxy: Preserve original shell commands
   - Default recommendation: Python for simple scripts, ShellProxy for complex tools
2. **Use Virtual Environments**: For tools with dependencies, use MambaShellProxy (recommended), CondaShellProxy, or PipShellProxy
3. **Handle Wildcards Appropriately**: Ask user how to handle wildcards (config param or batch processing)
4. **Map Named Outputs**: Preserve named outputs from Snakemake rules
5. **Handle Errors**: Add proper error handling and logging
6. **Test Thoroughly**: Create unit tests for each converted task
7. **Validate Resources**: Ensure file formats match expected inputs/outputs

### Execution Directive Mapping
1. **shell**: Ask user preference (Python vs ShellProxy)
2. **script**: Ask user preference (inline vs external)
3. **run**: Direct Python code conversion
4. **notebook**: Ask user preference (convert to script vs execute notebook)
5. **wrapper**: Implement wrapper functionality (research wrapper source)
6. **cwl**: Parse CWL and implement tool execution

### Parameter Mapping
1. **Make Parameters Optional**: Use default values from Snakemake config
2. **Add Validation**: Use min_value, max_value, allowed_values for config params
3. **Document Defaults**: Mention original Snakemake default values in descriptions
4. **Convert Wildcards**: Map wildcards to config parameters or batch processing logic
5. **Handle Threads/Resources**: Convert to IntParam config parameters

## Common Patterns

### Pattern 1: Simple Shell Command
```python
# Snakemake
rule transform:
    input: "input.txt"
    output: "output.txt"
    shell: "transform {input} > {output}"
```
→ Create a Task with File input/output, use ShellProxy or convert to Python

### Pattern 2: Rule with Parameters
```python
# Snakemake
rule filter:
    input: "data.txt"
    output: "filtered.txt"
    params: threshold=0.05
    shell: "filter.py {input} --threshold {params.threshold} > {output}"
```
→ Create a Task with File input, FloatParam config, File output

### Pattern 3: Multiple Inputs/Outputs
```python
# Snakemake
rule merge:
    input:
        file1="data1.txt",
        file2="data2.txt"
    output:
        merged="merged.txt",
        stats="stats.txt"
    shell: "merge.py {input.file1} {input.file2} -o {output.merged} -s {output.stats}"
```
→ Create a Task with multiple input_specs and output_specs

### Pattern 4: Script Directive
```python
# Snakemake
rule analyze:
    input: "data.txt"
    output: "results.txt"
    params: threshold=0.05
    script: "scripts/analyze.py"
```
→ Create a Task and inline the script logic or call it externally

### Pattern 5: Conda Environment
```python
# Snakemake
rule qc:
    input: "reads.fastq"
    output: "qc_results.txt"
    conda: "envs/qc.yaml"
    shell: "fastqc {input} -o {output}"
```
→ Create a Task using MambaShellProxy with the conda environment file

### Pattern 6: Wildcard Processing
```python
# Snakemake
rule process:
    input: "data/{sample}.txt"
    output: "results/{sample}_processed.txt"
    shell: "process {input} > {output}"
```
→ Create a Task with StrParam for sample_name, or ListParam for batch processing

## Reference

### Snakemake Documentation
- **Snakemake Rules**: https://snakemake.readthedocs.io/en/stable/snakefiles/rules.html
- **Execution Directives**: https://snakemake.readthedocs.io/en/stable/snakefiles/rules.html#python
- **Conda Integration**: https://snakemake.readthedocs.io/en/stable/snakefiles/deployment.html

### Constellab Task Documentation
- **Task Documentation**: See [task-expert.md](task-expert.md) for complete task creation guide
- **Virtual Environments**: Reference task-expert.md section on ShellProxy classes
- **External Tools**: Reference task-expert.md section on advanced tasks

### Example Code
- Task examples: [${GWS_CORE_SRC}/impl](${GWS_CORE_SRC}/impl)
- File class: [${GWS_CORE_SRC}/impl/file/file.py](${GWS_CORE_SRC}/impl/file/file.py)
- Folder class: [${GWS_CORE_SRC}/impl/file/folder.py](${GWS_CORE_SRC}/impl/file/folder.py)

## Task

**CRITICAL REMINDER**: When executing this command, you MUST:

1. **Read the Snakemake workflow file first** (typically `Snakefile` or `*.smk`)
2. **Extract all rules, config, and wildcards** from the workflow
3. **Present a complete analysis** to the user showing:
   - All configuration parameters and wildcards
   - All rules with inputs, outputs, execution directives, and descriptions
   - Virtual environment requirements (conda, container)
   - The workflow structure (how rules connect via file dependencies)
4. **Ask these validation questions**:
   - Should all rules be converted? (or specify which ones)
   - For each execution directive, confirm conversion strategy:
     - `shell:` Convert to Python or keep as ShellProxy?
     - `script:` Inline or keep external?
     - `notebook:` Convert to script or execute notebook?
     - `wrapper:` Custom implementation strategy?
     - `cwl:` Custom implementation strategy?
   - How should wildcards be handled? (config param vs batch processing)
   - Confirm proposed task names (PascalCase from snake_case)
   - Where to create the tasks? (brick name)
5. **WAIT for user confirmation** before implementing anything
6. **Follow user's preferences** for implementation (Python vs ShellProxy, inline vs external, etc.)

Do NOT start implementing tasks without completing this validation workflow!

---

$ARGUMENTS
