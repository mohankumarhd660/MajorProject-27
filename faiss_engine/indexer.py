import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from models.dataset import DatasetEntry
from utils.db import get_db_session

INDEX_DIR = Path(__file__).resolve().parents[1] / "faiss_engine" / "store"
INDEX_DIR.mkdir(parents=True, exist_ok=True)
INDEX_PATH = INDEX_DIR / "dataset.index"
META_PATH = INDEX_DIR / "meta.json"

_model = None

def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def build_or_load_index(force_rebuild: bool = False):
    if INDEX_PATH.exists() and META_PATH.exists() and not force_rebuild:
        index = faiss.read_index(str(INDEX_PATH))
        meta = json.loads(META_PATH.read_text(encoding="utf-8"))
        return index, meta

    db = get_db_session()
    entries = db.query(DatasetEntry).all()

    texts = []
    ids = []
    for e in entries:
        payload = None
        if e.question and e.answer:
            payload = f"Q: {e.question}\nA: {e.answer}"
        elif e.raw_text:
            payload = e.raw_text

        if not payload or not payload.strip():
            continue
        texts.append(payload[:4000])
        ids.append(e.id)

    model = get_embedding_model()
    dim = model.get_sentence_embedding_dimension()

    if not texts:
        index = faiss.IndexFlatIP(dim)
        meta = {"ids": [], "dim": dim}
        faiss.write_index(index, str(INDEX_PATH))
        META_PATH.write_text(json.dumps(meta), encoding="utf-8")
        return index, meta

    # Compute dense embeddings
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    meta = {"ids": ids, "dim": dim, "model": "all-MiniLM-L6-v2", "num_docs": len(texts)}
    faiss.write_index(index, str(INDEX_PATH))
    META_PATH.write_text(json.dumps(meta), encoding="utf-8")

    return index, meta


def search(query: str, k: int = 5):
    index, meta = build_or_load_index(force_rebuild=False)
    ids = meta.get("ids") or []

    if not ids:
        return []

    model = get_embedding_model()
    q_emb = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)

    scores, idxs = index.search(q_emb, k)
    results = []
    for score, idx in zip(scores[0], idxs[0]):
        if idx == -1:
            continue
        entry_id = ids[idx]
        results.append({"id": entry_id, "score": float(score)})
    
    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    return results
