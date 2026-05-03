import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict

_embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
_client = chromadb.PersistentClient(path="./chroma_db")


def _collection_name(doc_id: str) -> str:
    # ChromaDB collection names must be 3-63 chars, alphanumeric + hyphens
    safe = "".join(c if c.isalnum() else "-" for c in doc_id)
    return f"doc-{safe}"[:63]


def store_chunks(doc_id: str, doc_name: str, chunks: List[Dict]) -> None:
    collection = _client.get_or_create_collection(
        _collection_name(doc_id), embedding_function=_embedding_fn
    )
    ids = [f"{doc_id}_chunk_{c['chunk_index']}" for c in chunks]
    documents = [c["text"] for c in chunks]
    metadatas = [
        {
            "doc_id": doc_id,
            "doc_name": doc_name,
            "page": c["page"],
            "chunk_index": c["chunk_index"],
        }
        for c in chunks
    ]
    collection.add(ids=ids, documents=documents, metadatas=metadatas)


def query_chunks(doc_id: str, question: str, n_results: int = 5) -> List[Dict]:
    collection = _client.get_or_create_collection(
        _collection_name(doc_id), embedding_function=_embedding_fn
    )
    count = collection.count()
    if count == 0:
        return []
    results = collection.query(
        query_texts=[question], n_results=min(n_results, count)
    )
    return [
        {
            "text": doc,
            "page": meta["page"],
            "chunk_index": meta["chunk_index"],
            "doc_name": meta["doc_name"],
            "relevance_score": round(1 - dist, 4),
        }
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ]


def delete_document(doc_id: str) -> None:
    try:
        _client.delete_collection(_collection_name(doc_id))
    except Exception:
        pass


def list_chunks_count(doc_id: str) -> int:
    try:
        return _client.get_collection(
            _collection_name(doc_id), embedding_function=_embedding_fn
        ).count()
    except Exception:
        return 0
