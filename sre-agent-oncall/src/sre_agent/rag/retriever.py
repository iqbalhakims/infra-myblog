"""Hybrid retriever: BM25 keyword + Chroma semantic, results fused."""

import logging
from typing import List

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from rank_bm25 import BM25Okapi

from sre_agent.config import settings

log = logging.getLogger(__name__)

COLLECTION = "runbooks"
EMBED_MODEL = "all-MiniLM-L6-v2"
TOP_K = 5


def _get_collection() -> chromadb.Collection:
    client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    ef = SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
    return client.get_or_create_collection(COLLECTION, embedding_function=ef)


def _semantic_search(collection: chromadb.Collection, query: str, k: int) -> List[str]:
    results = collection.query(query_texts=[query], n_results=k)
    return results["documents"][0] if results["documents"] else []


def _bm25_search(collection: chromadb.Collection, query: str, k: int) -> List[str]:
    all_docs = collection.get()["documents"]
    if not all_docs:
        return []
    tokenized = [doc.lower().split() for doc in all_docs]
    bm25 = BM25Okapi(tokenized)
    scores = bm25.get_scores(query.lower().split())
    ranked = sorted(zip(scores, all_docs), key=lambda x: x[0], reverse=True)
    return [doc for _, doc in ranked[:k] if _ > 0]


def retrieve(query: str, k: int = TOP_K) -> str:
    """
    Hybrid search: merge semantic + BM25 results, deduplicate, return top-k.
    """
    try:
        collection = _get_collection()
        semantic = _semantic_search(collection, query, k)
        keyword = _bm25_search(collection, query, k)

        # Deduplicate preserving order — semantic results ranked first
        seen: set[str] = set()
        merged: List[str] = []
        for doc in semantic + keyword:
            if doc not in seen:
                seen.add(doc)
                merged.append(doc)

        top = merged[:k]
        if not top:
            return "No relevant runbook found."
        return "\n\n---\n\n".join(top)
    except Exception as exc:
        log.warning("RAG retrieval failed: %s", exc)
        return f"RAG unavailable: {exc}"
