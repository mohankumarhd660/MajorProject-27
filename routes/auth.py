from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from forms.auth_forms import LoginForm, SignupForm
from services.auth_service import authenticate, create_user, authenticate_by_firebase
from services.firebase_service import verify_firebase_token
from utils.security import validate_password, validate_username
import os

auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/")
def landing():
    if current_user.is_authenticated:
        return redirect(url_for("auth.post_login"))
    return render_template("landing.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("auth.post_login"))

    form = LoginForm()
    firebase_config = {
        "apiKey": os.getenv("FIREBASE_API_KEY", ""),
        "authDomain": "ai-learning-assistant-36c3e.firebaseapp.com",
        "projectId": "ai-learning-assistant-36c3e"
    }

    if form.validate_on_submit():
        user = authenticate(form.username.data.strip(), form.password.data)
        if user:
            login_user(user)
            return redirect(url_for("auth.post_login"))
        return render_template("login.html", form=form, error="Invalid credentials", fb_config=firebase_config)

    return render_template("login.html", form=form, fb_config=firebase_config)


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("auth.post_login"))

    firebase_config = {
        "apiKey": os.getenv("FIREBASE_API_KEY", ""),
        "authDomain": "ai-learning-assistant-36c3e.firebaseapp.com",
        "projectId": "ai-learning-assistant-36c3e"
    }

    form = SignupForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip() if form.email.data else None
        password = form.password.data
        role = form.role.data

        if not validate_username(username):
            return render_template("signup.html", form=form, error="Invalid username", fb_config=firebase_config)
        if not validate_password(password):
            return render_template("signup.html", form=form, error="Password must be at least 8 characters", fb_config=firebase_config)

        try:
            user = create_user(username, password, role, email=email)
        except ValueError as e:
            return render_template("signup.html", form=form, error=str(e), fb_config=firebase_config)

        login_user(user)
        return redirect(url_for("auth.post_login"))

    return render_template("signup.html", form=form, fb_config=firebase_config)


@auth_bp.post("/google-login")
def google_login():
    data = request.get_json()
    id_token = data.get("id_token")
    if not id_token:
        return {"error": "Missing token"}, 400
        
    try:
        token_data = verify_firebase_token(id_token)
        email = token_data.get("email")
        uid = token_data.get("uid")
        name = token_data.get("name")
        
        user = authenticate_by_firebase(email, uid, name)
        if user:
            login_user(user)
            return {"status": "success", "redirect": url_for("auth.post_login")}, 200
        return {"error": "Could not authenticate"}, 401
    except Exception as e:
        return {"error": str(e)}, 401


@auth_bp.get("/post-login")
@login_required
def post_login():
    if current_user.role == "teacher":
        return redirect(url_for("teacher.dashboard"))
    return redirect(url_for("student.dashboard"))


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    next_url = request.args.get("next")
    return redirect(next_url or url_for("auth.landing"))
