

from gws_core.external_source.external_source import ExternalSource


class ExternalSourceService():

    @classmethod
    def get_or_create_external_source(cls, source_id: str, source_type: str, source_name: str) -> ExternalSource:
        """Get or create an external source

        :param source_id: the id of the source
        :type source_id: str
        :param source_type: the type of the source
        :type source_type: str
        :param source_name: the name of the source
        :type source_name: str
        :return: the external source
        :rtype: ExternalSource
        """
        external_source = ExternalSource.get_or_none(
            ExternalSource.source_id == source_id,
            ExternalSource.source_type == source_type
        )

        if external_source is None:
            external_source = ExternalSource.create(
                source_id=source_id,
                source_type=source_type,
                source_name=source_name
            )

        return external_source
