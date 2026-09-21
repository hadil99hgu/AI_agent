from pydantic import BaseModel
from dataclasses import dataclass
from typing import Any



class KnowledgeDocument(BaseModel):
    text: str
    source: str
    metadata: dict

class DocumentChunk(BaseModel):
    chunk_id: str
    text: str
    source: str
    metadata: dict

class RetrievedChunk(BaseModel):
    chunk: DocumentChunk
    score: float


@dataclass
class RAGState:
    chunks: list[DocumentChunk]
    vectorizer: Any
    sparse_vectors: Any
    document_embeddings: Any