from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required

from services.teacher_service import get_teacher_dashboard, get_student_detail

teacher_bp = Blueprint("teacher", __name__, url_prefix="/teacher")


def _require_teacher():
    if current_user.role != "teacher":
        return redirect(url_for("student.dashboard"))
    return None


@teacher_bp.get("/dashboard")
@login_required
def dashboard():
    gate = _require_teacher()
    if gate:
        return gate

    data = get_teacher_dashboard()
    return render_template("teacher/dashboard.html", data=data)


@teacher_bp.get("/students/<int:user_id>")
@login_required
def student_detail(user_id: int):
    gate = _require_teacher()
    if gate:
        return gate

    detail = get_student_detail(user_id)
    return render_template("teacher/student_detail.html", detail=detail)
