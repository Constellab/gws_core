import json
import os
import shutil
import time
from typing import Any

from gws_core.brick.brick_service import BrickService
from gws_core.community.community_service import CommunityService
from gws_core.config.config_params import ConfigParams
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_set import ParamSet
from gws_core.config.param.param_spec import BoolParam, IntParam, StrParam
from gws_core.core.utils.settings import Settings
from gws_core.core.utils.string_helper import StringHelper
from gws_core.docker.docker_dto import (
    DockerContainerStatus,
    RegisterComposeOptionsRequestDTO,
)
from gws_core.docker.docker_service import DockerService
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.file.folder import Folder
from gws_core.impl.json.json_dict import JSONDict
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs
from gws_core.test.junit_xml_reader import JUnitXmlReportSet


@task_decorator(
    unique_name="BrickTestRunner",
    human_name="Brick test runner",
    short_description="Run pytest suites of bricks inside a fresh glab container and collect JUnit results.",
)
class BrickTestRunner(Task):
    """Run brick test suites inside a fresh `glab` test container.

    This task installs a configurable set of bricks inside a sub-compose,
    runs `gws server test-all` for the bricks marked "Run tests", and reports
    the JUnit XML output. The task always finishes in **success** so the
    structured summary is available downstream — inspect `summary.is_success`
    to learn whether the underlying tests actually passed.

    ## Inputs / Outputs
    - **results** (Folder): folder containing the per-brick `*.xml` JUnit reports.
    - **summary** (JSONDict): aggregated counts (totals + per-brick breakdown)
      and the list of test failures.

    ## Parameters
    - **bricks** (ParamSet): one row per brick to install. Each row carries
      `name`, `version` and a `run_tests` toggle. `gws_core` must be present.
    - **parallel**: pass `--parallel` to `gws server test-all`.
    - **compose_timeout_seconds**: cap how long the test container can run.
    """

    # Brick that owns the sub-compose registration and the extension dir.
    _BRICK_NAME = "gws_core"
    # Name of the test container in docker/docker-compose.yaml — used to poll
    # for completion via DockerService.get_sub_compose_service_status.
    _SERVICE_NAME = "glab-test"

    input_specs: InputSpecs = InputSpecs({})
    output_specs: OutputSpecs = OutputSpecs(
        {
            "results": OutputSpec(
                Folder,
                human_name="JUnit XML folder",
                short_description="Raw per-brick JUnit XML files.",
            ),
            "summary": OutputSpec(
                JSONDict,
                human_name="Test summary",
                short_description="Aggregated counts and failures.",
            ),
        }
    )

    config_specs: ConfigSpecs = ConfigSpecs(
        {
            "bricks": ParamSet(
                ConfigSpecs(
                    {
                        "name": StrParam(
                            human_name="Brick name",
                            short_description="Brick to install (e.g. gws_core).",
                        ),
                        "version": StrParam(
                            human_name="Brick version",
                            short_description="Version tag, e.g. 0.22.0-beta.5.",
                        ),
                        "run_tests": BoolParam(
                            human_name="Run tests",
                            default_value=True,
                            short_description="Run this brick's pytest suite.",
                        ),
                    }
                ),
                max_number_of_occurrences=-1,
                human_name="Bricks to install",
                short_description="gws_core is mandatory.",
            ),
            "parallel": BoolParam(
                human_name="Parallel suites",
                default_value=False,
                short_description="Pass --parallel to gws server test-all.",
            ),
            "compose_timeout_seconds": IntParam(
                human_name="Compose timeout (s)",
                default_value=3600,
                min_value=60,
                short_description="Maximum wait for the test container to finish.",
            ),
        }
    )

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        bricks = self._validate_bricks(params.get_value("bricks"))
        parallel = params.get_value("parallel")
        timeout = params.get_value("compose_timeout_seconds")

        # --- Working directory ----------------------------------------------
        # The extension dir is mirrored on the docker host under LAB_VOLUME_HOST,
        # so the compose can mount /conf/config.json and /output from there.
        run_id = StringHelper.generate_uuid()
        ext_root = BrickService.get_brick_extension_dir(self._BRICK_NAME, run_id)
        output_dir = os.path.join(ext_root, "output")
        os.makedirs(output_dir, exist_ok=True)

        self._write_config_json(ext_root, bricks)

        bricks_to_test = ",".join(b["name"] for b in bricks if b["run_tests"])
        docker_folder = os.path.join(os.path.dirname(__file__), "docker")

        # --- Match the glab image to the requested gws_core version ---------
        # The community service exposes the GLAB_VERSION pinned for each
        # gws_core release; using it keeps test runs reproducible.
        gws_core_version = next(b["version"] for b in bricks if b["name"].lower() == "gws_core")
        glab_version = self._resolve_glab_version(gws_core_version)

        self.log_info_message(
            f"Starting BrickTestRunner run {run_id} for bricks: {bricks_to_test} "
            f"(glab:{glab_version})"
        )

        docker = DockerService()
        started = False
        warnings: list[str] = []

        # The whole compose lifecycle is wrapped in a try/except: any failure
        # is recorded as a warning and surfaced via the summary, but the task
        # itself still completes successfully so downstream tasks get the
        # results resource.
        try:
            # --- Register & start the sub-compose ---------------------------
            # Variables interpolated by the lab manager into the shipped YAML.
            docker.register_sub_compose_from_folder(
                brick_name=self._BRICK_NAME,
                unique_name=run_id,
                folder_path=docker_folder,
                options=RegisterComposeOptionsRequestDTO(
                    description=f"BrickTestRunner {run_id}",
                    auto_start=True,
                    environment_variables={
                        "RUN_ID": run_id,
                        "GLAB_VERSION": glab_version,
                        "TEST_BRICK_NAME": bricks_to_test,
                        "TEST_PARALLEL": "true" if parallel else "false",
                    },
                ),
            )
            started = True

            # --- Wait for the container to be up ----------------------------
            # First barrier: the lab manager's "register" job finishes once
            # the compose has started — it does NOT wait for the service to
            # exit, hence the second loop below.
            docker.wait_for_compose_status(
                brick_name=self._BRICK_NAME,
                unique_name=run_id,
                interval_seconds=5.0,
                max_attempts=max(int(timeout / 5), 1),
                message_dispatcher=self.message_dispatcher,
            )

            # --- Wait for the test run to finish ----------------------------
            # glab-test is a one-shot container: it runs `gws server test-all`
            # and exits. Poll its status until STOPPED/ERROR (or timeout).
            deadline = time.time() + timeout
            finished = False
            while time.time() < deadline:
                inspect = docker.get_sub_compose_service_status(
                    self._BRICK_NAME, run_id, self._SERVICE_NAME
                )
                if inspect.status in (DockerContainerStatus.STOPPED, DockerContainerStatus.ERROR):
                    self.log_info_message(
                        f"Test container exited with status {inspect.status.value} "
                        f"(exit code {inspect.exitCode})."
                    )
                    finished = True
                    break
                time.sleep(5)
            if not finished:
                warnings.append("Test container did not finish before timeout.")
                self.log_warning_message(warnings[-1])

        except Exception as exc:
            warnings.append(f"Compose start failed: {exc}")
            self.log_error_message(str(exc))

        # --- Collect results ------------------------------------------------
        # JUnitXmlReportSet is tolerant to a missing/empty folder, so this is
        # safe even when the compose never produced any XML.
        report_set = JUnitXmlReportSet(output_dir)
        summary = self._build_summary(bricks, report_set, run_id, warnings)

        # Copy the XMLs out of the extension dir (which we are about to delete)
        # so the Folder resource keeps pointing at a valid path.
        results_dir = self._copy_to_temp(output_dir)
        out_folder = Folder(results_dir)
        summary_dict = JSONDict(summary)

        # --- Cleanup --------------------------------------------------------
        if started:
            try:
                docker.unregister_compose(self._BRICK_NAME, run_id)
            except Exception as cleanup_exc:
                self.log_warning_message(f"Cleanup failed: {cleanup_exc}")

        FileHelper.delete_dir(ext_root)

        return {"results": out_folder, "summary": summary_dict}

    def _validate_bricks(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalize the ParamSet rows and enforce the gws_core / run_tests rules.

        Returns a fresh list with stripped name/version and a coerced
        run_tests bool. Raises on duplicate names (case-insensitive),
        missing fields, missing gws_core, or no test target.
        """
        if not rows:
            raise Exception("At least one brick must be configured.")

        seen: set[str] = set()
        normalized: list[dict[str, Any]] = []
        for row in rows:
            name = (row.get("name") or "").strip()
            version = (row.get("version") or "").strip()
            run_tests = bool(row.get("run_tests"))
            if not name:
                raise Exception("Every brick row must have a name.")
            if not version:
                raise Exception(f"Brick '{name}' is missing a version.")
            key = name.lower()
            if key in seen:
                raise Exception(f"Brick '{name}' is listed twice.")
            seen.add(key)
            normalized.append({"name": name, "version": version, "run_tests": run_tests})

        if not any(b["name"].lower() == "gws_core" for b in normalized):
            raise Exception(
                "gws_core must be present in the brick list (it is required to run the tests)."
            )

        if not any(b["run_tests"] for b in normalized):
            raise Exception("At least one brick must have 'Run tests' enabled.")

        return normalized

    def _resolve_glab_version(self, gws_core_version: str) -> str:
        info = CommunityService.get_brick_version_info("gws_core", gws_core_version)
        glab_version = (info.technicalInfo or {}).get("GLAB_VERSION")
        if not glab_version:
            raise Exception(
                f"Community returned no GLAB_VERSION for gws_core@{gws_core_version}."
            )
        return glab_version

    def _copy_to_temp(self, source_dir: str) -> str:
        results_dir = Settings.make_temp_dir()
        if not os.path.isdir(source_dir):
            return results_dir
        for entry in os.listdir(source_dir):
            src = os.path.join(source_dir, entry)
            dst = os.path.join(results_dir, entry)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        return results_dir

    def _write_config_json(self, ext_root: str, bricks: list[dict[str, Any]]) -> None:
        """Write the GPM brick-list config.json the glab container reads from /conf."""
        config = {
            "environment": {
                "bricks": [{"name": b["name"], "version": b["version"]} for b in bricks],
            }
        }
        with open(os.path.join(ext_root, "config.json"), "w", encoding="utf-8") as fh:
            json.dump(config, fh, indent=2)

    def _build_summary(
        self,
        bricks: list[dict[str, Any]],
        report_set: JUnitXmlReportSet,
        run_id: str,
        warnings: list[str],
    ) -> dict[str, Any]:
        """Aggregate the JUnit results into the JSONDict output payload.

        Shape: { run_id, is_success, tests_run, totals, bricks[], failures[],
        warnings[] }. is_success requires both a passing report set AND no
        warnings (so a timeout or compose start failure is reflected).
        """
        per_brick: list[dict[str, Any]] = []
        for b in bricks:
            report = report_set.report(b["name"])
            if report is None:
                per_brick.append(
                    {
                        "name": b["name"],
                        "version": b["version"],
                        "run_tests": b["run_tests"],
                        "report_found": False,
                        "tests_total": 0,
                        "tests_passed": 0,
                        "tests_failed": 0,
                        "tests_errors": 0,
                        "tests_skipped": 0,
                        "is_success": False,
                    }
                )
                continue
            per_brick.append(
                {
                    "name": b["name"],
                    "version": b["version"],
                    "run_tests": b["run_tests"],
                    "report_found": True,
                    "tests_total": report.tests_total,
                    "tests_passed": report.tests_passed,
                    "tests_failed": report.tests_failed,
                    "tests_errors": report.tests_errors,
                    "tests_skipped": report.tests_skipped,
                    "is_success": report.is_success,
                }
            )

        return {
            "run_id": run_id,
            "is_success": report_set.is_success and not warnings,
            "tests_run": report_set.reports_total > 0,
            "totals": {
                "tests_total": report_set.tests_total,
                "tests_passed": report_set.tests_passed,
                "tests_failed": report_set.tests_failed,
                "tests_errors": report_set.tests_errors,
                "tests_skipped": report_set.tests_skipped,
                "reports_total": report_set.reports_total,
                "reports_passed": report_set.reports_passed,
                "reports_failed": report_set.reports_failed,
            },
            "bricks": per_brick,
            "failures": [f.to_dict() for f in report_set.failures],
            "warnings": warnings,
        }
