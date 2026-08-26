from dataclasses import dataclass

from gws_core.core.model.base import Base
from gws_core.model.typing_deprecated import TypingDeprecated
from gws_core.model.typing_dto import TypingErrorDTO, TypingObjectType
from gws_core.model.typing_style import TypingStyle


@dataclass
class TypingRegistration:
    """Description of a typing to register in the TypingManager.

    These values travel together from the decorators (resource, task, protocol, app...)
    down to the Typing model, so they are grouped in a single object instead of being
    re-declared and forwarded by every function of the chain.

    :param object_class: class to register
    :type object_class: type[Base]
    :param object_type: typing object type
    :type object_type: TypingObjectType
    :param unique_name: a unique name for this type in the brick. Only 1 object in the current brick can have this name.
                        //!\\ DO NOT MODIFIED THIS NAME ONCE IS DEFINED //!\\
    :type unique_name: str
    :param human_name: name used in the interface. If empty, it is generated from the unique_name
    :type human_name: str
    :param short_description: description used in the interface. Must not be longer than 255 caracters
    :type short_description: str
    :param hide: if True the typing class will not be shown to the user when retriving the typings, defaults to False
    :type hide: bool
    :param style: style of the object, view TypingStyle object for more info, defaults to None
    :type style: TypingStyle | None
    :param object_sub_type: sub type of the object (like the task type), defaults to None
    :type object_sub_type: str | None
    :param related_model_typing_name: typing name of a related model (like the resource of a task), defaults to None
    :type related_model_typing_name: str | None
    :param deprecated: object to tell that the object is deprecated. See TypingDeprecated for more info, defaults to None
    :type deprecated: TypingDeprecated | None
    :param definition_errors: errors found while defining the object. The object is registered but marked as broken, defaults to None
    :type definition_errors: list[TypingErrorDTO] | None
    """

    object_class: type[Base]
    object_type: TypingObjectType
    unique_name: str
    human_name: str = ""
    short_description: str = ""
    hide: bool = False
    style: TypingStyle | None = None
    object_sub_type: str | None = None
    related_model_typing_name: str | None = None
    deprecated: TypingDeprecated | None = None
    definition_errors: list[TypingErrorDTO] | None = None
