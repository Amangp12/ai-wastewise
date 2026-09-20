import os
import glob
import json
from pathlib import Path

from dotenv import load_dotenv
from google import genai
import chromadb

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found. Copy .env.example to .env and paste your key in.")

client = genai.Client(api_key=API_KEY)

EMBEDDING_MODEL = "gemini-embedding-001"
KNOWLEDGE_BASE_DIR = "knowledge_base"
CHROMA_DB_DIR = "chroma_store"
COLLECTION_NAME = "waste_management_kb"

# Chunking parameters, in characters (simple and predictable; good enough
# for a knowledge base of a handful of documents).
TARGET_CHUNK_SIZE = 800
CHUNK_OVERLAP = 150


def chunk_text(text: str, source_name: str) -> list[dict]:
    """Split one document's text into overlapping chunks.
    Returns a list of {"text": ..., "source": ...} dicts.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) <= TARGET_CHUNK_SIZE:
            current_chunk += ("\n\n" if current_chunk else "") + para
        else:
            if current_chunk:
                chunks.append(current_chunk)
            # Start the next chunk with a small overlap from the end of
            # the previous one, so context isn't lost at the boundary.
            overlap_text = current_chunk[-CHUNK_OVERLAP:] if current_chunk else ""
            current_chunk = (overlap_text + "\n\n" + para) if overlap_text else para

    if current_chunk:
        chunks.append(current_chunk)

    return [{"text": c, "source": source_name} for c in chunks]


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts using Gemini's embedding model."""
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=texts,
    )
    return [e.values for e in result.embeddings]


def ingest():
    doc_paths = sorted(glob.glob(os.path.join(KNOWLEDGE_BASE_DIR, "*.txt")))
    if not doc_paths:
        raise RuntimeError(
            f"No .txt files found in {KNOWLEDGE_BASE_DIR}/. Add your source documents there first."
        )

    all_chunks = []
    for path in doc_paths:
        source_name = Path(path).name
        text = Path(path).read_text(encoding="utf-8")
        doc_chunks = chunk_text(text, source_name)
        all_chunks.extend(doc_chunks)
        print(f"  {source_name}: {len(doc_chunks)} chunks")

    print(f"Total chunks across all documents: {len(all_chunks)}")

    print("Embedding chunks (this calls the Gemini API)...")
    texts = [c["text"] for c in all_chunks]
    embeddings = embed_texts(texts)

    print("Storing in Chroma vector database...")
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    # Recreate the collection fresh each time we ingest, so re-running
    # this script after editing source documents doesn't leave stale
    # chunks behind.
    try:
        chroma_client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = chroma_client.create_collection(COLLECTION_NAME)

    collection.add(
        ids=[f"chunk_{i}" for i in range(len(all_chunks))],
        embeddings=embeddings,
        documents=texts,
        metadatas=[{"source": c["source"]} for c in all_chunks],
    )

    print(f"Done. {len(all_chunks)} chunks stored in {CHROMA_DB_DIR}/")


if __name__ == "__main__":
    ingest()
