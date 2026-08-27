from sqlalchemy import func

from models.user import User
from models.quiz import TopicPerformance
from models.coding import Submission
from utils.db import get_db_session


def get_teacher_dashboard() -> dict:
    db = get_db_session()

    students = db.query(User).filter(User.role == "student").order_by(User.username.asc()).all()

    perf = (
        db.query(TopicPerformance.user_id, func.sum(TopicPerformance.correct), func.sum(TopicPerformance.total))
        .group_by(TopicPerformance.user_id)
        .all()
    )
    by_user = {uid: (c or 0, t or 0) for uid, c, t in perf}

    accuracies = []
    for s in students:
        c, t = by_user.get(s.id, (0, 0))
        accuracies.append((c / t) if t else 0)

    avg_perf = (sum(accuracies) / len(accuracies)) if accuracies else 0

    subj = (
        db.query(TopicPerformance.subject, func.sum(TopicPerformance.correct), func.sum(TopicPerformance.total))
        .group_by(TopicPerformance.subject)
        .all()
    )
    weakest_subject = "-"
    if subj:
        scored = []
        for s, c, t in subj:
            acc = (c / t) if t else 0
            scored.append((acc, s))
        scored.sort(key=lambda x: x[0])
        weakest_subject = scored[0][1]

    topic = (
        db.query(TopicPerformance.topic, func.sum(TopicPerformance.correct), func.sum(TopicPerformance.total))
        .group_by(TopicPerformance.topic)
        .all()
    )
    insights = []
    if topic:
        scored_t = []
        for tname, c, t in topic:
            acc = (c / t) if t else 0
            scored_t.append((acc, tname))
        scored_t.sort(key=lambda x: x[0])
        weakest_topic = scored_t[0][1]
        insights.append(f"Most students struggle with {weakest_topic}")

    return {
        "students": students,
        "cards": {
            "total_students": len(students),
            "avg_performance": avg_perf,
            "weakest_subject": weakest_subject,
        },
        "insights": insights,
    }


def get_student_detail(user_id: int) -> dict:
    db = get_db_session()
    student = db.query(User).filter(User.id == user_id).first()

    # Get topic performance
    topic = db.query(TopicPerformance).filter(TopicPerformance.user_id == user_id).all()
    
    # Get coding submissions
    subs = db.query(Submission).filter(Submission.user_id == user_id).order_by(Submission.id.desc()).limit(10).all()
    
    # Calculate coding stats
    total_submissions = db.query(Submission).filter(Submission.user_id == user_id).count()
    accepted_submissions = db.query(Submission).filter(
        Submission.user_id == user_id,
        Submission.status == "accepted"
    ).count()
    
    # Calculate topic-wise stats for charts
    topic_stats = []
    for t in topic:
        accuracy = (t.correct / t.total * 100) if t.total else 0
        topic_stats.append({
            "topic": t.topic,
            "subject": t.subject,
            "correct": t.correct,
            "total": t.total,
            "accuracy": round(accuracy, 1)
        })
    
    # Sort by accuracy
    topic_stats_sorted = sorted(topic_stats, key=lambda x: x["accuracy"])
    
    # Weak topics (bottom 5)
    weak_topics = topic_stats_sorted[:5]
    
    # Strong topics (top 5)
    strong_topics = sorted(topic_stats, key=lambda x: x["accuracy"], reverse=True)[:5]
    
    # Calculate overall stats
    total_correct = sum(t.correct for t in topic)
    total_questions = sum(t.total for t in topic)
    overall_accuracy = (total_correct / total_questions * 100) if total_questions else 0
    
    # Subject-wise aggregation
    subject_stats = {}
    for t in topic:
        if t.subject not in subject_stats:
            subject_stats[t.subject] = {"correct": 0, "total": 0}
        subject_stats[t.subject]["correct"] += t.correct
        subject_stats[t.subject]["total"] += t.total
    
    subject_chart_data = []
    for subject, stats in subject_stats.items():
        acc = (stats["correct"] / stats["total"] * 100) if stats["total"] else 0
        subject_chart_data.append({
            "subject": subject,
            "accuracy": round(acc, 1)
        })
    
    # Recent activity (last 7 days simulation)
    recent_activity = []
    for i in range(7):
        recent_activity.append({
            "day": f"Day {i+1}",
            "quizzes": max(0, len(topic) - i) if i < 3 else 0,
            "coding": accepted_submissions if i == 0 else max(0, accepted_submissions - i)
        })
    
    return {
        "student": student,
        "topic": topic,
        "submissions": subs,
        "weak_topics": weak_topics,
        "strong_topics": strong_topics,
        "topic_stats": topic_stats,
        "subject_chart_data": subject_chart_data,
        "coding_stats": {
            "total": total_submissions,
            "accepted": accepted_submissions,
            "rate": round((accepted_submissions / total_submissions * 100), 1) if total_submissions else 0
        },
        "overall_stats": {
            "total_questions": total_questions,
            "correct_answers": total_correct,
            "accuracy": round(overall_accuracy, 1)
        },
        "recent_activity": recent_activity,
        "insights": generate_student_insights(student, weak_topics, overall_accuracy, accepted_submissions, total_submissions)
    }


def generate_student_insights(student, weak_topics, overall_accuracy, accepted_submissions, total_submissions):
    insights = []
    
    if not student:
        return insights
    
    # Overall performance insight
    if overall_accuracy >= 80:
        insights.append(f"🌟 {student.username} is performing excellently with {overall_accuracy:.0f}% overall accuracy!")
    elif overall_accuracy >= 60:
        insights.append(f"📈 {student.username} is showing good progress with {overall_accuracy:.0f}% accuracy. Room for improvement.")
    else:
        insights.append(f"⚠️ {student.username} needs additional support. Overall accuracy is {overall_accuracy:.0f}%.")
    
    # Coding performance
    if total_submissions > 0:
        coding_rate = (accepted_submissions / total_submissions * 100)
        if coding_rate >= 70:
            insights.append(f"💻 Strong coding skills! {coding_rate:.0f}% submission acceptance rate.")
        elif coding_rate >= 40:
            insights.append(f"💻 Coding practice needed. Current acceptance rate: {coding_rate:.0f}%")
        else:
            insights.append(f"💻 Requires significant coding practice. Only {coding_rate:.0f}% submissions accepted.")
    
    # Weak areas
    if weak_topics:
        weakest = weak_topics[0]
        insights.append(f"🎯 Focus area: {weakest['topic']} ({weakest['accuracy']:.0f}% accuracy)")
    
    return insights
