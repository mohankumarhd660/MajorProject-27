from models.chat import ChatMessage
from models.dataset import DatasetEntry
from utils.db import get_db_session
from services.groq_client import groq_chat


def _save_chat(db, user_id: int, thread_id: str, role: str, content: str, source: str):
    db.add(
        ChatMessage(
            user_id=user_id,
            thread_id=thread_id,
            role=role,
            content=content,
            source=source,
        )
    )


def _format_paragraphs(text: str) -> str:
    """Ensure text has proper paragraph formatting."""
    if not text:
        return text
    import re
    text = str(text)
    text = text.replace("**", "").replace("*", "")
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)

    # Add line breaks after sentences if they're too long
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if len(sentences) > 1:
        # Group sentences into logical paragraphs (3-4 sentences each)
        paragraphs = []
        current_para = []
        for i, sent in enumerate(sentences):
            current_para.append(sent)
            if len(current_para) >= 3 or i == len(sentences) - 1:
                paragraphs.append(' '.join(current_para))
                current_para = []
        return re.sub(r"\n{3,}", "\n\n", '\n\n'.join(paragraphs)).strip()
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def answer_query(user_id: int, thread_id: str, query: str) -> dict:
    db = get_db_session()

    _save_chat(db, user_id, thread_id, "user", query, "ai")

    # Retrieve context from FAISS
    from faiss_engine.indexer import search
    results = search(query, k=1)
    context_entries = []
    for r in results:
        entry = db.query(DatasetEntry).filter(DatasetEntry.id == r["id"]).first()
        if entry:
            if entry.question and entry.answer:
                context_entries.append(f"Q: {entry.question}\nA: {entry.answer}")
            elif entry.raw_text:
                context_entries.append(entry.raw_text)
    
    context_str = "\n\n".join(context_entries)[:1000]
    
    if context_str:
        prompt = f"Context information is below.\n---------------------\n{context_str}\n---------------------\nGiven the context information and no prior knowledge, answer the user's query: {query}"
    else:
        prompt = query

    content = groq_chat(prompt)
    content = _format_paragraphs(content)
    _save_chat(db, user_id, thread_id, "assistant", content, "ai")

    # Optional storage only (for history/analytics), never used for retrieval.
    db.add(
        DatasetEntry(
            source_file="self_learning.json",
            entry_type="qa",
            question=query,
            answer=content,
        )
    )

    db.commit()
    return {"reply": content, "source": "ai", "thread_id": thread_id, "score": None}
