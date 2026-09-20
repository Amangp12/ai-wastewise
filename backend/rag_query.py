import os
import json

from dotenv import load_dotenv
from google import genai
import chromadb

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY not found. Copy .env.example to .env and paste your key in.")

client = genai.Client(api_key=API_KEY)

EMBEDDING_MODEL = "gemini-embedding-001"
GENERATION_MODEL = "gemini-3.6-flash"
CHROMA_DB_DIR = "chroma_store"
COLLECTION_NAME = "waste_management_kb"
TOP_K = 4  # how many chunks to retrieve per query


def retrieve(query: str, top_k: int = TOP_K) -> list[dict]:
    """Embed the query and fetch the top_k most relevant chunks from Chroma."""
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    collection = chroma_client.get_collection(COLLECTION_NAME)

    query_embedding = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=[query],
    ).embeddings[0].values

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )

    chunks = []
    for text, metadata in zip(results["documents"][0], results["metadatas"][0]):
        chunks.append({"text": text, "source": metadata["source"]})
    return chunks


GENERATION_PROMPT_TEMPLATE = """You are helping a user understand how to dispose of a waste item.

Item: {object_name}
Material: {material}
Waste category: {category}

Below are the ONLY facts you are allowed to use. Do not add any disposal
information from your own general knowledge -- only use what is in these
retrieved passages. If the passages don't fully answer the question, say
so honestly in your explanation rather than filling the gap with unsourced
information.

--- RETRIEVED PASSAGES ---
{retrieved_context}
--- END OF RETRIEVED PASSAGES ---

Respond with ONLY a JSON object (no markdown fences) with exactly these
fields:

{{
  "recommended_action": "<a short, clear, practical instruction for what the user should actually do with this item>",
  "explanation": "<why this is the right approach, grounded in the retrieved passages>",
  "sustainability_impact": "<a brief note on why disposing of this correctly matters environmentally, grounded in the retrieved passages>",
  "grounded_in_sources": true or false,
  "coverage_note": "<if the retrieved passages don't fully cover this item/category, say so plainly here; otherwise empty string>"
}}

Set "grounded_in_sources" to false if the retrieved passages don't
actually contain relevant disposal guidance for this item -- do not force
an answer that isn't supported by the passages.
"""


def generate_recommendation(object_name: str, material: str, category: str) -> dict:
    """Full Phase 7 pipeline: retrieve relevant chunks, then generate a
    grounded recommendation using only those chunks.
    """
    query = f"how to dispose of {material} {object_name}, category {category}"
    retrieved_chunks = retrieve(query)

    if not retrieved_chunks:
        return {
            "recommended_action": "",
            "explanation": "",
            "sustainability_impact": "",
            "grounded_in_sources": False,
            "coverage_note": "No relevant information found in the knowledge base for this item.",
            "sources": [],
        }

    context_text = "\n\n---\n\n".join(
        f"[Source: {c['source']}]\n{c['text']}" for c in retrieved_chunks
    )

    prompt = GENERATION_PROMPT_TEMPLATE.format(
        object_name=object_name,
        material=material,
        category=category,
        retrieved_context=context_text,
    )

    response = client.models.generate_content(
        model=GENERATION_MODEL,
        contents=[prompt],
    )

    raw_text = response.text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Model did not return valid JSON. Raw response:\n{raw_text}") from e

    # Attach which sources were actually retrieved, so the user can see
    # exactly where the recommendation came from -- this is the
    # "show source/reference" requirement from the project brief.
    result["sources"] = sorted(set(c["source"] for c in retrieved_chunks))
    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Usage: python rag_query.py <object_name> <material> <category>")
        print('Example: python rag_query.py "plastic water bottle" plastic "Recyclable/Dry Waste"')
        sys.exit(1)

    result = generate_recommendation(sys.argv[1], sys.argv[2], sys.argv[3])
    print(json.dumps(result, indent=2))
