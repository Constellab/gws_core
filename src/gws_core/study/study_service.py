
from typing import List

from gws_core.core.utils.logger import Logger
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.user import User
from pydantic.errors import NotNoneError

from ..central.central_service import CentralService
from ..core.service.base_service import BaseService
from .study import Study
from .study_dto import CentralStudy, StudyDto


class StudyService(BaseService):

    @classmethod
    def get_available_studies(cls) -> List[StudyDto]:

        central_studies: List[StudyDto] = cls.get_central_studies()

        lab_studies: List[StudyDto] = cls.get_lab_studies()

        # Add the lab studies to central studies and avoid duplicate
        for lab_study in lab_studies:
            if lab_study not in central_studies:
                central_studies.append(lab_study)

        return central_studies

    @classmethod
    def get_central_studies(cls) -> List[StudyDto]:
        central_studies: List[CentralStudy]
        try:
            central_studies = CentralService.get_current_user_studies()
        except Exception as err:
            Logger.log_exception_stack_trace(err)
            return []

        studies_dto: List[StudyDto] = []
        for study in central_studies:
            studies_dto.append(StudyDto(uri=study['id'], title=study['title'], description=study['description']))
        return studies_dto

    @classmethod
    def get_lab_studies(cls) -> List[StudyDto]:
        studies: List[Study] = list(Study.select())

        studies_dto: List[StudyDto] = []
        for study in studies:
            studies_dto.append(StudyDto(uri=study.uri, title=study.title, description=study.description))
        return studies_dto

    @classmethod
    def get_or_create_study_from_dto(cls, study_dto: StudyDto) -> Study:
        """Retreive the study based on a DTO and if it doesn't exists, it creates the study
        """
        if study_dto is None or study_dto.uri is None:
            return None

        study: Study = Study.get_by_uri(study_dto.uri)

        if study is not None:
            return study

        # Create the study form the DTO
        study = Study()
        study.uri = study_dto.uri
        study.title = study_dto.title
        study.description = study_dto.description
        study.owner = CurrentUserService.get_and_check_current_user()
        return study.save()
