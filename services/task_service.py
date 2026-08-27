from models.task import Task
from models.dataset import DatasetEntry
from models.coding import CodingProblem
from services.dataset_loader import load_dataset_into_db
from utils.db import get_db_session


def ensure_tasks_seeded():
    db = get_db_session()
    if db.query(Task).count() > 0:
        return

    load_dataset_into_db()

    intents = (
        db.query(DatasetEntry)
        .filter(DatasetEntry.entry_type == "intent")
        .order_by(DatasetEntry.id.asc())
        .limit(12)
        .all()
    )
    for e in intents:
        db.add(
            Task(
                title=e.question[:180] if e.question else "Learning",
                subject="CS",
                difficulty="easy",
                task_type="quiz",
                status="pending",
            )
        )

    problems = db.query(CodingProblem).order_by(CodingProblem.id.asc()).limit(12).all()
    for p in problems:
        db.add(
            Task(
                title=p.title[:180],
                subject="DSA",
                difficulty=p.difficulty,
                task_type="coding",
                status="pending",
            )
        )

    texts = (
        db.query(DatasetEntry)
        .filter(DatasetEntry.entry_type.in_(["qa", "text"]))
        .order_by(DatasetEntry.id.asc())
        .limit(6)
        .all()
    )
    for e in texts:
        title = e.question or (e.raw_text[:120] if e.raw_text else "Learning")
        db.add(Task(title=title[:180], subject="General", difficulty="easy", task_type="learning", status="pending"))

    db.commit()


def get_tasks():
    ensure_tasks_seeded()
    db = get_db_session()
    return db.query(Task).order_by(Task.id.desc()).all()
