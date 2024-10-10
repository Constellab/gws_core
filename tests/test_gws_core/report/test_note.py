

from gws_core.folder.space_folder import SpaceFolder
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import (RichTextBlockType,
                                                     RichTextDTO)
from gws_core.impl.robot.robot_resource import Robot
from gws_core.impl.robot.robot_tasks import RobotCreate
from gws_core.note.note import Note, NoteScenario
from gws_core.note.note_dto import NoteInsertTemplateDTO, NoteSaveDTO
from gws_core.note.note_service import NoteService
from gws_core.note.note_view_model import NoteViewModel
from gws_core.note_template.note_template_service import NoteTemplateService
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_service import ResourceService
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.scenario.scenario_service import ScenarioService
from gws_core.test.base_test_case import BaseTestCase


# test_note
class TestNote(BaseTestCase):

    def test_note(self):
        folder = SpaceFolder(title='Folder').save()

        # test create an empty note
        note: Note = NoteService.create(NoteSaveDTO(title='Test note'))

        self.assertIsInstance(note, Note)
        self.assertEqual(note.title, 'Test note')

        note = NoteService.update(note.id, NoteSaveDTO(title='New title'))
        self.assertEqual(note.title, 'New title')

        content: RichTextDTO = RichText.create_rich_text_dto([RichText.create_paragraph('1', 'Hello world!')])
        NoteService.update_content(note.id, content)
        note = note.refresh()
        self.assertEqual(len(note.content.blocks), 1)

        scenario = ScenarioService.create_scenario()

        # Create a second scenario with a note
        scenario_2 = ScenarioService.create_scenario()
        note_2 = NoteService.create(NoteSaveDTO(title='Note 2'), [scenario_2.id])

        # Add exp 1 on note 1
        NoteService.add_scenario(note.id, scenario.id)
        notes = NoteService.get_by_scenario(scenario.id)
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0].id, note.id)

        # Check that note_2 ha an scenario
        notes = NoteService.get_by_scenario(scenario_2.id)
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0].id, note_2.id)

        # Check get scenario by note
        scenarios = NoteService.get_scenarios_by_note(note.id)
        self.assertEqual(len(scenarios), 1)
        self.assertEqual(scenarios[0].id, scenario.id)

        # Test remove scenario
        NoteService.remove_scenario(note.id, scenario.id)
        notes = NoteService.get_by_scenario(scenario.id)
        self.assertEqual(len(notes), 0)

        # Try to validate note_2, but there should be an error because the scenario is not validated
        self.assertRaises(Exception, NoteService._validate, note_2.id)
        scenario_2.is_validated = True
        scenario_2.folder = folder
        scenario_2.save()

        note_2 = NoteService._validate(note_2.id, folder.id)
        self.assertTrue(note_2.is_validated)

        # Try to update note_2
        self.assertRaises(Exception, NoteService.update_content, note_2.id, {})

        # Add exp 1 on note 1 to delete it afterward
        NoteService.add_scenario(note.id, scenario.id)
        NoteService.delete(note.id)
        self.assertIsNone(Note.get_by_id(note.id))
        self.assertEqual(len(NoteService.get_scenarios_by_note(note.id)), 0)

    def test_associated_views(self):
        """ Test when we add a resource view, it created an associated resource for the note
        """
        # create note and resource
        note = NoteService.create(NoteSaveDTO(title='Test note'))
        resource_model = ResourceModel.save_from_resource(Robot.empty(), ResourceOrigin.UPLOADED)

        view_result = ResourceService.call_view_on_resource_model(resource_model, "view_as_json", {}, True)

        # simulate the rich text with resource id
        rich_text_resource_view = view_result.view_config.to_rich_text_resource_view()
        block = RichText.create_block('1', RichTextBlockType.RESOURCE_VIEW, rich_text_resource_view)

        # update note content
        new_content = RichText.create_rich_text_dto([block])
        NoteService.update_content(note.id, new_content)

        # check that the associated NoteViewModel is created
        note_views = NoteViewModel.get_by_note(note.id)
        self.assertEqual(len(note_views), 1)

        # test get note by resource
        paginator = NoteService.get_by_resource(resource_model.id)
        # check result
        self.assertEqual(paginator.page_info.total_number_of_items, 1)
        self.assertEqual(paginator.results[0].id, note.id)

        # test adding the same resource a second time it shouldn't create a new associated view
        new_content = RichText.create_rich_text_dto([block, block])
        NoteService.update_content(note.id, new_content)
        note_views = NoteViewModel.get_by_note(note.id)
        self.assertEqual(len(note_views), 1)

        # test removing the resource
        new_content = RichText.create_rich_text_dto([])
        NoteService.update_content(note.id, new_content)
        note_views = NoteViewModel.get_by_note(note.id)
        self.assertEqual(len(note_views), 0)

    # test to have a view config to a note
    def test_add_view_config_to_note(self):
        # generate a resource from an scenario
        scenario = ScenarioProxy()
        scenario.get_protocol().add_process(RobotCreate, 'create')
        scenario.run()

        i_process = scenario.get_protocol().get_process('create')
        robot_model = i_process.get_output_resource_model('robot')

        # create a view config
        result = ResourceService.call_view_on_resource_model(robot_model, "view_as_string", {}, True)

        note = NoteService.create(NoteSaveDTO(title='Test note'))
        # add the view to the note
        NoteService.add_view_to_content(note.id, result.view_config.id)

        # Retrieve the note rich text
        note_db = NoteService.get_by_id_and_check(note.id)
        rich_text = note_db.get_content_as_rich_text()

        # check that a view exist in the rich text
        resource_views = rich_text.get_resource_views_data()
        self.assertEqual(len(resource_views), 1)
        self.assertEqual(resource_views[0]['view_method_name'], "view_as_string")
        self.assertEqual(resource_views[0]['resource_id'], robot_model.id)

        # verify that the note was automatically associated with the scenario
        self.assertEqual(NoteScenario.find_by_pk(scenario.get_model().id, note.id).count(), 1)

        with self.assertRaises(Exception):
            # Check that we cannot remove the scenario because of the view
            NoteService.remove_scenario(note.id, scenario.get_model().id)

        # remove the view from the note
        NoteService.update_content(note.id, RichText.create_rich_text_dto([]))

        # Check that we cannot remove the scenario because of the view
        NoteService.remove_scenario(note.id, scenario.get_model().id)

    def test_insert_note_template(self):
        # prepare the data
        note_template = NoteTemplateService.create_empty('title')
        rich_text = RichText()
        rich_text.add_paragraph('First paragraph')
        rich_text.add_paragraph('Second paragraph')
        NoteTemplateService.update_content(note_template.id, rich_text.get_content())

        note = NoteService.create(NoteSaveDTO(title='Test note'))
        note_rich_text = RichText()
        note_rich_text.add_paragraph('Start note')
        note_rich_text.add_paragraph('End note')
        NoteService.update_content(note.id, note_rich_text.get_content())

        # inser the note template in the note
        data = NoteInsertTemplateDTO(block_index=1, note_template_id=note_template.id)
        NoteService.insert_template(note.id, data)

        note = note.refresh()
        note_rich_text = note.get_content_as_rich_text()

        expected_blocks = [
            {"id": "1", "type": "paragraph", "data": {"text": "Start note"}},
            {"id": "2", "type": "paragraph", "data": {"text": "First paragraph"}},
            {"id": "3", "type": "paragraph", "data": {"text": "Second paragraph"}},
            {"id": "4", "type": "paragraph", "data": {"text": "End note"}}
        ]

        self.assert_json(note_rich_text.get_content_as_json().get('blocks'), expected_blocks, ['id'])
