

from typing import List

from gws_core import BaseTestCase
from gws_core.study.study import Study
from gws_core.study.study_dto import StudyDto
from gws_core.study.study_service import StudyService


class TestStudy(BaseTestCase):

    def test_get_or_create_study(self):

        study_dto: StudyDto = StudyDto(uri="caf61803-70e5-4ac3-9adb-53a35f65a2f1",
                                       title="Study", description="Description")

        study: Study = StudyService.get_or_create_study_from_dto(study_dto)

        self.assertEqual(Study.select().count(), 1)
        self.assertEqual(study.uri, "caf61803-70e5-4ac3-9adb-53a35f65a2f1")
        self.assertEqual(study.title, "Study")
        self.assertEqual(study.description, "Description")

        # Check that if we call the same study, it doesn't create a new one
        study: Study = StudyService.get_or_create_study_from_dto(study_dto)
        self.assertEqual(Study.select().count(), 1)

        studies: List[Study] = StudyService.get_available_studies()
        self.assertEqual(len(studies), 1)
