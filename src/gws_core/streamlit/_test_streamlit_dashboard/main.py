

import os
from json import dump, load

import streamlit as st
from gws_core import ExternalSpaceCreateFolder, FSNode, SpaceService
from gws_core.streamlit import (ResourceSearchInput, StreamlitTranslateLang,
                                StreamlitTranslateService)
from gws_core.tag.tag import Tag

# from gws_core import FileHelper, RichText
# from gws_core.resource.resource_model import ResourceModel
# from gws_core.streamlit import rich_text_editor
# from gws_core.streamlit.widgets.streamlit_resource_select import \
# ResourceSearchInput

sources: list

st.title("Hello World")
# search = ResourceSearchInput().add_fs_node_extension_filter('.csv').select()

title = st.text_input(label='Title')

tag_key = st.text_input(label='Tag Key')

tag_value = st.text_input(label='Tag Value')

if st.button('Create Folder'):
    folder = ExternalSpaceCreateFolder(name=title, tags=[Tag(key=tag_key, value=tag_value)])
    SpaceService.get_instance().create_root_folder(folder)


id = st.text_input(label='Folder ID')

if st.button('Add or update tag'):
    SpaceService.get_instance().add_or_replace_tags_on_object(id, [Tag(key=tag_key, value=tag_value)])

if st.button('Add tag'):
    SpaceService.get_instance().add_tags_to_object(id, [Tag(key=tag_key, value=tag_value)])

if st.button('Delete tag'):
    SpaceService.get_instance().delete_tags_on_object(id, [Tag(key=tag_key, value=tag_value)])

translation_folder_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'trad')
translate_service = StreamlitTranslateService(translation_files_folder_path=translation_folder_path)
key = "a_test"

current_lang = translate_service.get_lang()

st.write("Translate : " + translate_service.translate(key))

if st.button('Change lang'):
    if current_lang == StreamlitTranslateLang.EN:
        current_lang = StreamlitTranslateLang.FR
    else:
        current_lang = StreamlitTranslateLang.EN

    translate_service.change_lang(current_lang)

# folder = sources[0]
# file_path = os.path.join(folder.path, 'test.json')
# images = os.path.join(folder.path, 'images')

# # FileHelper.create_dir_if_not_exist(images)
# default_resource = ResourceModel.get_by_id_and_check('f3aa406d-bac6-468c-aa96-19b0cc0b5ad9')

# selected_resource: ResourceModel | None = ResourceSearchInput().add_flagged_filter(
#     True).add_is_archived_filter(False) \
#     .add_order_by(ResourceModel.name) \
#     .select(placeholder="Search for folder")
# .select(placeholder="Search for folder")

# st.write('Hello ')
# # print('Selected
# #  resource ', selected_resource)

# if selected_resource:
#     st.write(selected_resource)

#     if isinstance(selected_resource, ResourceModel):
#         st.write("Is ResourceModel")

# rich_text: RichText = None
# if os.path.exists(file_path):
#     with open(file_path, 'r') as f:
#         # print('Loading from json ', str(load(f)))
#         rich_text = RichText.from_json(load(f))
# else:
#     rich_text = RichText()
# # rich_text.add_paragraph("Hello World c'est super")

# result = rich_text_editor(placeholder='Ma note', initial_value=rich_text,
#                           key="test")

# st.write('Result')
# if result:

#     print('Saving to', result.to_dto_json_dict())

#     with open(file_path, 'w') as f:
#         dump(result.to_dto_json_dict(), f)

# search_scenario_builder = ScenarioSearchBuilder().add_tag_filter(
#     Tag(key='test', value='test')).add_is_archived_filter(False)

# list_scenario: List[Scenario] = search_scenario_builder.search_all()

# scenario_proxy = ScenarioProxy.from_existing_scenario("ID du scenario")

# scenario_proxy.add_to_queue()
