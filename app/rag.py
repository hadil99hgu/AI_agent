from app.rag_model import KnowledgeDocument,DocumentChunk,RetrievedChunk
from pathlib import Path
import yaml
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity





def load_document(path: Path) -> KnowledgeDocument:
    with open(path,"r",encoding='utf-8') as file:
        content=file.read()
    metadata, body = parse_frontmatter(content)
    return KnowledgeDocument(source=path.name,text=body,metadata=metadata)

def parse_frontmatter(text: str) -> tuple[dict, str]:
    lines=text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {},text
    closing_index=None
    
    for i in range(1,len(lines)):
        if lines[i].strip()=='---':
            closing_index=i
            break
    if closing_index is None:
            raise ValueError('unclosed_front matter')
    metadata_text='\n'.join(lines[:closing_index])
    body = "\n".join(lines[closing_index + 1:]).strip()
    metadata = yaml.safe_load(metadata_text) or {}

    return metadata, body
    

def load_documents(
    knowledge_dir: str | Path,
) -> list[KnowledgeDocument]:
    documents=[]
    knowledge_dir=Path(knowledge_dir)
    for path in knowledge_dir.glob("*.md"):
        document=load_document(path)
        documents.append(document)
    return documents



def chunk_documents(
    documents: list[KnowledgeDocument],
    chunk_size: int = 500,
    overlap: int = 100,
) -> list[DocumentChunk]:
     all_chunks=[]
     for document in documents:
         chunks=chunk_document(document,chunk_size,overlap)
         all_chunks.extend(chunks)
     return all_chunks
    


def chunk_document(
    document: KnowledgeDocument,
    chunk_size: int = 500,
    overlap: int = 100,
) -> list[DocumentChunk]:

    if overlap >= chunk_size:
        raise ValueError("chunk_size should be bigger than overlap")

    metadata = document.metadata
    source = document.source
    body = document.text

    chunks = []
    step = chunk_size - overlap

    i = 0
    chunk_number = 1

    while i < len(body):
        chunk = body[i:i + chunk_size]

        chunk_id = f"{source}_chunk_{chunk_number}"

        chunk_doc = DocumentChunk(
            metadata=metadata,
            text=chunk,
            source=source,
            chunk_id=chunk_id,
        )

        chunks.append(chunk_doc)

        i += step
        chunk_number += 1

    return chunks


def filter_chunks(
    chunks: list[DocumentChunk],
    filters: dict | None = None,
) -> list[DocumentChunk]:

    if not filters:
        return chunks

    return [
        chunk
        for chunk in chunks
        if all(
            chunk.metadata.get(key) == value
            for key, value in filters.items()
        )
    ]


def build_sparse_index(
    chunks: list[DocumentChunk],
):
    if not chunks:
        raise ValueError("chunks cannot be empty")

    tool = TfidfVectorizer()

    texts = [chunk.text for chunk in chunks]
    document_vectors=tool.fit_transform(texts)
    return tool,document_vectors


def build_dense_index(
    chunks: list[DocumentChunk],
    embedding_function,
):
    if not chunks:
            raise ValueError("chunks cannot be empty")

    texts = [chunk.text for chunk in chunks]
    document_vectors=embedding_function(texts)
    return document_vectors


def retrieve_dense(
    query: str,
    chunks: list[DocumentChunk],
    document_embeddings,
    embedding_function,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    query_embedding=embedding_function([query])
    scores = cosine_similarity(query_embedding, document_embeddings)
    indices=scores.argsort(reverse=True)
    top_k=min(top_k,len(document_embeddings))
    return [RetrievedChunk(score=scores[indices[i]],chunk=chunks[indices[i]]) for i in range(top_k)]



def reciprocal_rank_fusion(
    result_lists: list[list[RetrievedChunk]],
    k: int = 60,
) -> list[RetrievedChunk]:
    ...

def hybrid_retrieve(
    query: str,
    ...,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    ...


def rerank(
    query: str,
    candidates: list[RetrievedChunk],
    top_k: int = 3,
) -> list[RetrievedChunk]:
    ...



def build_context(
    retrieved_chunks: list[RetrievedChunk],
) -> str:
    ...

def build_rag_input(
    question: str,
    context: str,
) -> list[dict]:
    ...

def answer_with_rag(
    question: str,
    top_k: int = 3,
) -> str:
    ...