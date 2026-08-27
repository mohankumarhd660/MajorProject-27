import csv
import json
import os
from pathlib import Path

from models.dataset import DatasetEntry
from models.coding import CodingProblem
from utils.db import get_db_session

DATASET_ROOT = Path(__file__).resolve().parents[1] / "Dataset"


def _upsert_dataset_entry(db, entry: DatasetEntry):
    existing = (
        db.query(DatasetEntry)
        .filter(DatasetEntry.source_file == entry.source_file)
        .filter((DatasetEntry.question == entry.question) | (DatasetEntry.raw_text == entry.raw_text))
        .first()
    )
    if existing:
        return existing
    db.add(entry)
    return entry


def load_dataset_into_db() -> dict:
    db = get_db_session()

    if not DATASET_ROOT.exists():
        raise RuntimeError(f"Dataset folder not found: {DATASET_ROOT}")

    loaded_entries = 0
    loaded_problems = 0

    for file_path in DATASET_ROOT.rglob("*"):
        if not file_path.is_file():
            continue

        suffix = file_path.suffix.lower()
        rel = str(file_path.relative_to(DATASET_ROOT))

        if suffix == ".json":
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
            except Exception:
                continue

            if isinstance(data, dict) and "intents" in data and isinstance(data["intents"], list):
                for intent in data["intents"]:
                    tag = intent.get("tag")
                    patterns = intent.get("patterns") or []
                    responses = intent.get("responses") or []
                    if not patterns or not responses:
                        continue
                    for p in patterns:
                        entry = DatasetEntry(
                            source_file=rel,
                            entry_type="intent",
                            tag=str(tag) if tag else None,
                            question=str(p),
                            answer=str(responses[0]),
                        )
                        _upsert_dataset_entry(db, entry)
                        loaded_entries += 1

        elif suffix in {".txt"}:
            try:
                txt = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if txt.strip():
                entry = DatasetEntry(source_file=rel, entry_type="text", raw_text=txt.strip())
                _upsert_dataset_entry(db, entry)
                loaded_entries += 1

        elif suffix in {".csv"}:
            try:
                with file_path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
                    reader = csv.DictReader(f)
                    if not reader.fieldnames:
                        continue
                    cols = {c.lower().strip(): c for c in reader.fieldnames if c}

                    qa_ok = {"problem", "solution"}.issubset(set(cols.keys()))
                    problem_col = None
                    code_col = None

                    for cand in ["problem", "question", "prompt"]:
                        if cand in cols:
                            problem_col = cols[cand]
                            break
                    for cand in ["python code", "code", "solution", "answer"]:
                        if cand in cols:
                            code_col = cols[cand]
                            break

                    for row in reader:
                        if qa_ok:
                            problem = (row.get(cols["problem"]) or "").strip()
                            solution = (row.get(cols["solution"]) or "").strip()
                            if problem and solution:
                                entry = DatasetEntry(
                                    source_file=rel,
                                    entry_type="qa",
                                    question=problem[:2000],
                                    answer=solution[:8000],
                                )
                                _upsert_dataset_entry(db, entry)
                                loaded_entries += 1

                        if problem_col and code_col:
                            title = (row.get(problem_col) or "").strip()
                            code = (row.get(code_col) or "").strip()
                            if not title or not code:
                                continue

                            existing = db.query(CodingProblem).filter(CodingProblem.title == title[:200]).first()
                            if existing:
                                continue

                            tests = {"cases": []}
                            starter = "".join(code.splitlines(True)[:40])
                            db.add(
                                CodingProblem(
                                    title=title[:200],
                                    difficulty="medium",
                                    description=title,
                                    starter_code=starter or "def solve():\n    pass\n",
                                    tests_json=json.dumps(tests),
                                    source_file=rel,
                                )
                            )
                            loaded_problems += 1
            except Exception:
                continue

    db.commit()

    return {"dataset_entries": loaded_entries, "coding_problems": loaded_problems, "dataset_root": str(DATASET_ROOT)}
