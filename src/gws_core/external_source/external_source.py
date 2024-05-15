

from typing import Any, Dict

from peewee import CharField, TextField

from gws_core.core.model.db_field import JSONField
from gws_core.core.model.model_with_user import ModelWithUser


class ExternalSource(ModelWithUser):

    source_type = CharField(null=False)

    source_name = CharField(null=False)

    description = TextField(null=True)

    # store the information of the source
    data: Dict[str, Any] = JSONField(null=True)

    class Meta:
        indexes = (
            # unique index on source_type and source_name
            (("source_type", "source_name"), True),
        )
