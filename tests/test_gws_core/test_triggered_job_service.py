from gws_core import BaseTestCase
from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException
from gws_core.impl.robot.robot_protocol import RobotSimpleTravel
from gws_core.impl.robot.robot_service import RobotService
from gws_core.impl.robot.robot_tasks import RobotCreate
from gws_core.model.typing import Typing
from gws_core.protocol.protocol_service import ProtocolService
from gws_core.scenario.scenario_enums import ScenarioStatus
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.scenario_template.scenario_template_service import ScenarioTemplateService
from gws_core.triggered_job.triggered_job_dto import (
    CreateTriggeredJobFromProcessDTO,
    CreateTriggeredJobFromTemplateDTO,
    UpdateTriggeredJobDTO,
)
from gws_core.triggered_job.triggered_job_model import TriggeredJobModel
from gws_core.triggered_job.triggered_job_service import TriggeredJobService
from gws_core.triggered_job.triggered_job_types import (
    JobRunTrigger,
    JobStatus,
    TriggerType,
)


# test_triggered_job_service
class TestTriggeredJobService(BaseTestCase):
    def test_create_from_task(self):
        """Test creating a triggered job from a Task"""
        # Get the typing for RobotCreate
        typing = Typing.get_by_model_type(RobotCreate)

        dto = CreateTriggeredJobFromProcessDTO(
            process_typing_name=typing.typing_name,
            cron_expression="0 * * * *",
            is_active=False,
            name="Test Robot Create Job",
            description="Test job",
        )

        job = TriggeredJobService.create_from_process(dto)

        self.assertIsNotNone(job.id)
        self.assertEqual(job.name, "Test Robot Create Job")
        self.assertEqual(job.cron_expression, "0 * * * *")
        self.assertFalse(job.is_active)
        self.assertTrue(job.uses_process_typing())
        self.assertEqual(job.process_typing.typing_name, typing.typing_name)

    def test_create_from_protocol(self):
        """Test creating a triggered job from a Protocol"""
        # Get the typing for RobotSimpleTravel
        typing = Typing.get_by_model_type(RobotSimpleTravel)

        dto = CreateTriggeredJobFromProcessDTO(
            process_typing_name=typing.typing_name,
            cron_expression="*/15 * * * *",
            is_active=True,
            name="Robot Protocol Job",
            description="Execute robot protocol every 15 minutes",
        )

        job = TriggeredJobService.create_from_process(dto)

        self.assertIsNotNone(job.id)
        self.assertTrue(job.is_active)
        self.assertIsNotNone(job.next_run_at)
        self.assertEqual(job.process_typing.typing_name, typing.typing_name)

    def test_create_from_invalid_typing(self):
        """Test that creating from invalid typing raises error"""
        dto = CreateTriggeredJobFromProcessDTO(
            process_typing_name="invalid.typing",
            cron_expression="0 * * * *",
            is_active=False,
            name="Invalid Job",
        )

        with self.assertRaises(BadRequestException):
            TriggeredJobService.create_from_process(dto)

    def test_create_from_template(self):
        """Test creating a triggered job from a ScenarioTemplate"""
        # Create a scenario template first
        proto = RobotService.create_robot_simple_travel()

        template = ScenarioTemplateService.create_from_protocol(
            protocol=proto, name="Robot Template"
        )

        dto = CreateTriggeredJobFromTemplateDTO(
            scenario_template_id=template.id,
            cron_expression="0 2 * * *",
            is_active=False,
            name="Template Job",
            description="Job from template",
        )

        job = TriggeredJobService.create_from_template(dto)

        self.assertIsNotNone(job.id)
        self.assertEqual(job.name, "Template Job")
        self.assertTrue(job.uses_scenario_template())
        self.assertEqual(job.scenario_template.id, template.id)

    def test_invalid_cron_expression(self):
        """Test that invalid cron expression raises error"""
        typing = Typing.get_by_model_type(RobotCreate)

        dto = CreateTriggeredJobFromProcessDTO(
            process_typing_name=typing.typing_name,
            cron_expression="invalid cron",
            is_active=False,
            name="Invalid Cron Job",
        )

        with self.assertRaises(BadRequestException):
            TriggeredJobService.create_from_process(dto)

    def test_update_job(self):
        """Test updating a triggered job"""
        # Create job
        typing = Typing.get_by_model_type(RobotCreate)

        dto = CreateTriggeredJobFromProcessDTO(
            process_typing_name=typing.typing_name,
            cron_expression="0 * * * *",
            is_active=False,
            name="Original Name",
        )
        job = TriggeredJobService.create_from_process(dto)

        # Update job
        update_dto = UpdateTriggeredJobDTO(
            name="Updated Name", description="Updated description", cron_expression="0 0 * * *"
        )
        updated_job = TriggeredJobService.update(job.id, update_dto)

        self.assertEqual(updated_job.name, "Updated Name")
        self.assertEqual(updated_job.description, "Updated description")
        self.assertEqual(updated_job.cron_expression, "0 0 * * *")

    def test_activate_deactivate(self):
        """Test activating and deactivating a job"""
        typing = Typing.get_by_model_type(RobotCreate)

        dto = CreateTriggeredJobFromProcessDTO(
            process_typing_name=typing.typing_name,
            cron_expression="0 * * * *",
            is_active=False,
            name="Test Job",
        )
        job = TriggeredJobService.create_from_process(dto)

        # Activate
        activated_job = TriggeredJobService.activate(job.id)
        self.assertTrue(activated_job.is_active)
        self.assertIsNotNone(activated_job.next_run_at)

        # Deactivate
        deactivated_job = TriggeredJobService.deactivate(job.id)
        self.assertFalse(deactivated_job.is_active)
        self.assertIsNone(deactivated_job.next_run_at)

    def test_delete_job(self):
        """Test deleting a job"""
        typing = Typing.get_by_model_type(RobotCreate)

        dto = CreateTriggeredJobFromProcessDTO(
            process_typing_name=typing.typing_name,
            cron_expression="0 * * * *",
            is_active=False,
            name="Job to Delete",
        )
        job = TriggeredJobService.create_from_process(dto)
        job_id = job.id

        # Delete
        TriggeredJobService.delete(job_id)

        # Verify deletion
        with self.assertRaises(Exception):
            TriggeredJobModel.get_by_id_and_check(job_id)

    def test_get_all_jobs(self):
        """Test retrieving all jobs"""
        initial_count = len(TriggeredJobService.get_all())

        # Create two jobs
        typing = Typing.get_by_model_type(RobotCreate)

        dto1 = CreateTriggeredJobFromProcessDTO(
            process_typing_name=typing.typing_name,
            cron_expression="0 * * * *",
            is_active=False,
            name="Job 1",
        )
        dto2 = CreateTriggeredJobFromProcessDTO(
            process_typing_name=typing.typing_name,
            cron_expression="0 2 * * *",
            is_active=False,
            name="Job 2",
        )

        TriggeredJobService.create_from_process(dto1)
        TriggeredJobService.create_from_process(dto2)

        all_jobs = TriggeredJobService.get_all()
        self.assertEqual(len(all_jobs), initial_count + 2)

    def test_execute_job_from_task(self):
        """Test executing a job that uses a Task"""
        typing = Typing.get_by_model_type(RobotCreate)

        dto = CreateTriggeredJobFromProcessDTO(
            process_typing_name=typing.typing_name,
            cron_expression="0 * * * *",
            is_active=False,
            name="Executable Job",
        )
        job = TriggeredJobService.create_from_process(dto)

        # Execute manually
        run = TriggeredJobService.execute_job(job, JobRunTrigger.MANUAL)

        self.assertIsNotNone(run.id)
        self.assertEqual(run.trigger, JobRunTrigger.MANUAL)
        self.assertEqual(run.triggered_job.id, job.id)
        self.assertIsNotNone(run.scenario)
        self.assertIn(run.status, [JobStatus.SUCCESS, JobStatus.ERROR])

    def test_to_dto_conversion(self):
        """Test DTO conversion"""
        typing = Typing.get_by_model_type(RobotCreate)

        dto = CreateTriggeredJobFromProcessDTO(
            process_typing_name=typing.typing_name,
            cron_expression="0 * * * *",
            is_active=True,
            name="DTO Test Job",
            description="Test DTO",
        )
        job = TriggeredJobService.create_from_process(dto)

        job_dto = TriggeredJobService.to_dto(job)

        self.assertEqual(job_dto.id, job.id)
        self.assertEqual(job_dto.name, "DTO Test Job")
        self.assertEqual(job_dto.description, "Test DTO")
        self.assertEqual(job_dto.trigger_type, TriggerType.CRON)
        self.assertTrue(job_dto.is_active)
        self.assertIsNotNone(job_dto.process_typing)

    def test_execute_job_from_template(self):
        """Test executing a job that uses a ScenarioTemplate"""
        # Create a protocol with RobotCreate task
        scenario = ScenarioProxy()
        scenario.get_protocol().add_task(RobotCreate)

        # Create a scenario template from the protocol
        template = ProtocolService.create_scenario_template_from_id(
            protocol_id=scenario.get_protocol().get_model_id(), name="Robot Create Template"
        )

        # Create a triggered job from the template
        dto = CreateTriggeredJobFromTemplateDTO(
            scenario_template_id=template.id,
            cron_expression="0 * * * *",
            is_active=False,
            name="Template Job Execution",
            description="Execute template job",
        )
        job = TriggeredJobService.create_from_template(dto)

        # Execute the job manually
        run = TriggeredJobService.execute_job(job, JobRunTrigger.MANUAL)

        # Verify the run was created
        self.assertIsNotNone(run.id)
        self.assertEqual(run.trigger, JobRunTrigger.MANUAL)
        self.assertEqual(run.triggered_job.id, job.id)
        self.assertIsNotNone(run.scenario)

        # Verify the scenario was created and executed
        scenario = run.scenario.refresh()
        self.assertIsNotNone(scenario)
        self.assertIn(scenario.status, [ScenarioStatus.SUCCESS, ScenarioStatus.ERROR])

        # Verify the run status matches the scenario status
        run = run.refresh()
        if scenario.is_success:
            self.assertEqual(run.status, JobStatus.SUCCESS)
        else:
            self.assertEqual(run.status, JobStatus.ERROR)
