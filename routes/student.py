import json

from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import current_user, login_required

from services.analytics_service import get_student_dashboard_metrics
from services.task_service import get_tasks
from services.quiz_service import build_quiz_for_user, get_available_topics
from services.coding_service import list_coding_problems, get_problem_payload

student_bp = Blueprint("student", __name__, url_prefix="/student")


def _require_student():
    if current_user.role != "student":
        return redirect(url_for("teacher.dashboard"))
    return None


@student_bp.get("/dashboard")
@login_required
def dashboard():
    gate = _require_student()
    if gate:
        return gate

    metrics = get_student_dashboard_metrics(current_user.id)
    return render_template("student/dashboard.html", metrics=metrics)


@student_bp.get("/tasks")
@login_required
def tasks():
    gate = _require_student()
    if gate:
        return gate

    items = get_tasks()
    return render_template("student/tasks.html", tasks=items)


@student_bp.get("/chat")
@login_required
def chat():
    gate = _require_student()
    if gate:
        return gate

    return render_template("student/chat.html")


@student_bp.get("/quiz")
@login_required
def quiz():
    gate = _require_student()
    if gate:
        return gate

    # Get query parameters for custom quiz
    topic = request.args.get("topic", "all")
    difficulty = request.args.get("difficulty", "medium")
    num_questions = int(request.args.get("num_questions", 5))
    
    # Build quiz with configuration
    quiz = build_quiz_for_user(
        current_user.id, 
        topic=topic if topic != "all" else None,
        num_questions=num_questions,
        difficulty=difficulty
    )
    return render_template("student/quiz.html", quiz_json=json.dumps(quiz))


@student_bp.get("/quiz/config")
@login_required
def quiz_config():
    gate = _require_student()
    if gate:
        return gate

    # Get available topics from dataset
    topics = get_available_topics()
    return render_template("student/quiz_config.html", topics=topics)


@student_bp.get("/coding")
@login_required
def coding_list():
    gate = _require_student()
    if gate:
        return gate

    problems = list_coding_problems(user_id=current_user.id)
    return render_template("student/coding_list.html", problems=problems)


@student_bp.get("/coding/<int:problem_id>")
@login_required
def coding(problem_id: int):
    gate = _require_student()
    if gate:
        return gate

    problem = get_problem_payload(problem_id)
    if not problem:
        return redirect(url_for("student.coding_list"))
    return render_template("student/coding.html", problem=problem)


@student_bp.get("/analytics")
@login_required
def analytics():
    gate = _require_student()
    if gate:
        return gate

    metrics = get_student_dashboard_metrics(current_user.id)
    return render_template("student/analytics.html", metrics=metrics)
