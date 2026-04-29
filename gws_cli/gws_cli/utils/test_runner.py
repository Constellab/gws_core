"""Run brick test suites in subprocesses, leaving JUnit XML files behind.

Used by `gws server test-all`. Each brick runs in a fresh `gws server test`
subprocess that writes a JUnit XML to a folder. If no folder is provided, a
temp dir is created and removed at the end. Aggregating the XMLs into other
formats (JSON, HTML, etc.) is the caller's job — see
`gws_core.test.junit_xml_reader.JUnitXmlReportSet`.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from collections import deque
from dataclasses import dataclass

import typer

_OUTPUT_TAIL_LINES = 200


@dataclass
class BrickRunResult:
    name: str
    exit_code: int
    duration_seconds: float
    junit_xml_path: str

    @property
    def is_success(self) -> bool:
        return self.exit_code == 0


def _run_and_tee(cmd: list[str]) -> int:
    """Run cmd, stream stdout/stderr to console, return the exit code."""
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1
    )
    # Tail buffers used to keep the threads simple (and to drop stale output if
    # subprocess is chatty); we don't surface them right now.
    stdout_tail: deque[str] = deque(maxlen=_OUTPUT_TAIL_LINES)
    stderr_tail: deque[str] = deque(maxlen=_OUTPUT_TAIL_LINES)

    def _pump(stream, sink: deque[str], out) -> None:
        for line in iter(stream.readline, ""):
            out.write(line)
            out.flush()
            sink.append(line)
        stream.close()

    t_out = threading.Thread(target=_pump, args=(proc.stdout, stdout_tail, sys.stdout))
    t_err = threading.Thread(target=_pump, args=(proc.stderr, stderr_tail, sys.stderr))
    t_out.start()
    t_err.start()
    code = proc.wait()
    t_out.join()
    t_err.join()
    return code


def _print_summary(results: list[BrickRunResult]) -> None:
    typer.echo("\n=== test-all summary ===")
    for r in results:
        label = "PASS" if r.is_success else f"FAIL (exit {r.exit_code})"
        typer.echo(f"  {r.name}: {label}")


def _run_brick(
    brick_dir: str,
    log_level: str,
    parallel: bool,
    workers: str,
    durations: int,
    junit_path: str,
) -> BrickRunResult:
    name = os.path.basename(brick_dir)
    typer.echo(f"\n=== Running tests for brick '{name}' ===")

    cmd = ["gws", "--log-level", log_level, "server", "test", "all", "--brick-name", name]
    if durations > 0:
        cmd += ["--durations", str(durations)]
    if parallel:
        cmd += ["--parallel", "-n", workers]
    cmd += ["--junit-xml", junit_path]

    started = time.monotonic()
    code = _run_and_tee(cmd)
    return BrickRunResult(
        name=name,
        exit_code=code,
        duration_seconds=round(time.monotonic() - started, 2),
        junit_xml_path=junit_path,
    )


def run_test_all(
    brick_dirs: list[str],
    log_level: str,
    parallel: bool,
    workers: str,
    durations: int,
    junit_dir: str = "",
) -> list[BrickRunResult]:
    """Run tests for each brick sequentially. Each brick gets its own JUnit XML.

    If `junit_dir` is provided, XMLs are written there and kept after the run.
    Otherwise a temp dir is created and removed before returning.
    """
    keep_dir = bool(junit_dir)
    out_dir = junit_dir or tempfile.mkdtemp(prefix="gws-test-junit-")
    if keep_dir:
        os.makedirs(out_dir, exist_ok=True)

    results: list[BrickRunResult] = []
    try:
        for brick_dir in brick_dirs:
            junit_path = os.path.join(out_dir, f"{os.path.basename(brick_dir)}.xml")
            results.append(
                _run_brick(brick_dir, log_level, parallel, workers, durations, junit_path)
            )
    finally:
        if not keep_dir:
            shutil.rmtree(out_dir, ignore_errors=True)

    _print_summary(results)
    return results
