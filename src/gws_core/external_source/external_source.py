

from peewee import CharField

from gws_core.core.model.model import Model


class ExternalSource(Model):

    source_id = CharField(null=False)

    source_type = CharField(null=False)

    source_name = CharField(null=False)

    class Meta:
        indexes = (
            (("source_id", "source_type"), True),
        )
