

import os
from copy import deepcopy
from typing import Dict, Optional, TypeVar, cast, final

from gws_core.core.model.base_typing import BaseTyping
from gws_core.impl.file.file_r_field import FileRField
from gws_core.model.typing_manager import TypingManager
from gws_core.model.typing_style import (TypingIconColor, TypingIconType,
                                         TypingStyle)
from gws_core.resource.kv_store import KVStore
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.technical_info import TechnicalInfo, TechnicalInfoDict
from gws_core.tag.tag_list import TagList
from gws_core.tag.tag_list_field import TagListField
from regex import T

from ..config.config_params import ConfigParams
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.utils.reflector_helper import ReflectorHelper
from ..impl.json.json_view import JSONView
from ..model.typing_register_decorator import typing_registrator
from .r_field.primitive_r_field import UUIDRField
from .r_field.r_field import BaseRField, RFieldStorage
from .r_field.serializable_r_field import SerializableRField
from .view.view_decorator import view

# Typing names generated for the class resource
CONST_RESOURCE_TYPING_NAME = "RESOURCE.gws_core.Resource"

ResourceType = TypeVar('ResourceType', bound='Resource')


@typing_registrator(unique_name="Resource", object_type="RESOURCE",
                    style=TypingStyle.default_resource())
class Resource(BaseTyping):

    uid: str = UUIDRField(storage=RFieldStorage.DATABASE)
    name: str | None
    technical_info = cast(TechnicalInfoDict, SerializableRField(TechnicalInfoDict))

    # set this during the run of a task to apply a dynamic style to the resource
    # This overrides the style set byt the resource_decorator
    style: TypingStyle | None

    # provide tags to this attribute to save them on resource generation
    tags: TagList = cast(TagList, TagListField())

    flagged: bool

    # Set by the resource parent on creation
    # //!\\ Do not modify theses values
    __model_id__: str | None = None
    __kv_store__: KVStore | None = None
    __origin__: ResourceOrigin | None = None

    # Provided at the Class level automatically by the @ResourceDecorator
    # //!\\ Do not modify theses values
    __is_exportable__: bool = False

    def __init__(self):
        """
        Constructor, please do not overwrite this method, use the init method instead
        Leave the constructor without parameters.
        """

        # check that the class level property typing_name is set
        if self.get_typing_name() == CONST_RESOURCE_TYPING_NAME and type(self) != Resource:  # pylint: disable=unidiomatic-typecheck
            raise BadRequestException(
                f"The resource {self.full_classname()} is not decorated with @resource_decorator, it can't be instantiate. Please decorate the resource class with @ResourceDecorator")

        # init the default name
        self.name = None
        self.style = None
        self.flagged = False
        # Init default values of BaseRField
        properties: Dict[str, BaseRField] = ReflectorHelper.get_property_names_of_type(type(self), BaseRField)
        for key, r_field in properties.items():
            setattr(self, key, r_field.get_default_value())

    def init(self) -> None:
        """
        This can be overwritten to perform custom initialization of the resource.
        This method is called after the __init__ (constructor) of the resource.
        The values of RFields are set when this method is called.
        """

    @view(view_type=JSONView, human_name="View resource", short_description="View the complete resource as json", default_view=True)
    def view_as_json(self, params: ConfigParams) -> JSONView:
        """By default the view_as_json dumps the RFields mark with, include_in_dict_view=True
        This method is used to send the resource information back to the interface
        """
        properties: Dict[str, BaseRField] = ReflectorHelper.get_property_names_of_type(type(self), BaseRField)

        json_ = {}
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
        return self.get_human_name()

    def get_name(self) -> str:
        """Get the name of the resource or the default name if the name is None

        :return: [description]
        :rtype: [type]
        """
        return self.name or self.get_default_name()

    def set_name(self, name: Optional[str]) -> None:
        """Set the name of the resource.
        You can override this method to force a format for the name of the resource.

        :param name: name to format
        :type name: str
        """
        if not name:
            self.name = self.get_default_name()
        else:
            if not isinstance(name, str):
                name = str(name)
            self.name = name.strip()

    def get_default_style(self) -> TypingStyle:
        """Get the default style of the resource

        :return: [description]
        :rtype: [type]
        """
        return self.get_style()

    def add_technical_info(self, technical_info: TechnicalInfo) -> None:
        """Add technical information on the resource. Technical info are useful to set additional information on the resource.

        :param technical_info: technical information to add (key, value)
        this is a long description of the technical information, defaults to None
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

    def check_resource(self) -> Optional[str]:
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
        clone: ResourceType = type(self)()

        model_id = self.get_model_id()
        if model_id:
            clone.__set_model_id__(model_id)
        # TODO copy other attributes (like tags, style, etc)

        # get the r_fields of the resource
        r_fields: Dict[str, BaseRField] = self.__get_resource_r_fields__()
        for fieldname, _ in r_fields.items():
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
            if not self.__kv_store__:
                return attr
            if name in self.__kv_store__:
                if isinstance(attr, FileRField):
                    value = attr.deserialize(self.__kv_store__.get_key_file_path(name))
                else:
                    value = attr.deserialize(self.__kv_store__.get(name))
                setattr(self, name, value)
                return value
            else:
                # if the key is not in the kv_store return the default
                # this can happend when the RField is new
                return attr.get_default_value()

        # lazy load the tags
        elif isinstance(attr, TagListField):
            tag_list = attr.load_tags(self.get_model_id())
            setattr(self, name, tag_list)
            return tag_list

        return attr

    @final
    def get_model_id(self) -> str | None:
        """Get the id of the resource model in the database.
        It is provided by the system for input resources of a task.

        :return: model id
        :rtype: str
        """
        return self.__model_id__

    ############################################### CLASS METHODS ####################################################

    @classmethod
    def copy_style(cls, icon_technical_name: str | None = None,
                   icon_type: TypingIconType | None = None,
                   background_color: str | None = None,
                   icon_color: TypingIconColor | None = None) -> TypingStyle:
        """Copy the style of the resource with the possibility to override some properties.
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
        style = TypingManager.get_typing_from_name_and_check(cls.get_typing_name()).style
        return style.clone_with_overrides(icon_technical_name, icon_type, background_color, icon_color)

    ############################################### SYSTEM METHODS ####################################################

    @final
    def __set_model_id__(self, model_id: str) -> None:
        """Set the model id of the resource
        This method is called by the system when the resource is created,
        you should not call this method yourself

        :param model_id: model id
        :type model_id: str
        """
        self.__model_id__ = model_id

    @final
    def __set_kv_store__(self, kv_store: KVStore) -> None:
        """Set the kv_store of the resource
        This method is called by the system when the resource is created,
        you should not call this method yourself

        :param kv_store: kv_store
        :type kv_store: KVStore
        """
        self.__kv_store__ = kv_store

    @final
    def __set_origin__(self, origin: ResourceOrigin) -> None:
        """ Override the origin of the resource, this is used to set a special origin to the resource.
        Use only when you know what you are doing.

        :param origin: origin
        :type origin: ResourceOrigin
        """
        self.__origin__ = origin

    @final
    @classmethod
    def __set_is_exportable__(cls, is_exportable: bool) -> None:
        """Set the resource as exportable. This method is called by the system when the resource is created,
        you should not call this method yourself

        :param is_exportable: is_exportable
        :type is_exportable: bool
        """
        cls.__is_exportable__ = is_exportable
