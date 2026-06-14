"""ChromaDB vector store for university document chunks."""

import logging
import uuid
from pathlib import Path

import chromadb
from chromadb.config import Settings

from rag.embeddings import embed_texts

logger = logging.getLogger(__name__)

COLLECTION_NAME = "pakistan_universities"
CHROMA_PATH = Path(__file__).resolve().parent.parent / "data" / "chroma_db"


def init_vectorstore():
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(
        path=str(CHROMA_PATH),
        settings=Settings(anonymized_telemetry=False),
    )
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


def add_documents(collection, docs: list[dict]) -> int:
    if not docs:
        return 0

    texts = [doc["text"] for doc in docs]
    embeddings = embed_texts(texts)

    ids = [str(uuid.uuid4()) for _ in docs]
    metadatas = [
        {
            "university": doc["university"],
            "url": doc.get("url", ""),
            "page_type": doc.get("page_type", "general"),
        }
        for doc in docs
    ]

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    return len(docs)


def query(collection, question: str, university: str, top_k: int = 5) -> list[dict]:
    results = collection.query(
        query_embeddings=[embed_texts([question])[0]],
        n_results=top_k,
        where={"university": university},
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    for doc_text, metadata in zip(documents, metadatas):
        chunks.append(
            {
                "text": doc_text,
                "url": metadata.get("url", ""),
                "page_type": metadata.get("page_type", ""),
            }
        )

    return chunks


def get_document_count(collection) -> int:
    return collection.count()


def clear_collection(collection) -> None:
    existing = collection.get(include=[])
    if existing["ids"]:
        collection.delete(ids=existing["ids"])
    logger.info("Cleared existing documents from vector store")
