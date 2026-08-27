import re
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()


def configure_security(app):
    csrf.init_app(app)

    @app.after_request
    def set_security_headers(response):
        response.headers['Cross-Origin-Opener-Policy'] = 'same-origin-allow-popups'
        return response


_username_re = re.compile(r"^[a-zA-Z0-9_\-\.]{3,30}$")


def validate_username(username: str) -> bool:
    if not username:
        return False
    return bool(_username_re.match(username))


def validate_password(password: str) -> bool:
    if not password or len(password) < 8:
        return False
    return True
