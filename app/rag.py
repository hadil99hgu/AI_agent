from app.rag_model import KnowledgeDocument,DocumentChunk,RetrievedChunk
from pathlib import Path
import yaml
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.llm import get_llm_client
from app.rag_model import RAGState
import json
from sentence_transformers import SentenceTransformer, CrossEncoder
embedding_model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
reranker_model = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L6-v2"
)

def initialize_rag(
    knowledge_dir: str | Path,
)-> RAGState:
    documents=load_documents(knowledge_dir)
    chunks=chunk_documents(documents)
    vectorizer,sparse_vectors = build_sparse_index(chunks)
    document_embeddings= build_dense_index(chunks,embedding_function=embedding_function)
    return (
    chunks,
    vectorizer,
    sparse_vectors,
    document_embeddings,
)


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


def embedding_function(texts: list[str]):
    if not texts:
        raise ValueError("texts cannot be empty")

    embeddings = embedding_model.encode(
        texts,normalize_embeddings=True
    )

    return embeddings

    
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


def retrieve_sparse(
        query: str,
        chunks: list[DocumentChunk],
        document_vectors,
         vectorizer: TfidfVectorizer,
        top_k: int = 5,
        ) ->list[RetrievedChunk]:
        
        query_vector=vectorizer.trasform(query)
        scores = cosine_similarity(query_vector, document_vectors)[0]
        indices=scores.argsort()[::-1]
        top_k=min(top_k,len(chunks))
        return [RetrievedChunk(score=float(scores[indices[i]]),
                               chunk=chunks[indices[i]]) for i in range(top_k)]

def retrieve_dense(
    query: str,
    chunks: list[DocumentChunk],
    document_embeddings,
    embedding_function,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    query_embedding=embedding_function([query])
    scores = cosine_similarity(query_embedding, document_embeddings)
    indices=scores.argsort()[::-1]
    top_k=min(top_k,len(document_embeddings))
    return [RetrievedChunk(score=float(scores[indices[i]]),chunk=chunks[indices[i]]) for i in range(top_k)]



def reciprocal_rank_fusion(
    result_lists: list[list[RetrievedChunk]],
    k: int = 60,
) -> list[RetrievedChunk]:
    all_chunks=[]
    scores=[]
    all_chunks_id=[]
    for ranking in result_lists:
        for rank,RetChunk in enumerate(ranking,start=1):
            chunk=RetChunk.chunk
            chunk_id=chunk.id
            if chunk_id in all_chunks_id:
                ind_chunk=all_chunks_id.index(chunk_id)
                scores[ind_chunk]+=1/(k+rank)      
            else:
                all_chunks.append(chunk)
                scores.append(1/(rank+k))

    results=[RetrievedChunk(chunk=all_chunks[i],score=scores[i]) for i in range(len(all_chunks))]
    results.sort(key=lambda x:x.score,reverse=True)
    return results


def hybrid_retrieve(
    query: str,
    chunks: list[DocumentChunk],
    vectorizer,
    sparse_vectors,
    document_embeddings,
    embedding_function,
    top_k: int = 5,
) -> list[RetrievedChunk]:

    candidate_k = min(len(chunks), max(10, 2 * top_k))

    sparse_results=retrieve_sparse(query,chunks,sparse_vectors,
                                vectorizer,candidate_k)
   
    dense_results=retrieve_dense(query,chunks,document_embeddings,
                                  embedding_function,candidate_k)
    
    fused_results = reciprocal_rank_fusion(
        [sparse_results, dense_results]
    )

    return fused_results[:top_k]
#https://medium.com/@devalshah1619/mathematical-intuition-behind-reciprocal-rank-fusion-rrf-explained-in-2-mins-002df0cc5e2a


def reranker_function(
    pairs: list[tuple[str, str]],
):
    if not pairs:
        raise ValueError("pairs cannot be empty")

    scores = reranker_model.predict(
        pairs
    )

    return scores

def rerank(
    query: str,
    candidates: list[RetrievedChunk],
    reranker_function,
    top_k: int = 3,
) -> list[RetrievedChunk]:

    if not candidates:
        return []

    pairs = [
        (query, candidate.chunk.text)
        for candidate in candidates
    ]
   
    scores = reranker_function(pairs)
    if len(scores) != len(candidates):
        raise ValueError("Reranker must return one score per candidate")

    indices = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True,
    )
    # return top_k
    top_k = min(top_k, len(candidates))

    results = [RetrievedChunk(score=scores[i],chunk=candidates[i].chunk) for i in indices[:top_k]]
    return results

def build_context(
    retrieved_chunks: list[RetrievedChunk],
) -> str:
    if not retrieved_chunks:
        return ""
    context_parts=[]
    for result in retrieved_chunks:
        chunk = result.chunk
        context_parts.append(
            f"[SOURCE: {chunk.source} | CHUNK: {chunk.chunk_id}]\n{chunk.text}"
        )
    return '\n\n'.join(context_parts)

def build_rag_input(
    question: str,
    context: str,
) -> list[dict]:

    system_prompt = {
        "role": "system",
        "content": ('do not invent facts\n'
            'answer the question only using the relevant information from the context text.\n'
            "f you don't find any relevant information then say no.\n"
            'cite sources using the source labels\n'

        )}
    user_prompt = {
        "role": "user",
        "content": (
            f'context :\n {context} \n\n'
            f'question :\n {question}'
            )}

    return [system_prompt, user_prompt]

def generate_rag_answer(
    question: str,
    context: str,
) -> str:

    messages = build_rag_input(question, context)

    client = get_llm_client()

    response = client.responses.create(
        model="google/gemma-4-26b-a4b-it:free",
        input=messages,
    )
    return response.output_text 


# search_knowledge_base()
# → returns evidence/chunks
# answer_with_rag()
# → takes evidence and asks the LLM to write the answer

def search_knowledge_base(
    question: str,
    rag_state: RAGState,
    top_k: int = 3,
) -> list[RetrievedChunk]:

    candidate_k = max(10, 3 * top_k)

    candidates = hybrid_retrieve(
        query=question,
        chunks=rag_state.chunks,
        vectorizer=rag_state.vectorizer,
        sparse_vectors=rag_state.sparse_vectors,
        document_embeddings=rag_state.document_embeddings,
        embedding_function=embedding_function,
        top_k=candidate_k,
    )

    best_chunks = rerank(
        query=question,
        candidates=candidates,
        reranker_function=reranker_function,
        top_k=top_k,
    )

    return best_chunks

def answer_with_rag(
    question: str,
    rag_state: RAGState,
    top_k: int = 3,
) -> str:
    best_chunks = search_knowledge_base(question,
                       rag_state,top_k=top_k,)

    context = build_context(best_chunks)
    answer = generate_rag_answer(
        question,context)

    return answer


#########################
#######EVALUATION#######

def load_eval_cases(
    path: str | Path,
) -> list[dict]:

    path = Path(path)

    with open(path, "r", encoding="utf-8") as file:
        eval_cases = json.load(file)

    return eval_cases


def evaluate_retrieval(
    eval_cases: list[dict],
    rag_state: RAGState,
    top_k: int = 3,
) -> dict:

    case_results = []

    for case in eval_cases:
        question = case["question"]
        expected_sources = case["expected_sources"]

        results = search_knowledge_base(
            question,
            rag_state,
            top_k=top_k,
        )

        retrieved_sources = [
            result.chunk.source
            for result in results
        ]

        hit = any(
            source in retrieved_sources
            for source in expected_sources
        )

        retrieved_expected = sum(
            1
            for source in expected_sources
            if source in retrieved_sources
        )

        recall = (
            retrieved_expected / len(expected_sources)
            if expected_sources
            else 0.0
        )

        case_results.append({
            "question": question,
            "expected_sources": expected_sources,
            "retrieved_sources": retrieved_sources,
            "hit": hit,
            "recall": recall,
        })

    hit_rate = (
        sum(case["hit"] for case in case_results)
        / len(case_results)
        if case_results
        else 0.0
    )

    mean_recall = (
        sum(case["recall"] for case in case_results)
        / len(case_results)
        if case_results
        else 0.0
    )

    return {
        "hit_rate_at_k": hit_rate,
        "mean_recall_at_k": mean_recall,
        "cases": case_results,
    }

# Hit@k
# → did we retrieve at least one expected source?

# Recall@k
# → what fraction of all expected sources did we retrieve?

def search_knowledge_tool(
    query: str,
    rag_state: RAGState,
    top_k: int = 3,
) -> dict:

    results = search_knowledge_base(
        question=query,
        rag_state=rag_state,
        top_k=top_k,
    )

    formatted_results = [
        {
            "source": result.chunk.source,
            "chunk_id": result.chunk.chunk_id,
            "text": result.chunk.text,
            "score": float(result.score),
        }
        for result in results
    ]

    return {
        "success": True,
        "results": formatted_results,
    }


if __name__ == "__main__":
    texts = [
        "Can I use my phone abroad?",
        "Premium includes roaming in Europe.",
    ]

    embeddings = embedding_function(texts)

    print(type(embeddings))
    print(embeddings.shape)
    print(embeddings[0][:10])

