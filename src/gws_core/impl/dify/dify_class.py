from typing import Any, Dict, List, Literal, Optional

from gws_core.core.model.model_dto import BaseModelDTO

DifyIndexingTechnique = Literal['economic', 'high_quality']


class DifyUpdateDocumentOptions(BaseModelDTO):
    remove_extra_spaces: bool = True
    remove_urls_emails: bool = False
    chunk_separator: str = '\n\n'
    chunk_max_tokens: int = 500


class DifySendDocumentOptions(DifyUpdateDocumentOptions):
    indexing_technique: DifyIndexingTechnique = 'economic'
    lang: str = 'en'


class DifyDatasetDocument(BaseModelDTO):
    """Model for document information in the response."""
    id: str
    position: int
    data_source_type: str
    data_source_info: Dict[str, str]
    dataset_process_rule_id: str
    name: str
    created_from: str
    created_by: str
    created_at: int
    tokens: int
    indexing_status: str
    error: Optional[str] = None
    enabled: bool
    disabled_at: Optional[int] = None
    disabled_by: Optional[str] = None
    archived: bool


class DifySendDocumentResponse(BaseModelDTO):
    """Model for the response from sending a document."""
    document: DifyDatasetDocument
    batch: Optional[str] = None


class DifySendMessageSource(BaseModelDTO):
    dataset_id: str
    dataset_name: str
    document_id: str
    document_name: str
    data_source_type: Literal['upload_file']
    retriever_from: Literal['api']
    score: float  # 0-1


class DifySendMessageStreamResponse(BaseModelDTO):
    answer: str


class DifySendEndMessageStreamResponse(BaseModelDTO):
    conversation_id: Optional[str] = None
    sources: Optional[List[DifySendMessageSource]] = None


class DifyGetDocumentsResponse(BaseModelDTO):
    """Model for the response from retrieving documents."""
    data: List[DifyDatasetDocument]
    has_more: bool
    limit: int
    total: int
    page: int


class DifyChunkDocument(BaseModelDTO):
    """Model for document information within a chunk."""
    id: str
    data_source_type: str
    name: str
    doc_type: Optional[str] = None


class DifySegment(BaseModelDTO):
    """Model for segment information in a chunk."""
    id: str
    position: int
    document_id: str
    content: str
    sign_content: str
    answer: Optional[str] = None
    word_count: int
    tokens: int
    keywords: List[str]
    index_node_id: str
    index_node_hash: str
    hit_count: int
    enabled: bool
    disabled_at: Optional[int] = None
    disabled_by: Optional[str] = None
    status: str
    created_by: str
    created_at: int
    indexing_at: int
    completed_at: int
    error: Optional[str] = None
    stopped_at: Optional[int] = None
    document: DifyChunkDocument


class DifyChunkRecord(BaseModelDTO):
    """Model for a chunk record in the retrieval results."""
    segment: DifySegment
    child_chunks: Optional[Any]
    score: Optional[float] = None
    tsne_position: Optional[Any] = None


class DifyChunksResponse(BaseModelDTO):
    """Model for the response from retrieving chunks from a dataset."""
    query: Dict[str, str]
    records: List[DifyChunkRecord]

    def get_distinct_documents(self) -> List[DifyChunkDocument]:
        """Get distinct documents from the chunk records."""
        documents = {}
        for record in self.records:
            doc = record.segment.document
            if doc.id not in documents:
                documents[doc.id] = doc
        return list(documents.values())


class DifyDocumentChunk(BaseModelDTO):
    """Model for a document chunk."""
    id: str
    position: int
    document_id: str
    content: str
    answer: Optional[str] = None
    word_count: int
    tokens: int
    keywords: List[str]
    index_node_id: str
    index_node_hash: str
    hit_count: int
    enabled: bool
    disabled_at: Optional[int] = None
    disabled_by: Optional[str] = None
    status: str
    created_by: str
    created_at: int
    indexing_at: int
    completed_at: int
    error: Optional[str] = None
    stopped_at: Optional[int] = None


class DifyDocumentChunksResponse(BaseModelDTO):
    """Model for the response from retrieving chunks from a document."""
    data: List[DifyDocumentChunk]
    doc_form: str
    has_more: bool
    limit: int
    total: int
    page: int

    def count_words(self) -> int:
        """Count the total number of words in the chunks."""
        return sum(chunk.word_count for chunk in self.data)

    def get_all_chunk_texts(self) -> str:
        """Get all chunk texts."""
        return "\n".join(chunk.content for chunk in self.data)


class DifyUploadFile(BaseModelDTO):
    """Model for the response from retrieving upload file information."""
    id: str
    name: str
    size: int
    extension: str
    url: str
    download_url: str
    mime_type: str
    created_by: str
    created_at: float


class DifyUploadFileResponse(BaseModelDTO):
    file: DifyUploadFile
    base_dify_url: str  # used for old dify version

    def get_download_url(self) -> str:
        if self.file.download_url.startswith('https'):
            return self.file.download_url
        return self.base_dify_url + self.file.download_url


class DifyMetadata(BaseModelDTO):
    """Model for updating metadata."""
    id: str
    value: str
    name: str


class DifyCreateDatasetMetadataRequest(BaseModelDTO):
    """Model for updating metadata."""
    type: Literal['string', 'number', 'time']
    name: str


class DifyCreateDatasetMetadataResponse(BaseModelDTO):
    """Model for updating metadata."""
    id: str
    name: str
    type: Literal['string', 'number', 'time']


class DifyUpdateDocumentsMetadataRequest(BaseModelDTO):
    """Model for updating metadata."""
    document_id: str
    metadata_list: List[DifyMetadata]


class DifyGetDatasetMetadataResponseMetadata(BaseModelDTO):
    id: str
    name: str
    type: Literal['string', 'number', 'time']
    count: int


class DifyGetDatasetMetadataResponse(BaseModelDTO):
    """Model for getting dataset metadata."""
    doc_metadata: List[DifyGetDatasetMetadataResponseMetadata]
    built_in_field_enabled: bool
