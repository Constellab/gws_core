

import os
from copy import deepcopy
from typing import Dict, TypeVar, Union, final

from gws_core.impl.file.file_r_field import FileRField
from gws_core.model.typing_manager import TypingManager
from gws_core.model.typing_style import (TypingIconColor, TypingIconType,
                                         TypingStyle)
from gws_core.resource.kv_store import KVStore
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.technical_info import TechnicalInfo, TechnicalInfoDict
from gws_core.tag.tag_list import TagList
from gws_core.tag.tag_list_field import TagListField

from ..config.config_params import ConfigParams
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.model.base import Base
from ..core.utils.reflector_helper import ReflectorHelper
from ..impl.json.json_view import JSONView
from ..model.typing_register_decorator import typing_registrator
from .r_field.primitive_r_field import UUIDRField
from .r_field.r_field import BaseRField
from .r_field.serializable_r_field import SerializableRField
from .view.view_decorator import view

# Typing names generated for the class resource
CONST_RESOURCE_TYPING_NAME = "RESOURCE.gws_core.Resource"

ResourceType = TypeVar('ResourceType', bound='Resource')


@typing_registrator(unique_name="Resource", object_type="RESOURCE",
                    style=TypingStyle.default_resource())
class Resource(Base):

    uid: str = UUIDRField(searchable=True)
    name: str
    technical_info: TechnicalInfoDict = SerializableRField(TechnicalInfoDict)

    # set this during the run of a task to apply a dynamic style to the resource
    # This overrides the style set byt the resource_decorator
    style: TypingStyle

    # provide tags to this attribute to save them on resource generation
    tags: TagList = TagListField()

    # Provided at the Class level automatically by the @ResourceDecorator
    # //!\\ Do not modify theses values
    _typing_name: str = None
    _human_name: str = None
    _short_description: str = None
    _is_exportable: bool = False
    # Set by the resource parent on creation
    _model_id: str = None
    _kv_store: KVStore = None
    __origin__: ResourceOrigin = None

    def __init__(self):
        """
        Constructor, please do not overwrite this method, use the init method instead
        Leave the constructor without parameters.
        """

        # check that the class level property _typing_name is set
        if self._typing_name == CONST_RESOURCE_TYPING_NAME and type(self) != Resource:  # pylint: disable=unidiomatic-typecheck
            raise BadRequestException(
                f"The resource {self.full_classname()} is not decorated with @ResourceDecorator, it can't be instantiate. Please decorate the resource class with @ResourceDecorator")

        # init the default name
        self.name = None
        self.style = None
        # Init default values of BaseRField
        properties: Dict[str, BaseRField] = ReflectorHelper.get_property_names_of_type(type(self), BaseRField)
        for key, r_field in properties.items():
            setattr(self, key, r_field.get_default_value())

        # call init
        self.init()

    def init(self) -> None:
        """
        This can be overwritten to perform custom initialization of the resource.
        This method is called just after the __init__ (constructor) of the resource.
        The default values of RFields are set before this method is called.
        """

    @view(view_type=JSONView, human_name="View resource", short_description="View the complete resource as json", default_view=True)
    def view_as_json(self, params: ConfigParams) -> JSONView:
        """By default the view_as_json dumps the RFields mark with, include_in_dict_view=True
        This method is used to send the resource information back to the interface
        """
        properties: Dict[str, BaseRField] = ReflectorHelper.get_property_names_of_type(type(self), BaseRField)

        json_: dict = {}
        for key, r_field in properties.items():
            if r_field.include_in_dict_view:
                json_[key] = r_field.serialize(getattr(self, key))

        return JSONView(json_)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Resource):
            return False
        return (self is o) or ((self.uid is not None) and (self.uid == o.uid))

    def __hash__(self):
        return hash(self.uid)

    def get_default_name(self) -> str:
        """You can redefine this method to set a name of the resource.
        When saving the resource the name will be saved automatically
        This can be useful to distinguish this resource from another one or to search for the resource

        :return: [description]
        :rtype: [type]
        """
        return self._human_name

    def add_technical_info(self, technical_info: TechnicalInfo) -> None:
        """Add technical information on the resource. Technical info are useful to set additional information on the resource.

        :param technical_info: technical information to add (key, value)
        :type technical_info: TechnicalInfo
        """
        self.technical_info.add(technical_info)

    def get_technical_info(self, key: str) -> TechnicalInfo:
        """Get the technical information of the resource


        :param key: key of the technical information
        :type key: str
        :return: _description_
        :rtype: TechnicalInfo
        """
        return self.technical_info.get(key)

    def check_resource(self) -> Union[str, None]:
        """You can redefine this method to define custom logic to check this resource.
        If there is a problem with the resource, return a string that define the error, otherwise return None
        This method is called on output resources of a task. If there is an error returned, the task will be set to error and next proceses will not be run.
        It is also call when uploading a resource (usually for files or folder), if there is an error returned, the resource will not be uploaded
        """
        return None

    def clone(self: ResourceType) -> ResourceType:
        """
        Clone the resource to create a new instance with a new id. It copies the RFields.

        :return: The cloned resource
        :rtype: Resource
        """
        clone: Resource = type(self)()
        clone._model_id = self._model_id

        # get the r_fields of the resource
        r_fields: Dict[str, BaseRField] = self.__get_resource_r_fields__()
        for fieldname, r_field in r_fields.items():
            value = getattr(self, fieldname)
            setattr(clone, fieldname, deepcopy(value))

        return clone

    @final
    @classmethod
    def __get_resource_r_fields__(cls) -> Dict[str, BaseRField]:
        """Get the list of resource's r_fields,
        the key is the property name, the value is the BaseRField object
        """
        return ReflectorHelper.get_property_names_of_type(cls, BaseRField)

    @final
    def __getattribute__(self, name):
        """Override get attribute to lazy load kvstore Rfields

        :param name: [description]
        :type name: [type]
        :return: [description]
        :rtype: [type]
        """
        attr = super().__getattribute__(name)

        if isinstance(attr, BaseRField):
            if name in self._kv_store:
                if isinstance(attr, FileRField):
                    value = attr.deserialize(os.path.join(self._kv_store.full_file_dir, self._kv_store.get(name)))
                else:
                    value = attr.deserialize(self._kv_store.get(name))
                setattr(self, name, value)
                return value
            else:
                # if the key is not in the kv_store return the default
                # this can happend when the RField is new
                return attr.get_default_value()

        # lazy load the tags
        elif isinstance(attr, TagListField):
            tag_list = attr.load_tags(self._model_id)
            setattr(self, name, tag_list)
            return tag_list

        return attr

    @classmethod
    def clone_style(cls, icon_technical_name: str = None,
                    icon_type: TypingIconType = None,
                    background_color: str = None,
                    icon_color: TypingIconColor = None) -> TypingStyle:
        """Clone the style of the resource with the possibility to override some properties.
        Useful when settings the style for a task based on the resource style.

        :param icon_technical_name: technical name of the icon if provided, the icon_type must also be provided, defaults to None
        :type icon_technical_name: str, optional
        :param icon_type: type of the icon if provided, the icon_technical_name must also be provided, defaults to None
        :type icon_type: TypingIconType, optional
        :param background_color: background color, defaults to None
        :type background_color: str, optional
        :param icon_color: icon color, defaults to None
        :type icon_color: TypingIconColor, optional
        :return: _description_
        :rtype: TypingStyle
        """
        style = TypingManager.get_typing_from_name_and_check(cls._typing_name).style
        return style.clone_with_overrides(icon_technical_name, icon_type, background_color, icon_color)
