# AI_agent

main.py : API / input point
models.py : data models
crm.py : mock system of client relationship management
agent.py : agent logic
test_main.py : tests



offline ingestion
-----------------

documents
   ↓
chunk_documents()
   ↓
chunks + metadata
   ↓
build sparse index
build dense index

online query
------------

question
   ↓
retrieve_sparse()
retrieve_dense()
   ↓
rank fusion
   ↓
rerank()
   ↓
top-k chunks
   ↓
build_context()
   ↓
LLM
   ↓
answer + sources
