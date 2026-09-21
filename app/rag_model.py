from pydantic import BaseModel



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