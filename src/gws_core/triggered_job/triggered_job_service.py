import traceback

from croniter import croniter

from gws_core.core.db.gws_core_db_manager import GwsCoreDbManager
from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.utils import Utils
from gws_core.model.typing import Typing

# Get all typings with cron job decorator
from gws_core.process.process_factory import ProcessFactory
from gws_core.protocol.protocol import Protocol
from gws_core.protocol.protocol_service import ProtocolService
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_enums import ScenarioCreationType
from gws_core.scenario.scenario_run_service import ScenarioRunService
from gws_core.scenario.scenario_service import ScenarioService
from gws_core.scenario_template.scenario_template import ScenarioTemplate
from gws_core.task.task import Task
from gws_core.triggered_job.triggered_job_dto import (
    ActivateTriggeredJobDTO,
    CreateTriggeredJobFromProcessDTO,
    CreateTriggeredJobFromTemplateDTO,
    TriggeredJobDTO,
    TriggeredJobRunDTO,
    UpdateTriggeredJobDTO,
)
from gws_core.triggered_job.triggered_job_model import TriggeredJobModel
from gws_core.triggered_job.triggered_job_run_model import TriggeredJobRunModel
from gws_core.triggered_job.triggered_job_types import (
    JobRunTrigger,
    TriggerType,
)
from gws_core.user.current_user_service import AuthenticateUser
from gws_core.user.user import User


class TriggeredJobService:
    """Service for managing triggered jobs"""

    @classmethod
    @GwsCoreDbManager.transaction()
    def create_from_process(cls, dto: CreateTriggeredJobFromProcessDTO) -> TriggeredJobModel:
        """
        Create a triggered job from a Task or Protocol typing name.
        """
        # Validate typing exists and is TASK or PROTOCOL
        typing = Typing.get_by_typing_name(dto.process_typing_name)
        if typing is None:
            raise BadRequestException(f"Typing '{dto.process_typing_name}' not found")

        if typing.object_type not in ("TASK", "PROTOCOL"):
            raise BadRequestException(
                f"Typing '{dto.process_typing_name}' is not a TASK or PROTOCOL"
            )

        # Validate cron expression
        cls._validate_cron_expression(dto.cron_expression)

        job = TriggeredJobModel(
            process_typing=typing,
            scenario_template=None,
            config_values=dto.config_values,
            trigger_type=TriggerType.CRON,
            cron_expression=dto.cron_expression,
            is_active=dto.is_active,
            name=dto.name,
            description=dto.description,
        )

        job.update_next_run()
        job.save()

        return job

    @classmethod
    @GwsCoreDbManager.transaction()
    def create_from_template(cls, dto: CreateTriggeredJobFromTemplateDTO) -> TriggeredJobModel:
        """
        Create a triggered job from a ScenarioTemplate.
        """
        # Validate template exists
        template = ScenarioTemplate.get_by_id(dto.scenario_template_id)
        if template is None:
            raise BadRequestException(f"ScenarioTemplate '{dto.scenario_template_id}' not found")

        # Validate cron expression
        cls._validate_cron_expression(dto.cron_expression)

        job = TriggeredJobModel(
            process_typing=None,
            scenario_template=template,
            config_values=dto.config_values,
            trigger_type=TriggerType.CRON,
            cron_expression=dto.cron_expression,
            is_active=dto.is_active,
            name=dto.name,
            description=dto.description,
        )

        job.update_next_run()
        job.save()

        return job

    # ========================== UPDATE ==========================

    @classmethod
    @GwsCoreDbManager.transaction()
    def update(cls, job_id: str, dto: UpdateTriggeredJobDTO) -> TriggeredJobModel:
        """Update a triggered job"""
        job = cls.get_by_id_and_check(job_id)

        if dto.name is not None:
            job.name = dto.name

        if dto.description is not None:
            job.description = dto.description

        if dto.cron_expression is not None:
            cls._validate_cron_expression(dto.cron_expression)
            job.cron_expression = dto.cron_expression
            job.update_next_run()

        if dto.config_values is not None:
            job.config_values = dto.config_values

        job.save()
        return job

    @classmethod
    @GwsCoreDbManager.transaction()
    def activate(cls, job_id: str, dto: ActivateTriggeredJobDTO | None = None) -> TriggeredJobModel:
        """Activate a triggered job"""
        job = cls.get_by_id_and_check(job_id)

        if dto and dto.cron_expression:
            cls._validate_cron_expression(dto.cron_expression)
            job.cron_expression = dto.cron_expression

        if not job.cron_expression:
            raise BadRequestException("Cannot activate job without a cron expression")

        job.is_active = True
        job.update_next_run()
        job.save()

        return job

    @classmethod
    @GwsCoreDbManager.transaction()
    def deactivate(cls, job_id: str) -> TriggeredJobModel:
        """Deactivate a triggered job"""
        job = cls.get_by_id_and_check(job_id)

        job.is_active = False
        job.next_run_at = None
        job.save()

        return job

    @classmethod
    def delete(cls, job_id: str) -> None:
        """Delete a triggered job"""
        TriggeredJobModel.delete_by_id(job_id)

    # ========================== EXECUTION ==========================

    @classmethod
    def run_manual(cls, job_id: str) -> TriggeredJobRunModel:
        """Manually trigger a job execution"""
        job = cls.get_by_id_and_check(job_id)
        return cls.execute_job(job, JobRunTrigger.MANUAL)

    @classmethod
    def execute_job(
        cls,
        job: TriggeredJobModel,
        trigger: JobRunTrigger,
    ) -> TriggeredJobRunModel:
        """
        Execute a triggered job.
        Creates a Scenario from the job's source and runs it.
        """
        # Check if job is already running
        if job.is_running():
            raise BadRequestException(
                f"Job '{job.name}' is already running. Wait for the current execution to complete."
            )

        # Create run record
        run = TriggeredJobRunModel.create_run(job, trigger)

        try:
            # Authenticate as sys user for execution
            with AuthenticateUser(User.get_and_check_sysuser()):
                # Create and run scenario
                scenario = cls._create_scenario_for_job(job)
                run.scenario = scenario
                run.save()

                # Run the scenario
                ScenarioRunService.run_scenario(scenario)

                # Check scenario status
                scenario = scenario.refresh()
                if scenario.is_success:
                    run.mark_as_success()
                else:
                    error_info = scenario.get_error_info()
                    run.mark_as_error(
                        message=error_info.detail if error_info else "Scenario failed",
                        stacktrace=None,
                    )

        except Exception as e:
            Logger.error(f"Error executing triggered job '{job.name}': {e}")
            Logger.log_exception_stack_trace(e)
            run.mark_as_error(
                message=str(e),
                stacktrace=traceback.format_exc(),
            )

        finally:
            # Update next run time for CRON jobs
            if job.is_active and job.is_cron_job():
                job.update_next_run()
                job.save()

        return run

    @classmethod
    def _create_scenario_for_job(cls, job: TriggeredJobModel) -> Scenario:
        """Create a Scenario from the job's source (Task, Protocol, or Template)"""

        if job.uses_process_typing():
            # Create from Task or Protocol typing
            process_class = job.process_typing.get_type()
            if process_class is None:
                raise BadRequestException(
                    f"Could not load class for typing '{job.process_typing.typing_name}'"
                )

            if Utils.issubclass(process_class, Protocol):
                # Create scenario from Protocol
                scenario = ScenarioService.create_scenario_from_protocol_type(
                    protocol_type=process_class,
                    title=f"[Job] {job.name}",
                    creation_type=ScenarioCreationType.TRIGGERED_JOB,
                )
            else:
                # Create scenario from Task (wrap in protocol)
                scenario = cls._create_scenario_from_task(
                    task_class=process_class,
                    title=f"[Job] {job.name}",
                    config_values=job.config_values,
                )

            return scenario

        elif job.uses_scenario_template():
            # Create from ScenarioTemplate
            scenario = ScenarioService.create_scenario(
                title=f"[Job] {job.name}",
                scenario_template=job.scenario_template,
                creation_type=ScenarioCreationType.TRIGGERED_JOB,
            )

            # TODO: Apply config_values overrides if provided

            return scenario

        else:
            raise BadRequestException(
                "Job has no valid source (process_typing or scenario_template)"
            )

    @classmethod
    def _create_scenario_from_task(
        cls,
        task_class: type[Task],
        title: str,
        config_values: dict | None,
    ) -> Scenario:
        """Create a scenario containing a single task"""

        # Create empty protocol
        protocol_model = ProcessFactory.create_protocol_empty()

        # Create scenario
        scenario = ScenarioService.create_scenario_from_protocol_model(
            protocol_model=protocol_model,
            title=title,
            creation_type=ScenarioCreationType.TRIGGERED_JOB,
        )

        # Add task to protocol using ProtocolService
        ProtocolService.add_process_to_protocol(
            protocol_model=protocol_model,
            process_type=task_class,
            instance_name="main_task",
            config_params=config_values,
        )

        return scenario

    # ========================== READ ==========================

    @classmethod
    def get_by_id_and_check(cls, job_id: str) -> TriggeredJobModel:
        """Get a job by ID and raise 404 if not found"""
        return TriggeredJobModel.get_by_id_and_check(job_id)

    @classmethod
    def get_all(cls) -> list[TriggeredJobModel]:
        """Get all triggered jobs"""
        return list(TriggeredJobModel.select().order_by(TriggeredJobModel.name))

    @classmethod
    def get_runs(cls, job_id: str, limit: int = 100) -> list[TriggeredJobRunModel]:
        """Get all runs for a job"""
        job = cls.get_by_id_and_check(job_id)
        return TriggeredJobRunModel.get_runs_for_job(job, limit)

    @classmethod
    def get_run_by_id_and_check(cls, run_id: str) -> TriggeredJobRunModel:
        """Get a run by ID and raise 404 if not found"""
        return TriggeredJobRunModel.get_by_id_and_check(run_id)

    # ========================== DTO CONVERSION ==========================

    @classmethod
    def to_dto(cls, job: TriggeredJobModel) -> TriggeredJobDTO:
        """Convert a TriggeredJobModel to DTO"""
        last_run = job.get_last_run()

        return TriggeredJobDTO(
            id=job.id,
            created_at=job.created_at,
            last_modified_at=job.last_modified_at,
            created_by=job.created_by.to_dto() if job.created_by else None,
            last_modified_by=job.last_modified_by.to_dto() if job.last_modified_by else None,
            name=job.name,
            description=job.description,
            trigger_type=job.trigger_type,
            is_active=job.is_active,
            cron_expression=job.cron_expression,
            next_run_at=job.next_run_at,
            process_typing=job.process_typing.to_ref_dto() if job.process_typing else None,
            scenario_template_id=job.scenario_template.id if job.scenario_template else None,
            scenario_template_name=job.scenario_template.name if job.scenario_template else None,
            config_values=job.config_values,
            last_run=cls.run_to_dto(last_run) if last_run else None,
        )

    @classmethod
    def run_to_dto(cls, run: TriggeredJobRunModel) -> TriggeredJobRunDTO:
        """Convert a TriggeredJobRunModel to DTO"""
        return TriggeredJobRunDTO(
            id=run.id,
            created_at=run.created_at,
            last_modified_at=run.last_modified_at,
            triggered_job_id=run.triggered_job.id,
            trigger=run.trigger,
            scenario_id=run.scenario.id if run.scenario else None,
            started_at=run.started_at,
            ended_at=run.ended_at,
            status=run.status,
            error_info=run.error_info,
            duration_seconds=run.get_duration_seconds(),
        )

    # ========================== HELPERS ==========================

    @classmethod
    def _validate_cron_expression(cls, cron_expression: str) -> None:
        """Validate a cron expression"""
        if not cron_expression:
            raise BadRequestException("Cron expression is required")

        try:
            croniter(cron_expression)
        except Exception as e:
            raise BadRequestException(f"Invalid cron expression: {e}")
