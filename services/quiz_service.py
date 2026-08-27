import json
import random

from models.dataset import DatasetEntry
from models.quiz import QuizAttempt, TopicPerformance
from utils.db import get_db_session


# Subject-to-topics mapping for structured analytics
SUBJECT_TOPICS = {
    "DSA": ["Arrays", "Strings", "Trees", "Graphs", "Sorting", "Linked List", "Stack", "Queue", "Heap", "Dynamic Programming", "Recursion"],
    "OS": ["Process Scheduling", "Deadlocks", "Memory Management", "Paging", "Segmentation", "File Systems", "CPU Scheduling", "Threads", "Synchronization"],
    "CN": ["Routing", "TCP/IP", "Protocols", "OSI Model", "Network Topology", "DNS", "HTTP", "Subnetting", "Switching"],
    "DBMS": ["SQL", "Normalization", "Transactions", "ACID", "Indexing", "Joins", "ER Model", "Relational Algebra", "NoSQL"]
}

# Reverse mapping: topic -> subject
_TOPIC_TO_SUBJECT = {}
for subj, topics in SUBJECT_TOPICS.items():
    for t in topics:
        _TOPIC_TO_SUBJECT[t.lower()] = subj

# Keyword-based fallback mapping for auto-detection
_KEYWORD_SUBJECT_MAP = {
    "dsa": ["array", "tree", "graph", "sort", "linked list", "stack", "queue", "heap", "dynamic programming", "recursion", "algorithm", "binary", "bst", "avl", "bfs", "dfs"],
    "os": ["process", "scheduling", "deadlock", "memory", "paging", "segmentation", "file system", "cpu", "thread", "semaphore", "mutex", "virtual memory", "disk"],
    "cn": ["network", "routing", "tcp", "ip", "protocol", "osi", "topology", "dns", "http", "subnet", "switch", "router", "packet", "ethernet"],
    "dbms": ["sql", "database", "normalization", "transaction", "acid", "index", "join", "er", "relational", "schema", "query", "table", "nosql", "mongodb"]
}


def _detect_subject(topic: str, question: str = "") -> str:
    """Detect subject from topic name or question content."""
    text = (topic + " " + question).lower()
    
    # Try exact topic match first
    if topic:
        topic_lower = topic.lower()
        if topic_lower in _TOPIC_TO_SUBJECT:
            return _TOPIC_TO_SUBJECT[topic_lower]
    
    # Try keyword matching
    scores = {"DSA": 0, "OS": 0, "CN": 0, "DBMS": 0}
    for subj_key, keywords in _KEYWORD_SUBJECT_MAP.items():
        for kw in keywords:
            if kw in text:
                scores[subj_key.upper()] += 1
    
    if any(scores.values()):
        return max(scores, key=scores.get)
    
    return "DSA"  # Default fallback


def get_available_topics() -> list:
    """Get all unique topics from dataset, organized by subject."""
    db = get_db_session()
    tags = db.query(DatasetEntry.tag).filter(DatasetEntry.entry_type == "intent").distinct().all()
    topics = [t[0] for t in tags if t[0]]
    
    if not topics:
        # Return all predefined topics organized by subject
        all_topics = []
        for subj, subj_topics in SUBJECT_TOPICS.items():
            all_topics.extend(subj_topics)
        return sorted(set(all_topics))
    
    return sorted(set(topics))


def build_quiz_for_user(user_id: int, topic: str = None, num_questions: int = 5, difficulty: str = "medium") -> dict:
    db = get_db_session()
    
    # Query base intents
    query = db.query(DatasetEntry).filter(DatasetEntry.entry_type == "intent")
    
    # Filter by topic if specified
    if topic and topic != "all":
        query = query.filter(DatasetEntry.tag == topic)
    
    intents = query.all()
    pool = [e for e in intents if e.question and e.answer]
    
    # If not enough questions for specific topic, fall back to all
    if len(pool) < num_questions and topic and topic != "all":
        intents = db.query(DatasetEntry).filter(DatasetEntry.entry_type == "intent").all()
        pool = [e for e in intents if e.question and e.answer]
    
    # Shuffle and select
    random.shuffle(pool)
    selected = pool[:num_questions]
    
    # Map difficulty to question complexity (using answer length as proxy)
    if difficulty == "easy":
        # Prefer shorter answers
        pool_easy = [e for e in pool if len(e.answer) < 200]
        if len(pool_easy) >= num_questions:
            random.shuffle(pool_easy)
            selected = pool_easy[:num_questions]
    elif difficulty == "hard":
        # Prefer longer, more complex answers
        pool_hard = [e for e in pool if len(e.answer) > 300]
        if len(pool_hard) >= num_questions:
            random.shuffle(pool_hard)
            selected = pool_hard[:num_questions]

    questions = []
    for e in selected:
        correct = e.answer.strip()
        distractors = [x.answer.strip() for x in random.sample(pool, k=min(3, len(pool))) if x.id != e.id]
        options = [correct] + distractors
        options = list(dict.fromkeys([o for o in options if o]))[:4]
        random.shuffle(options)

        # Detect real subject from tag/question
        topic_name = e.tag or "General"
        subject = _detect_subject(topic_name, e.question)
        
        questions.append(
            {
                "id": e.id,
                "subject": subject,
                "topic": topic_name,
                "difficulty": difficulty,
                "question": e.question,
                "options": options,
                "correct": correct,
            }
        )

    return {
        "questions": questions,
        "config": {
            "topic": topic or "all",
            "num_questions": num_questions,
            "difficulty": difficulty
        }
    }


def grade_quiz(user_id: int, quiz: dict, answers: dict) -> dict:
    questions = quiz.get("questions") or []
    correct = 0
    detailed_results = []

    db = get_db_session()

    topic_updates = {}
    weak_topics = []  # Track weak areas for suggestions
    
    for q in questions:
        qid = str(q.get("id"))
        chosen = (answers.get(qid) or "").strip()
        correct_answer = (q.get("correct") or "").strip()
        is_correct = chosen == correct_answer
        
        if is_correct:
            correct += 1

        subject = q.get("subject") or "DSA"
        topic = q.get("topic") or "General"
        
        # Track weak topics (wrong answers)
        if not is_correct:
            weak_topics.append({"topic": topic, "subject": subject})
        
        key = (subject, topic)
        if key not in topic_updates:
            topic_updates[key] = {"correct": 0, "total": 0}
        topic_updates[key]["total"] += 1
        if is_correct:
            topic_updates[key]["correct"] += 1
            
        # Store detailed result
        detailed_results.append({
            "question_id": q.get("id"),
            "question": q.get("question"),
            "your_answer": chosen,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "topic": topic,
            "subject": subject
        })

    total = len(questions)

    attempt = QuizAttempt(
        user_id=user_id,
        task_id=None,
        questions_json=json.dumps(quiz),
        answers_json=json.dumps(answers),
        score=correct,
        total=total,
    )
    db.add(attempt)

    for (subject, topic), upd in topic_updates.items():
        tp = (
            db.query(TopicPerformance)
            .filter(TopicPerformance.user_id == user_id)
            .filter(TopicPerformance.subject == subject)
            .filter(TopicPerformance.topic == topic)
            .first()
        )
        if not tp:
            tp = TopicPerformance(user_id=user_id, subject=subject, topic=topic, correct=0, total=0)
            db.add(tp)
        tp.correct += upd["correct"]
        tp.total += upd["total"]

    db.commit()

    accuracy = (correct / total) if total else 0
    
    # Identify unique weak topics
    unique_weak_topics = list(set([t["topic"] for t in weak_topics]))

    return {
        "score": correct, 
        "total": total, 
        "accuracy": accuracy,
        "results": detailed_results,
        "weak_topics": unique_weak_topics,
        "config": quiz.get("config", {})
    }


def generate_quiz_suggestions(score: int, total: int, accuracy: float, weak_topics: list, config: dict) -> str:
    """Generate AI-powered suggestions based on quiz performance using Groq API."""
    from services.groq_client import groq_chat
    
    percentage = (accuracy * 100)
    topic_str = ", ".join(weak_topics) if weak_topics else "None - Great job!"
    difficulty = config.get("difficulty", "medium")
    selected_topic = config.get("topic", "all")
    
    # Create performance summary
    if percentage >= 80:
        performance_level = "excellent"
        encouragement = "Outstanding performance!"
    elif percentage >= 60:
        performance_level = "good"
        encouragement = "Good work, but there's room for improvement."
    elif percentage >= 40:
        performance_level = "average"
        encouragement = "Keep practicing! You're making progress."
    else:
        performance_level = "needs improvement"
        encouragement = "Don't give up! Focus on the fundamentals."
    
    prompt = f"""You are an encouraging learning assistant. A student just completed a quiz with the following results:

Quiz Configuration:
- Topic: {selected_topic}
- Difficulty: {difficulty}
- Questions: {total}

Performance:
- Score: {score}/{total} ({percentage:.1f}%)
- Performance Level: {performance_level}
- Weak Areas: {topic_str}

Provide a brief, encouraging summary (2-3 sentences) and specific, actionable suggestions (2-3 bullet points) to help them improve. Be supportive and motivating. Keep your response under 150 words.

Format:
Summary: [encouraging summary]

Suggestions:
• [suggestion 1]
• [suggestion 2]  
• [suggestion 3]"""

    try:
        suggestion = groq_chat(prompt)
        return suggestion.strip()
    except Exception as e:
        # Fallback suggestions if AI fails
        return f"""Summary: {encouragement} You scored {score} out of {total} questions.

Suggestions:
• Review the topics you got wrong: {topic_str}
• Practice with similar difficulty questions
• Use the Chat AI feature to get explanations for challenging concepts"""
