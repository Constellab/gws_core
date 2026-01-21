from fastapi import Depends

from gws_core.triggered_job.triggered_job_dto import (
    ActivateTriggeredJobDTO,
    CreateTriggeredJobFromProcessDTO,
    CreateTriggeredJobFromTemplateDTO,
    TriggeredJobDTO,
    TriggeredJobRunDTO,
    UpdateTriggeredJobDTO,
)
from gws_core.triggered_job.triggered_job_service import TriggeredJobService
from gws_core.user.authorization_service import AuthorizationService

from ..core_controller import core_app


# ========================== CREATE ==========================

@core_app.post("/triggered-jobs/from-process", tags=["Triggered Jobs"])
def create_from_process(
    dto: CreateTriggeredJobFromProcessDTO,
    _=Depends(AuthorizationService.check_user_access_token),
) -> TriggeredJobDTO:
    """Create a triggered job from a Task or Protocol typing"""
    job = TriggeredJobService.create_from_process(dto)
    return TriggeredJobService.to_dto(job)


@core_app.post("/triggered-jobs/from-template", tags=["Triggered Jobs"])
def create_from_template(
    dto: CreateTriggeredJobFromTemplateDTO,
    _=Depends(AuthorizationService.check_user_access_token),
) -> TriggeredJobDTO:
    """Create a triggered job from a ScenarioTemplate"""
    job = TriggeredJobService.create_from_template(dto)
    return TriggeredJobService.to_dto(job)


# ========================== READ ==========================

@core_app.get("/triggered-jobs", tags=["Triggered Jobs"])
def get_all(
    _=Depends(AuthorizationService.check_user_access_token),
) -> list[TriggeredJobDTO]:
    """Get all triggered jobs"""
    jobs = TriggeredJobService.get_all()
    return [TriggeredJobService.to_dto(job) for job in jobs]


@core_app.get("/triggered-jobs/{id_}", tags=["Triggered Jobs"])
def get_by_id(
    id_: str,
    _=Depends(AuthorizationService.check_user_access_token),
) -> TriggeredJobDTO:
    """Get a triggered job by ID"""
    job = TriggeredJobService.get_by_id_and_check(id_)
    return TriggeredJobService.to_dto(job)


@core_app.get("/triggered-jobs/{id_}/runs", tags=["Triggered Jobs"])
def get_runs(
    id_: str,
    limit: int = 100,
    _=Depends(AuthorizationService.check_user_access_token),
) -> list[TriggeredJobRunDTO]:
    """Get all runs for a triggered job"""
    runs = TriggeredJobService.get_runs(id_, limit)
    return [TriggeredJobService.run_to_dto(run) for run in runs]


@core_app.get("/triggered-jobs/runs/{run_id}", tags=["Triggered Jobs"])
def get_run_by_id(
    run_id: str,
    _=Depends(AuthorizationService.check_user_access_token),
) -> TriggeredJobRunDTO:
    """Get a specific run by ID"""
    run = TriggeredJobService.get_run_by_id_and_check(run_id)
    return TriggeredJobService.run_to_dto(run)


# ========================== UPDATE ==========================

@core_app.put("/triggered-jobs/{id_}", tags=["Triggered Jobs"])
def update(
    id_: str,
    dto: UpdateTriggeredJobDTO,
    _=Depends(AuthorizationService.check_user_access_token),
) -> TriggeredJobDTO:
    """Update a triggered job"""
    job = TriggeredJobService.update(id_, dto)
    return TriggeredJobService.to_dto(job)


# ========================== ACTIVATION ==========================

@core_app.post("/triggered-jobs/{id_}/activate", tags=["Triggered Jobs"])
def activate(
    id_: str,
    dto: ActivateTriggeredJobDTO = None,
    _=Depends(AuthorizationService.check_user_access_token),
) -> TriggeredJobDTO:
    """Activate a triggered job"""
    job = TriggeredJobService.activate(id_, dto)
    return TriggeredJobService.to_dto(job)


@core_app.post("/triggered-jobs/{id_}/deactivate", tags=["Triggered Jobs"])
def deactivate(
    id_: str,
    _=Depends(AuthorizationService.check_user_access_token),
) -> TriggeredJobDTO:
    """Deactivate a triggered job"""
    job = TriggeredJobService.deactivate(id_)
    return TriggeredJobService.to_dto(job)


# ========================== EXECUTION ==========================

@core_app.post("/triggered-jobs/{id_}/run", tags=["Triggered Jobs"])
def run_manual(
    id_: str,
    _=Depends(AuthorizationService.check_user_access_token),
) -> TriggeredJobRunDTO:
    """Manually trigger a job execution"""
    run = TriggeredJobService.run_manual(id_)
    return TriggeredJobService.run_to_dto(run)


# ========================== DELETE ==========================

@core_app.delete("/triggered-jobs/{id_}", tags=["Triggered Jobs"])
def delete(
    id_: str,
    _=Depends(AuthorizationService.check_user_access_token),
) -> None:
    """Delete a triggered job"""
    TriggeredJobService.delete(id_)
