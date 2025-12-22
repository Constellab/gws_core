# Nextflow to Task Converter

This command specializes in converting Nextflow pipeline processes into Constellab Tasks following best practices.

## What is Nextflow?

Nextflow is a workflow management system that enables scalable and reproducible scientific workflows using software containers. It uses a domain-specific language (DSL) to define computational pipelines composed of processes that are connected via channels.

### Key Nextflow Concepts:
- **Process**: An independent computational step that takes inputs, executes a script, and produces outputs
- **Channel**: Data streams that connect processes together
- **Workflow**: Orchestrates the execution flow by connecting processes via channels
- **Parameters**: Configuration values (e.g., `params.input_file`, `params.repeat_times`)

## Conversion Strategy

When converting a Nextflow pipeline to Constellab Tasks:

1. **One Process = One Task**: Each Nextflow `process` block becomes a separate Constellab Task
2. **Channels = Task Inputs/Outputs**: Data flowing through channels becomes task input_specs and output_specs
3. **Parameters = Config Specs**: Nextflow `params` become task config_specs
4. **Script = Run Method**: The process `script:` block logic is implemented in the task's `run()` method

## Conversion Workflow

### Step 0: Initial Analysis and User Validation (MANDATORY)

**IMPORTANT**: Before implementing any tasks, you MUST follow this validation workflow:

1. **Read the Nextflow Pipeline File**: Locate and read the entire Nextflow pipeline file (typically `main.nf` or `*.nf`)

2. **Extract and Analyze All Processes**: Identify all `process` blocks and extract:
   - Process name
   - Input parameters (with types)
   - Output files/values
   - Brief description of what the process does (based on the script logic)
   - Pipeline parameters used (`params.*`)

3. **Present Summary to User**: Display a clear summary including:
   - **Pipeline Parameters**: List all `params.*` with their default values
   - **Processes to Convert**: For each process, show:
     - Process name
     - Inputs and outputs
     - Brief description of functionality
   - **Workflow Structure**: Show how processes are connected

4. **Ask for User Validation**: Before proceeding, ask the user:
   - **Should all processes be created?** Confirm which processes to create
   - **Convert bash to Python?** Ask if bash/shell scripts should be converted to Python code or kept as shell commands using `ShellProxy`
   - **Task naming**: Confirm the proposed task names (PascalCase conversion from snake_case)
   - **Brick location**: Ask where to create the tasks (which brick, or create a new one)

5. **Wait for User Confirmation**: Do NOT proceed with implementation until the user confirms all details

**Example Validation Output**:
```
## Nextflow Pipeline Analysis

### Pipeline Parameters
- `input_file`: Input text file (default: "input.txt")
- `repeat_times`: Number of times to repeat text (default: 3)

### Processes to Convert

#### 1. convert_to_upper
- **Input**: Text file (`input_file`)
- **Output**: `uppercase.txt`
- **Description**: Converts all lowercase letters to uppercase

#### 2. multiply_text
- **Input**: Text file (`uppercase_file`), Integer (`repeat_times`)
- **Output**: `output.txt`
- **Description**: Repeats text content multiple times with blank lines

### Workflow
convert_to_upper → multiply_text

---

**Questions for Validation:**
1. Should I create both processes? (Yes/No or specify which ones)
2. Should I convert bash scripts to Python code? (Recommended: Yes for better maintainability)
3. Confirm task names: `ConvertToUpper` and `MultiplyText`? (or provide custom names)
4. Where should I create these tasks? (brick name or create new brick)

Please confirm before I proceed with implementation.
```

### Step 1: Analyze the Nextflow Pipeline

After user validation, read and understand the pipeline structure in detail:
- Identify all `process` blocks to convert
- Map input/output channels between processes
- List all `params` used across processes
- Understand the workflow execution order
- Analyze script blocks for implementation details

### Step 2: Map Each Process to a Task

For each Nextflow process, create a corresponding Constellab Task:

#### Nextflow Process Structure:
```groovy
process process_name {
    publishDir "results"

    input:
    path input_file
    val some_param

    output:
    path 'output_file.txt'

    script:
    """
    # Shell commands here
    command --input ${input_file} --param ${some_param} > output_file.txt
    """
}
```

#### Corresponding Constellab Task:
```python
from gws_core import Task, task_decorator, ConfigParams, TaskInputs, TaskOutputs, InputSpec, OutputSpec, InputSpecs, OutputSpecs, ConfigSpecs, StrParam, IntParam, File
import os
@task_decorator(
    unique_name="ProcessName",
    human_name="Process Name",
    short_description="Description of what this process does"
)
class ProcessName(Task):
    """
    [Generated by Nextflow to Task Converter]

    Converted from Nextflow process: process_name

    ## Original Nextflow Process
    This task replicates the functionality of the `process_name` process from the Nextflow pipeline.

    ## Process Description
    [Describe what the process does]
    """

    input_specs = InputSpecs({
        'input_file': InputSpec(
            File,
            human_name="Input file",
            short_description="Input file for processing"
        )
    })

    output_specs = OutputSpecs({
        'output_file': OutputSpec(
            File,
            human_name="Output file",
            short_description="Processed output file"
        )
    })

    config_specs = ConfigSpecs({
        'some_param': StrParam(
            human_name="Some parameter",
            short_description="Parameter used in processing",
            default_value="default"
        )
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        # Get inputs
        input_file = inputs['input_file']
        input_path = input_file.path

        # Get parameters
        some_param = params.get_value('some_param')

        # Create output file path
        tmp_dir = self.create_tmp_dir()
        output_path = os.path.join(tmp_dir, "output_file.txt")

        # Execute the process logic (from Nextflow script block)
        # Option 1: Use ShellProxy for complex shell commands
        from gws_core import ShellProxy
        shell = ShellProxy()
        shell.run(f"command --input {input_path} --param {some_param} > {output_path}")

        # Option 2: Use Python libraries for data processing
        # [Implement the logic in Python if possible]

        # Return output
        output_file = File(output_path)
        return {'output_file': output_file}
```

### Step 3: Map Nextflow Types to Constellab Resources

| Nextflow Input/Output | Constellab Resource | Notes |
|----------------------|---------------------|-------|
| `path file` | `File` | Single file |
| `path '*.txt'` (glob) | `Folder` | Multiple files in a folder |
| `val variable` | Config param | Scalar values become config parameters |
| `tuple` | Multiple inputs/outputs | Map to multiple input_specs/output_specs |
| `env` | Config param | Environment variables become config parameters |

### Step 4: Convert Nextflow Parameters

Map `params.*` declarations to config_specs:

| Nextflow Parameter | Constellab Config Param |
|-------------------|-------------------------|
| `params.input_file = "file.txt"` | `StrParam(default_value="file.txt")` |
| `params.repeat_times = 3` | `IntParam(default_value=3)` |
| `params.threshold = 0.05` | `FloatParam(default_value=0.05)` |
| `params.enable_feature = true` | `BoolParam(default_value=True)` |
| `params.allowed_values = ['a', 'b']` | `StrParam(allowed_values=['a', 'b'])` |

### Step 5: Convert Script Logic

Convert the Nextflow `script:` block to Python in the `run()` method.

**IMPORTANT**: During Step 0, you should have asked the user whether to convert bash scripts to Python. Follow their preference:
- If user chose **Python conversion**: Use Strategy B (Python Libraries)
- If user chose **Keep bash**: Use Strategy A (ShellProxy)
- If user didn't specify: Recommend Python for simple scripts, ShellProxy for complex/specialized tools

#### Strategy A: Use ShellProxy (Preserve Original Commands)

**When to use**:
- User explicitly requested to keep bash commands
- Complex bash scripts that are difficult to translate
- Scripts that rely on specialized command-line tools not available in Python
- Scripts where preserving exact bash behavior is critical

```python
from gws_core import ShellProxy

def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
    input_file = inputs['input_file']
    # Create output file path
    tmp_dir = self.create_tmp_dir()
    output_path = os.path.join(tmp_dir, "output_file.txt")

    shell = ShellProxy()

    # Execute shell commands from Nextflow script block
    shell.run(f"cat {input_file.path} | tr '[a-z]' '[A-Z]' > {output_path}")

    self.log_success_message("Command completed successfully")

    return {'output': File(output_path)}
```

#### Strategy B: Use Python Libraries (Recommended)

**When to use**:
- User requested Python conversion
- Simple file operations (read, write, transform)
- Better maintainability and debugging needed
- Cross-platform compatibility important
- When Python libraries can replicate the functionality
```python
def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
    # Read input
    input_file = inputs['input_file']
    with open(input_file.path, 'r') as f:
        content = f.read()

    # Process (equivalent to Nextflow script)
    result = content.upper()

    # Write output
    # Create output file path
    tmp_dir = self.create_tmp_dir()
    output_path = os.path.join(tmp_dir, "output_file.txt")
    with open(output_path, 'w') as f:
        f.write(result)

    return {'output': File(output_path)}
```

### Step 6: Handle Dependencies

If the Nextflow process uses specific tools or dependencies, you can use virtual environments to manage them. Use **MambaShellProxy** (recommended for faster installation) or alternatively **CondaShellProxy** or **PipShellProxy** depending on your package requirements.

#### IMPORTANT: Python File Naming Convention

**CRITICAL**: When creating Python scripts that should NOT be automatically loaded/executed during lab startup, you MUST follow this naming convention:

- **Python files must start with an underscore (`_`)**: e.g., `_my_script.py`, `_helper.py`
- **OR** Python files must be placed in a folder that starts with an underscore: e.g., `_scripts/helper.py`, `_utils/processor.py`


#### Example: Nextflow Process with Dependencies

```groovy
process quality_control {
    conda 'bioconda::fastqc=0.11.9'

    input:
    path fastq_file

    output:
    path 'qc_results/*'

    script:
    """
    fastqc ${fastq_file} -o qc_results
    """
}
```

#### Convert to Constellab Task with Virtual Environment:

First, create an `quality_control_env.yml` file in the same directory as your task file:

**quality_control_env.yml**:
```yaml
name: fastqc_env
channels:
  - bioconda
  - conda-forge
dependencies:
  - fastqc=0.11.9
```

Then, create the task that references this environment file:

```python
import os
from gws_core import Task, task_decorator, ConfigParams, TaskInputs, TaskOutputs, InputSpec, OutputSpec, InputSpecs, OutputSpecs, ConfigSpecs, File, Folder, MambaShellProxy

@task_decorator(
    unique_name="QualityControl",
    human_name="Quality Control",
    short_description="Run FastQC quality control on sequencing data"
)
class QualityControl(Task):
    """
    [Generated by Nextflow to Task Converter]

    Converted from Nextflow process: quality_control

    ## Description
    Runs FastQC to assess the quality of high-throughput sequencing data.
    """

    input_specs = InputSpecs({
        'fastq_file': InputSpec(
            File,
            human_name="FASTQ file",
            short_description="Input sequencing file"
        )
    })

    output_specs = OutputSpecs({
        'qc_results': OutputSpec(
            Folder,
            human_name="QC results",
            short_description="Quality control analysis results"
        )
    })

    config_specs = ConfigSpecs({})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        fastq_file = inputs['fastq_file']

        # Get the path to the quality_control_env.yml file (in the same directory as this task file)
        env_file_path = os.path.join(os.path.dirname(__file__), "quality_control_env.yml")

        # Create virtual environment from YAML file (using MambaShellProxy - recommended)
        mamba = MambaShellProxy(
            env_file_path=env_file_path,
            env_name="fastqc_env",
            message_dispatcher=self.message_dispatcher
        )

        # Prepare output directory
        tmp_dir = self.create_tmp_dir()
        output_dir = os.path.join(tmp_dir, "qc_results")

        # Run FastQC command
        self.log_info_message("Running FastQC quality control...")
        mamba.run(f"fastqc {fastq_file.path} -o {output_dir}")

        self.log_success_message("Quality control analysis completed")

        return {'qc_results': Folder(output_dir)}
```

#### Alternative: Using Docker Containers

For processes that require Docker containers (e.g., complex bioinformatics tools), you can use the `DockerService` to run temporary containers. See the [Docker Service documentation](${GWS_CORE_SRC}/docker/doc_docker_service.md) section **"Temporary Docker Container for Process Execution"** for detailed guidance.

**Example: Nextflow Process with Container**

```groovy
process alignment {
    container 'biocontainers/bwa:0.7.17'

    input:
    path reads
    path reference

    output:
    path 'aligned.bam'

    script:
    """
    bwa mem ${reference} ${reads} | samtools view -bS - > aligned.bam
    """
}
```

**Convert to Constellab Task with Docker Container:**

First, create a `docker-compose.yml` next to your task file:

**_docker/docker-compose.yml**:
```yaml
services:
  bwa_aligner:
    image: biocontainers/bwa:0.7.17
    container_name: ${CONTAINER_PREFIX}-aligner
    volumes:
      - ${LAB_VOLUME_HOST}/input:/data/input
      - ${LAB_VOLUME_HOST}/output:/data/output
    command: >
      bash -c "bwa mem /data/input/reference.fa /data/input/reads.fq |
               samtools view -bS - > /data/output/aligned.bam"
    networks:
      - ${CONTAINER_PREFIX}

networks:
  ${CONTAINER_PREFIX}:
    driver: bridge
```

**Task implementation:**

```python
import os
from gws_core import Task, task_decorator, ConfigParams, TaskInputs, TaskOutputs, InputSpec, OutputSpec, InputSpecs, OutputSpecs, ConfigSpecs, File, DockerService, DockerComposeStatus

@task_decorator(
    unique_name="BwaAlignment",
    human_name="BWA Alignment",
    short_description="Align reads using BWA in a Docker container"
)
class BwaAlignment(Task):
    """
    [Generated by Nextflow to Task Converter]

    Converted from Nextflow process: alignment

    ## Description
    Aligns sequencing reads to a reference genome using BWA (Burrows-Wheeler Aligner).
    Runs in a temporary Docker container.
    """

    input_specs = InputSpecs({
        'reads': InputSpec(
            File,
            human_name="Reads file",
            short_description="FASTQ file containing sequencing reads"
        ),
        'reference': InputSpec(
            File,
            human_name="Reference genome",
            short_description="Reference genome FASTA file"
        )
    })

    output_specs = OutputSpecs({
        'aligned_bam': OutputSpec(
            File,
            human_name="Aligned BAM",
            short_description="Alignment results in BAM format"
        )
    })

    config_specs = ConfigSpecs({})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        reads_file = inputs['reads']
        reference_file = inputs['reference']

        # Prepare input/output directories
        tmp_dir = self.create_tmp_dir()
        input_dir = os.path.join(tmp_dir, "input")
        output_dir = os.path.join(tmp_dir, "output")

        # Copy input files to the shared directory
        self.copy_file(reads_file.path, os.path.join(input_dir, "reads.fq"))
        self.copy_file(reference_file.path, os.path.join(input_dir, "reference.fa"))

        # Get path to docker-compose.yml 
        docker_folder_path = os.path.join(os.path.dirname(__file__))

        docker_service = DockerService()

        # Register and start the temporary container
        self.log_info_message("Starting BWA alignment container...")
        docker_service.register_sub_compose_from_folder(
            brick_name="my_brick",
            unique_name="bwa_aligner",
            folder_path=docker_folder_path,
            description="Temporary BWA alignment container",
            auto_start=False
        )

        # Wait for container to complete processing
        self.log_info_message("Waiting for alignment to complete...")
        status = docker_service.wait_for_compose_status(
            brick_name="my_brick",
            unique_name="bwa_aligner",
            interval_seconds=2.0,
            max_attempts=30,
            message_dispatcher=self.message_dispatcher
        )

        if status.composeStatus.status != DockerComposeStatus.UP:
            raise Exception(f"Container failed to start: {status.composeStatus.info}")

        # Wait for processing to complete (implement your own completion check)
        # For example, monitor output file creation or container exit status

        # Stop and clean up the container
        self.log_info_message("Alignment complete, stopping container...")
        docker_service.stop_compose(
            brick_name="my_brick",
            unique_name="bwa_aligner"
        )

        # Get the output file
        output_bam_path = os.path.join(output_dir, "aligned.bam")

        self.log_success_message("BWA alignment completed successfully!")

        return {'aligned_bam': File(output_bam_path)}
```

**Key points for container-based tasks:**
- Use `${LAB_VOLUME_HOST}` for shared volumes between the container and the task
- Set `auto_start=False` for temporary containers
- Always stop the container after processing using `stop_compose()`
- For complete cleanup, you can use `unregister_compose()` instead
- Reference the [Docker Service documentation](${GWS_CORE_SRC}/docker/doc_docker_service.md) for template variables (`${CONTAINER_PREFIX}`, `${LAB_NETWORK}`, etc.)


## Complete Conversion Example

### Original Nextflow Pipeline:
```groovy
params.input_file = "input.txt"
params.repeat_times = 3

process convert_to_upper {
    input:
    path input_file

    output:
    path 'uppercase.txt'

    script:
    """
    cat ${input_file} | tr '[a-z]' '[A-Z]' > uppercase.txt
    """
}

process multiply_text {
    input:
    path uppercase_file
    val repeat_times

    output:
    path 'output.txt'

    script:
    """
    > output.txt
    for i in \$(seq 1 ${repeat_times}); do
        cat ${uppercase_file} >> output.txt
        echo "" >> output.txt
    done
    """
}

workflow {
    ch_input = channel.fromPath(params.input_file)
    ch_upper = convert_to_upper(ch_input)
    multiply_text(ch_upper, params.repeat_times)
}
```

### Converted to Constellab Tasks:

#### Task 1: ConvertToUpper
```python
import os
from gws_core import Task, task_decorator, ConfigParams, TaskInputs, TaskOutputs, InputSpec, OutputSpec, InputSpecs, OutputSpecs, ConfigSpecs, File

@task_decorator(
    unique_name="ConvertToUpper",
    human_name="Convert to Upper",
    short_description="Convert text file content to uppercase"
)
class ConvertToUpper(Task):
    """
    [Generated by Nextflow to Task Converter]

    Converted from Nextflow process: convert_to_upper

    ## Description
    Reads a text file and converts all lowercase letters to uppercase.
    """

    input_specs = InputSpecs({
        'input_file': InputSpec(
            File,
            human_name="Input file",
            short_description="Text file to convert"
        )
    })

    output_specs = OutputSpecs({
        'uppercase': OutputSpec(
            File,
            human_name="Uppercase file",
            short_description="Text file with uppercase content"
        )
    })

    config_specs = ConfigSpecs({})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        input_file = inputs['input_file']

        # Read input
        with open(input_file.path, 'r') as f:
            content = f.read()

        # Convert to uppercase
        uppercase_content = content.upper()

        # Write output
        tmp_dir = self.create_tmp_dir()
        output_path = os.path.join(tmp_dir, "uppercase.txt")
        with open(output_path, 'w') as f:
            f.write(uppercase_content)

        self.log_success_message(f"Converted {len(content)} characters to uppercase")

        return {'uppercase': File(output_path)}
```

#### Task 2: MultiplyText
```python
import os
from gws_core import Task, task_decorator, ConfigParams, TaskInputs, TaskOutputs, InputSpec, OutputSpec, InputSpecs, OutputSpecs, ConfigSpecs, File, IntParam

@task_decorator(
    unique_name="MultiplyText",
    human_name="Multiply Text",
    short_description="Repeat text file content multiple times"
)
class MultiplyText(Task):
    """
    [Generated by Nextflow to Task Converter]

    Converted from Nextflow process: multiply_text

    ## Description
    Repeats the content of a text file a specified number of times, with blank lines between repetitions.
    """

    input_specs = InputSpecs({
        'text_file': InputSpec(
            File,
            human_name="Text file",
            short_description="File to repeat"
        )
    })

    output_specs = OutputSpecs({
        'output': OutputSpec(
            File,
            human_name="Output file",
            short_description="File with repeated content"
        )
    })

    config_specs = ConfigSpecs({
        'repeat_times': IntParam(
            human_name="Repeat times",
            short_description="Number of times to repeat the text",
            default_value=3,
            min_value=1
        )
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        text_file = inputs['text_file']
        repeat_times = params.get_value('repeat_times')

        # Read input
        with open(text_file.path, 'r') as f:
            content = f.read()

        # Multiply content
        repeated_content = []
        for i in range(repeat_times):
            repeated_content.append(content)

        result = '\n'.join(repeated_content)

        # Write output
        tmp_dir = self.create_tmp_dir()
        output_path = os.path.join(tmp_dir, "output.txt")
        with open(output_path, 'w') as f:
            f.write(result)

        self.log_success_message(f"Repeated text {repeat_times} times")

        return {'output': File(output_path)}
```

## Task Generation

After analyzing the Nextflow pipeline, use the standard task generation command for each process:

```bash
gws task generate ConvertToUpper --human-name "Convert to Upper" --short-description "Convert text to uppercase"
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
   - Which processes to convert
   - Whether to use Python or ShellProxy for script conversion
   - Task naming conventions
   - Target brick location
4. **Respect User Choices**: Follow the user's preferences for implementation strategy

### Conversion Guidelines
1. **Preserve Process Logic**: Keep the original processing logic intact
2. **One Process = One Task**: Don't combine multiple processes into a single task
3. **Use Meaningful Names**: Convert snake_case process names to PascalCase task class names
4. **Document Origin**: Always mention the source Nextflow process in docstrings
5. **Start Docstring Correctly**: Begin class docstring with `[Generated by Nextflow to Task Converter]`

### Implementation Guidelines
1. **Follow User's Script Conversion Choice**:
   - If user chose Python: Convert bash to Python using native libraries
   - If user chose ShellProxy: Preserve original bash commands
   - Default recommendation: Python for simple scripts, ShellProxy for complex tools
2. **Use Virtual Environments**: For bioinformatics tools, use MambaShellProxy (recommended), CondaShellProxy, or PipShellProxy
3. **CRITICAL - File Naming Convention**:
   - ALL python scripts MUST start with underscore (`_`) or be in a folder starting with underscore (this prevents files from being scanned/executed during lab startup) 
4. **Handle Errors**: Add proper error handling and logging
5. **Test Thoroughly**: Create unit tests for each converted task
6. **Validate Resources**: Ensure file formats match expected inputs/outputs

### Parameter Mapping
1. **Make Parameters Optional**: Use default values from Nextflow params
2. **Add Validation**: Use min_value, max_value, allowed_values for config params
3. **Document Defaults**: Mention original Nextflow default values in descriptions

## Common Patterns

### Pattern 1: Simple File Transformation
```groovy
// Nextflow
process transform {
    input: path infile
    output: path 'outfile.txt'
    script: "command ${infile} > outfile.txt"
}
```
→ Create a Task with File input/output, implement logic in run()

### Pattern 2: Process with Parameters
```groovy
// Nextflow
process filter {
    input:
        path data
        val threshold
    output: path 'filtered.txt'
    script: "filter.py ${data} --threshold ${threshold}"
}
```
→ Create a Task with File input, IntParam/FloatParam config, File output

### Pattern 3: Multiple Inputs
```groovy
// Nextflow
process merge {
    input:
        path file1
        path file2
    output: path 'merged.txt'
    script: "cat ${file1} ${file2} > merged.txt"
}
```
→ Create a Task with multiple input_specs (file1, file2)

### Pattern 4: Container-based Process
```groovy
// Nextflow
process blast {
    container 'biocontainers/blast:2.12.0'
    input: path query
    output: path 'results.txt'
    script: "blastn -query ${query} -out results.txt"
}
```
→ Create a Task using CondaShellProxy or MambaShellProxy with the appropriate package

## Reference

### Nextflow Documentation
- **Nextflow Processes**: https://www.nextflow.io/docs/latest/process.html
- **Nextflow Channels**: https://www.nextflow.io/docs/latest/channel.html
- **Nextflow Workflows**: https://www.nextflow.io/docs/latest/workflow.html

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

1. **Read the Nextflow pipeline file first** (typically `main.nf` or `*.nf`)
2. **Extract all processes and parameters** from the pipeline
3. **Present a complete analysis** to the user showing:
   - All pipeline parameters with defaults
   - All processes with inputs, outputs, and descriptions
   - The workflow structure (how processes connect)
4. **Ask these validation questions**:
   - Should all processes be converted? (or specify which ones)
   - Convert bash scripts to Python, or keep as ShellProxy? (recommend Python for simple scripts)
   - Confirm proposed task names (PascalCase from snake_case)
   - Where to create the tasks? (brick name)
5. **WAIT for user confirmation** before implementing anything
6. **Follow user's preferences** for implementation (Python vs ShellProxy)

Do NOT start implementing tasks without completing this validation workflow!

---

$ARGUMENTS
