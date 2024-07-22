
from typing import Any, Optional

from gws_core.config.param.param_spec import ParamSpec
from gws_core.config.param.param_spec_decorator import param_spec_decorator
from gws_core.config.param.param_types import ParamSpecVisibilty
from gws_core.core.classes.validator import StrValidator
from gws_core.document_template.document_template import DocumentTemplate


@param_spec_decorator()
class DocumentTemplateParam(ParamSpec[str]):
    """ Document template params spec. When used, the end user will be able to select a document template
    from the list of document template available in the lab.

    The accessible value will be document template.

    """

    def __init__(self,
                 optional: bool = False,
                 visibility: ParamSpecVisibilty = "public",
                 human_name: Optional[str] = "Select document template",
                 short_description: Optional[str] = None,
                 ):
        """
        :param optional: See default value
        :type optional: Optional[str]
        :param visibility: Visibility of the param, see doc on type ParamSpecVisibilty for more info
        :type visibility: ParamSpecVisibilty
        :type default: Optional[ConfigParamType]
        :param human_name: Human readable name of the param, showed in the interface
        :type human_name: Optional[str]
        :param short_description: Description of the param, showed in the interface
        :type short_description: Optional[str]
        """

        super().__init__(
            optional=optional,
            visibility=visibility,
            human_name=human_name,
            short_description=short_description,
        )

    @classmethod
    def get_str_type(cls) -> str:
        return "document_template_param"

    def build(self, value: Any) -> dict:
        document_template: DocumentTemplate = None
        if value and isinstance(value, str):

            # retrieve the document template and return it
            document_template = DocumentTemplate.get_by_id(value)
            if document_template is None:
                raise Exception(f"Document template with id '{value}' not found")

        return document_template

    def validate(self, value: Any) -> str:
        if isinstance(value, DocumentTemplate):
            return value.id
        # if this is the credentials object, retrieve the name
        if isinstance(value, dict) and 'id' in value:
            value = value['id']

        validator = StrValidator()
        return validator.validate(value)
