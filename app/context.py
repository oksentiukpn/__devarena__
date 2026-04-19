"""
Context processors and request hooks for the DevArena Flask application.
"""

from flask import g, session
from flask_wtf.csrf import generate_csrf


def register_hooks(app):
    """
    Register application-wide hooks (before_request, after_request)
    and context processors.
    """

    @app.before_request
    def setup_request():
        """
        Runs before every request.
        1. Marks the session as permanent (for 14-day lifetime).
        2. Loads the current user into the global `g` object to prevent
           multiple database queries during a single request lifecycle.
        """
        session.permanent = True

        from app.models import User

        user_id = session.get("user_id")
        if user_id:
            g.user = User.query.get(user_id)
        else:
            g.user = None

    @app.context_processor
    def inject_nav_user():
        """
        Makes the current user available in every Jinja2 template as `nav_user`.
        Instead of querying the DB here, it safely retrieves it from `g.user`.
        """
        return dict(nav_user=getattr(g, "user", None))

    @app.after_request
    def set_csrf_cookie(response):
        """
        Expose the CSRF token in a cookie so JavaScript can read it and
        send it back in the X-CSRFToken header for AJAX/JSON requests.
        Flask-WTF automatically checks this header.
        """
        csrf_token = generate_csrf()

        # We use app.config to dynamically set secure flag
        # based on whether we are in dev or prod mode.
        response.set_cookie(
            "csrf_token",
            csrf_token,
            samesite=app.config.get("SESSION_COOKIE_SAMESITE", "Lax"),
            secure=app.config.get("SESSION_COOKIE_SECURE", True),
            httponly=False,  # Important: JS must be able to read it
        )
        return response
