from sqlalchemy import func

from models.quiz import TopicPerformance, QuizAttempt
from models.coding import Submission, CodingProblem
from models.task import Task
from utils.db import get_db_session
from services.quiz_service import _detect_subject, SUBJECT_TOPICS


def _band(accuracy: float) -> str:
    if accuracy >= 0.75:
        return "strong"
    if accuracy >= 0.40:
        return "medium"
    return "weak"


def get_student_dashboard_metrics(user_id: int) -> dict:
    db = get_db_session()

    # Get all topic performance data
    topic_rows = db.query(TopicPerformance).filter(TopicPerformance.user_id == user_id).all()
    total_correct = sum(r.correct for r in topic_rows)
    total_total = sum(r.total for r in topic_rows)

    accuracy = (total_correct / total_total) if total_total else 0.0

    by_subject = {}
    by_topic = []
    
    # Categorize topics by performance band
    strong_topics = []
    medium_topics = []
    weak_topics = []
    
    for r in topic_rows:
        # Detect proper subject for legacy data (e.g. "CS" -> real subject)
        proper_subject = _detect_subject(r.topic) if r.subject in ("CS", "General", "") else r.subject
        
        if proper_subject not in by_subject:
            by_subject[proper_subject] = {"correct": 0, "total": 0, "quizzes": 0}
        by_subject[proper_subject]["correct"] += r.correct
        by_subject[proper_subject]["total"] += r.total
        by_subject[proper_subject]["quizzes"] += 1  # Count quizzes per subject
        
        topic_acc = (r.correct / r.total) if r.total else 0.0
        by_topic.append({
            "topic": r.topic, 
            "subject": proper_subject,
            "accuracy": topic_acc,
            "correct": r.correct,
            "total": r.total,
            "incorrect": r.total - r.correct,
            "band": _band(topic_acc),
            "quizzes_taken": 1  # Each row represents one quiz attempt on this topic
        })
        
        # Categorize
        if topic_acc >= 0.75:
            strong_topics.append(r.topic)
        elif topic_acc >= 0.40:
            medium_topics.append(r.topic)
        else:
            weak_topics.append(r.topic)

    subject_perf = []
    for subject, agg in by_subject.items():
        subject_acc = (agg["correct"] / agg["total"]) if agg["total"] else 0.0
        subject_perf.append(
            {
                "subject": subject,
                "accuracy": subject_acc,
                "band": _band(subject_acc),
                "quizzes_taken": agg["quizzes"],
                "correct": agg["correct"],
                "total": agg["total"],
                "incorrect": agg["total"] - agg["correct"]
            }
        )

    subject_perf.sort(key=lambda x: x["accuracy"], reverse=True)
    by_topic.sort(key=lambda x: x["accuracy"], reverse=True)

    # Determine strongest subject and weakest topic
    strong_subject = subject_perf[0]["subject"] if subject_perf else "—"
    # Pick the weakest topic from weak topics, or the lowest accuracy topic
    if weak_topics:
        # Get the topic with lowest accuracy from weak topics
        weak_topic_candidates = [t for t in by_topic if t["topic"] in weak_topics]
        weak_topic_candidates.sort(key=lambda x: x["accuracy"])
        weak_topic = weak_topic_candidates[0]["topic"] if weak_topic_candidates else weak_topics[0]
    elif by_topic:
        weak_topic = by_topic[-1]["topic"]
    else:
        weak_topic = "—"

    # Get coding statistics
    submissions = db.query(Submission).filter(Submission.user_id == user_id).all()
    total_coding_attempted = len(submissions)
    completed_coding = len([s for s in submissions if s.status == "accepted"])
    failed_coding = len([s for s in submissions if s.status == "failed"])
    
    # Get unique problems solved
    solved_problem_ids = set(s.problem_id for s in submissions if s.status == "accepted")
    unique_problems_solved = len(solved_problem_ids)
    
    # Get total quiz attempts
    quiz_attempts = db.query(QuizAttempt).filter(QuizAttempt.user_id == user_id).count()

    return {
        "tasks_completed": total_total + completed_coding,
        "accuracy": accuracy,
        "accuracy_band": _band(accuracy),
        "strong_subject": strong_subject,
        "weak_topic": weak_topic,
        "subject_perf": subject_perf,
        "topic_perf": by_topic,
        "strong_topics": strong_topics,
        "medium_topics": medium_topics,
        "weak_topics": weak_topics,
        "has_data": len(topic_rows) > 0,
        # New detailed stats
        "quiz_stats": {
            "total_attempts": quiz_attempts,
            "total_questions_answered": total_total,
            "total_correct": total_correct,
            "total_incorrect": total_total - total_correct,
        },
        "coding_stats": {
            "total_attempted": total_coding_attempted,
            "accepted": completed_coding,
            "failed": failed_coding,
            "unique_solved": unique_problems_solved,
            "success_rate": (completed_coding / total_coding_attempted * 100) if total_coding_attempted > 0 else 0
        }
    }


def get_detailed_topic_analytics(user_id: int) -> dict:
    """Get detailed analytics for each topic with quiz history."""
    db = get_db_session()
    
    # Get all quiz attempts with details
    quiz_attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.user_id == user_id)
        .order_by(QuizAttempt.created_at.desc())
        .all()
    )
    
    # Get topic-wise breakdown
    topic_rows = db.query(TopicPerformance).filter(TopicPerformance.user_id == user_id).all()
    
    topics_detail = []
    for r in topic_rows:
        acc = (r.correct / r.total) if r.total else 0.0
        # Detect proper subject for legacy data
        proper_subject = _detect_subject(r.topic) if r.subject in ("CS", "General", "") else r.subject
        topics_detail.append({
            "topic": r.topic,
            "subject": proper_subject,
            "total_questions": r.total,
            "correct": r.correct,
            "incorrect": r.total - r.correct,
            "accuracy": acc,
            "band": _band(acc),
            "status": "Strong" if acc >= 0.75 else "Medium" if acc >= 0.40 else "Weak"
        })
    
    # Sort by accuracy descending
    topics_detail.sort(key=lambda x: x["accuracy"], reverse=True)
    
    return {
        "topics": topics_detail,
        "total_quizzes": len(quiz_attempts),
        "recent_attempts": [
            {
                "date": a.created_at.strftime("%Y-%m-%d") if a.created_at else "Unknown",
                "score": a.score,
                "total": a.total,
                "accuracy": (a.score / a.total * 100) if a.total else 0
            }
            for a in quiz_attempts[:5]  # Last 5 attempts
        ]
    }
