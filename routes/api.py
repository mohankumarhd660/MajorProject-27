import json

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from services.ai_service import answer_query
from services.quiz_service import grade_quiz, generate_quiz_suggestions
from services.coding_service import run_code, submit_code
from utils.security import csrf

api_bp = Blueprint("api", __name__, url_prefix="/api")
csrf.exempt(api_bp)


@api_bp.post("/chat")
@login_required
def chat_api():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    thread_id = (data.get("thread_id") or "default").strip()[:64]

    if not message:
        return jsonify({"error": "Empty message"}), 400

    try:
        result = answer_query(user_id=current_user.id, thread_id=thread_id, query=message)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e), "error_type": e.__class__.__name__}), 400


@api_bp.post("/quiz/submit")
@login_required
def quiz_submit():
    payload = request.get_json(silent=True) or {}
    quiz = payload.get("quiz")
    answers = payload.get("answers")

    if not isinstance(quiz, dict) or not isinstance(answers, dict):
        return jsonify({"error": "Invalid payload"}), 400

    result = grade_quiz(current_user.id, quiz, answers)
    return jsonify(result)


@api_bp.post("/quiz/suggestions")
@login_required
def quiz_suggestions():
    payload = request.get_json(silent=True) or {}
    score = payload.get("score", 0)
    total = payload.get("total", 0)
    accuracy = payload.get("accuracy", 0)
    weak_topics = payload.get("weak_topics", [])
    config = payload.get("config", {})
    
    try:
        suggestions = generate_quiz_suggestions(score, total, accuracy, weak_topics, config)
        return jsonify({"suggestions": suggestions})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@api_bp.post("/code/run")
@login_required
def code_run():
    payload = request.get_json(silent=True) or {}
    problem_id = int(payload.get("problem_id") or 0)
    code = payload.get("code") or ""
    language = (payload.get("language") or "python").strip().lower()
    custom_input = payload.get("custom_input")

    result = run_code(
        current_user.id,
        problem_id,
        code,
        language=language,
        custom_input=custom_input,
    )
    status = 200 if result.get("ok") else 400
    return jsonify(result), status


@api_bp.post("/code/submit")
@login_required
def code_submit():
    payload = request.get_json(silent=True) or {}
    problem_id = int(payload.get("problem_id") or 0)
    code = payload.get("code") or ""
    language = (payload.get("language") or "python").strip().lower()

    result = submit_code(current_user.id, problem_id, code, language=language)
    status = 200 if result.get("ok") else 400
    return jsonify(result), status
