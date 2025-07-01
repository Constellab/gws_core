
from typing import Any, Dict, Generator, List, Optional, Union

from gws_core.core.utils.logger import Logger
from gws_core.impl.dify.datahub_dify_resource import DatahubDifyResource
from gws_core.impl.dify.dify_class import (
    DifyCreateDatasetMetadataRequest, DifyDatasetDocument,
    DifyGetDatasetMetadataResponseMetadata, DifyMetadata,
    DifySendDocumentOptions, DifySendDocumentResponse,
    DifySendEndMessageStreamResponse, DifySendMessageStreamResponse,
    DifyUpdateDocumentsMetadataRequest)
from gws_core.impl.dify.dify_service import DifyService
from gws_core.impl.s3.datahub_s3_server_service import DataHubS3ServerService
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_search_builder import ResourceSearchBuilder


class DatahubDifyService:

    dify_service: DifyService
    dataset_id: str

    DIFY_ROOT_FOLDER_ID_METADATA_KEY = 'root_folder_id'
    DIFY_CONSTELLAB_RESOURCE_ID_METADATA_KEY = 'constellab_resource_id'
    DIFY_CHAT_INPUT_ACCESS_KEY = 'folder_'

    def __init__(self, dify_service: DifyService, dataset_id: str) -> None:
        self.dify_service = dify_service
        self.dataset_id = dataset_id

    def send_resource_to_dify(self, dify_resource: DatahubDifyResource) -> None:
        """Send a resource to Dify for processing."""

        if dify_resource.is_compatible_with_dify() is False:
            raise ValueError("The resource is not compatible with Dify.")

        root_folder = dify_resource.get_root_folder()
        if root_folder is None:
            raise ValueError("The resource does not have a folder.")

        root_folder_metadata = self.get_or_create_dify_root_folder_metadata()
        resource_metadata = self.get_or_create_dify_resource_metadata()

        file = dify_resource.get_file_path()

        # Send the resource to Dify
        options = DifySendDocumentOptions(
            indexing_technique='high_quality',
            chunk_max_tokens=2048,
            chunk_separator=dify_resource.get_chunk_separator(file.path),
            lang='en',
        )

        dify_document: DifySendDocumentResponse
        if dify_resource.is_synced_with_dify():
            # if the resource is already synced with dify, we need to update the document
            dify_document = self.dify_service.update_document(file.path, self.dataset_id,
                                                              dify_resource.get_and_check_dify_document_id(),
                                                              options,
                                                              filename=file.get_name())
        else:
            dify_document = self.dify_service.send_document(file.path, self.dataset_id, options,
                                                            filename=file.get_name())

        try:

            metadata = DifyUpdateDocumentsMetadataRequest(
                document_id=dify_document.document.id,
                metadata_list=[DifyMetadata(id=root_folder_metadata.id, name=root_folder_metadata.name,
                                            value=root_folder.id),
                               DifyMetadata(id=resource_metadata.id, name=resource_metadata.name,
                                            value=dify_resource.resource_model.id)],
            )
            self.dify_service.update_document_metadata(self.dataset_id, body=[metadata])
        except Exception as e:
            Logger.error(
                f"Error while updating metadata for dify object {dify_resource.resource_model.id} after dify upload: {e}")
            Logger.log_exception_stack_trace(e)
            # delete the document from Dify
            self.dify_service.delete_document(self.dataset_id, dify_document.document.id)
            raise e

        try:

            # Add the Dify document tag to the resource
            dify_resource.mark_resource_as_sent_to_dify(dify_document.document.id, self.dataset_id)
        except Exception as e:
            Logger.error(
                f"Error while adding tags to resource {dify_resource.resource_model.id} after dify upload: {e}")
            Logger.log_exception_stack_trace(e)

            # delete the document from Dify
            self.dify_service.delete_document(self.dataset_id, dify_document.document.id)
            raise e

    def get_or_create_dify_root_folder_metadata(self) -> DifyGetDatasetMetadataResponseMetadata:
        """Get or create the access right metadata in Dify."""
        new_metadata = DifyCreateDatasetMetadataRequest(
            name=self.DIFY_ROOT_FOLDER_ID_METADATA_KEY,
            type='string',
        )
        return self.dify_service.get_or_create_dataset_metadata(self.dataset_id, new_metadata)

    def get_or_create_dify_resource_metadata(
            self) -> DifyGetDatasetMetadataResponseMetadata:
        """Get or create the resource metadata in Dify."""
        new_metadata = DifyCreateDatasetMetadataRequest(
            name=self.DIFY_CONSTELLAB_RESOURCE_ID_METADATA_KEY,
            type='string',
        )
        return self.dify_service.get_or_create_dataset_metadata(self.dataset_id, new_metadata)

    def delete_resource_from_dify(self, dify_resource: DatahubDifyResource) -> None:
        """Delete a resource from Dify."""
        if dify_resource.is_synced_with_dify() is False:
            raise ValueError("The resource is not synced with Dify.")

        # Delete the resource from Dify
        self.dify_service.delete_document(dify_resource.get_dify_knowledge_base_id(),
                                          dify_resource.get_and_check_dify_document_id())

        # Remove the tags from the resource
        dify_resource.unmark_resource_as_sent_to_dify()

    def delete_dify_document(self, dify_document_id: str) -> None:
        """Delete a document from Dify."""
        self.dify_service.delete_document(self.dataset_id, dify_document_id)

    def get_all_resource_to_sync(self) -> List[DatahubDifyResource]:
        """Get all resources to sync with Dify."""

        resource_models = self._get_compatible_resources()

        datahub_resources = []
        for resource_model in resource_models:
            # check if the resource is compatible with dify
            dify_resource = DatahubDifyResource(resource_model)

            if dify_resource.is_compatible_with_dify() and not dify_resource.is_up_to_date_in_dify():
                datahub_resources.append(dify_resource)

        return datahub_resources

    def get_all_synced_resources(self) -> List[DatahubDifyResource]:
        """Get all resources synced with Dify."""

        resource_models = self._get_compatible_resources()

        datahub_resources = []
        for resource_model in resource_models:
            # check if the resource is compatible with dify
            dify_resource = DatahubDifyResource(resource_model)
            if dify_resource.is_synced_with_dify():
                datahub_resources.append(dify_resource)

        return datahub_resources

    def _get_compatible_resources(self) -> List[ResourceModel]:
        """Get all resources compatible with Dify."""
        # retrive all the files stored in the datahub
        research_search = ResourceSearchBuilder()
        s3_service = DataHubS3ServerService.get_instance()
        research_search.add_tag_filter(s3_service.get_datahub_tag())
        research_search.add_is_fs_node_filter()
        research_search.add_is_archived_filter(False)
        research_search.add_has_folder_filter()

        return research_search.search_all()

    def get_dify_documents_to_delete(self) -> List[DifyDatasetDocument]:
        """List all the dify documents that are not in the datahub anymore."""

        dify_documents = self.dify_service.get_all_documents(self.dataset_id)

        document_to_delete = []
        for dify_document in dify_documents:
            # check if the resource is compatible with dify
            dify_resource = DatahubDifyResource.from_dify_document_id(dify_document.id)
            if dify_resource is None:
                document_to_delete.append(dify_document)

        return document_to_delete

    #################################### CHAT ####################################

    def send_message_stream(self,
                            user_root_folder_ids: List[str],
                            query: str,
                            user: str,
                            conversation_id: Optional[str] = None,
                            inputs: Optional[Dict[str, Any]] = None,
                            files: Optional[list] = None) -> Generator[Union[str, DifySendMessageStreamResponse, DifySendEndMessageStreamResponse], None, None]:
        """
        Call the Dify API chat endpoint with streaming response.

        Args:
            user_root_folder_ids: List of root folder ID accessible by the user to limit the search
            query: The user's message
            conversation_id: Optional ID for continuing a conversation
            user: Optional user identifier
            inputs: Optional dictionary of input variables
            files: Optional list of files to include

        Returns:
            Generator that yields response chunks (string or objects)
        """

        # convert the list of root folder ids to list of inputs
        inputs = inputs or {}

        for i, root_folder_id in enumerate(user_root_folder_ids):
            inputs[f'{self.DIFY_CHAT_INPUT_ACCESS_KEY}{i + 1}'] = root_folder_id

        # Call the Dify API with streaming
        return self.dify_service.send_message_stream(
            query=query,
            conversation_id=conversation_id,
            user=user,
            inputs=inputs,
            files=files
        )
