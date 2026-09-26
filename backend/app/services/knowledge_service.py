import hashlib
import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
KB_PATH = BASE_DIR / "data" / "knowledge_base.json"

try:
    import chromadb
except ImportError:
    chromadb = None

_collection = None


class DeterministicEmbeddingFunction:
    """Tiny offline embedding function so the prototype never needs model downloads."""

    def __call__(self, input):
        vectors = []
        for text in input:
            vector = [0.0] * 64
            for token in text.lower().split():
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                index = int.from_bytes(digest[:2], "big") % len(vector)
                vector[index] += 1.0
            norm = sum(x * x for x in vector) ** 0.5 or 1.0
            vectors.append([x / norm for x in vector])
        return vectors

    def name(self):
        return "orca-deterministic-64"


def _load_documents():
    try:
        return json.loads(KB_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def _collection_or_none():
    global _collection
    if _collection is not None:
        return _collection
    if chromadb is None:
        return None
    try:
        client = chromadb.PersistentClient(path=os.getenv("CHROMA_PATH", str(BASE_DIR / "data" / "chroma")))
        _collection = client.get_or_create_collection(
            name="orca_marine_knowledge",
            embedding_function=DeterministicEmbeddingFunction(),
            metadata={"description": "ORCA source and product knowledge"},
        )
        documents = _load_documents()
        if documents and _collection.count() == 0:
            _collection.add(
                ids=[d["id"] for d in documents],
                documents=[d["text"] for d in documents],
                metadatas=[{"source": d["source"], "type": d["type"]} for d in documents],
            )
        return _collection
    except Exception:
        return None


def search_knowledge(query: str, limit: int = 5):
    query = (query or "").strip()
    if not query:
        return []

    collection = _collection_or_none()
    if collection is not None:
        try:
            result = collection.query(query_texts=[query], n_results=max(1, min(limit, 10)))
            ids = (result.get("ids") or [[]])[0]
            docs = (result.get("documents") or [[]])[0]
            metas = (result.get("metadatas") or [[]])[0]
            return [
                {"id": item_id, "text": doc, "source": (meta or {}).get("source"),
                 "type": (meta or {}).get("type"), "mode": "chroma"}
                for item_id, doc, meta in zip(ids, docs, metas)
            ]
        except Exception:
            pass

    tokens = {token for token in query.lower().split() if len(token) > 2}
    scored = []
    for item in _load_documents():
        haystack = f"{item.get('text', '')} {item.get('source', '')}".lower()
        score = sum(1 for token in tokens if token in haystack)
        if score:
            scored.append((score, item))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [{**item, "mode": "lexical_fallback", "score": score} for score, item in scored[:limit]]


def knowledge_status():
    documents = _load_documents()
    return {
        "provider": "ChromaDB",
        "configured": chromadb is not None,
        "documents": len(documents),
        "mode": "chroma" if chromadb is not None else "lexical_fallback",
        "embedding": "deterministic_offline",
        "path": os.getenv("CHROMA_PATH", str(BASE_DIR / "data" / "chroma")),
    }
