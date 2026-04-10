"""Load runbooks from markdown files, chunk, embed, and store in Chroma."""

import logging
import os
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from langchain.text_splitter import MarkdownTextSplitter

from sre_agent.config import settings

log = logging.getLogger(__name__)

COLLECTION = "runbooks"
EMBED_MODEL = "all-MiniLM-L6-v2"


def _get_collection() -> chromadb.Collection:
    client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    ef = SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
    return client.get_or_create_collection(COLLECTION, embedding_function=ef)


def ingest_runbooks() -> int:
    """Read all .md files in runbooks_dir, chunk, and upsert into Chroma."""
    collection = _get_collection()
    splitter = MarkdownTextSplitter(chunk_size=512, chunk_overlap=64)
    runbooks_path = Path(settings.runbooks_dir)
    total = 0

    for md_file in runbooks_path.glob("**/*.md"):
        text = md_file.read_text(encoding="utf-8")
        chunks = splitter.split_text(text)
        ids = [f"{md_file.stem}_{i}" for i in range(len(chunks))]
        metadatas = [{"source": str(md_file), "filename": md_file.name}] * len(chunks)
        collection.upsert(documents=chunks, ids=ids, metadatas=metadatas)
        total += len(chunks)
        log.info("Ingested %s → %d chunks", md_file.name, len(chunks))

    log.info("Total chunks ingested: %d", total)
    return total


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ingest_runbooks()
