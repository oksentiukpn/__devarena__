"""
Initializing app
"""

import logging
from datetime import timedelta

from authlib.integrations.flask_client import OAuth
from config import Config
from flask import Flask, session
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect, generate_csrf
from werkzeug.middleware.proxy_fix import ProxyFix

db = SQLAlchemy()
migrate = Migrate()
oauth = OAuth()
csrf = CSRFProtect()


def create_app(config_class=Config):
    """
    Create app
        config_class: Config class
            Config class is used to load config from .env file
            Example:
                from config import Config
                app = create_app(Config)
    """

    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initalising some needed features
    db.init_app(app)
    migrate.init_app(app, db)
    oauth.init_app(app)
    csrf.init_app(app)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Permanent sessions expire after 14 days
    app.permanent_session_lifetime = timedelta(days=14)

    log_level = logging.DEBUG if app.debug else logging.INFO

    gunicorn_logger = logging.getLogger("gunicorn.error")
    if gunicorn_logger.handlers:
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)
    else:
        logging.basicConfig(
            level=log_level,
            format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
        )
        app.logger.setLevel(log_level)

    app.logger.info("DevArena application initialized.")

    # --- Session & CSRF setup ---
    # Mark every session as permanent so the 14-day lifetime applies.
    @app.before_request
    def _make_session_permanent():
        session.permanent = True

    # Expose the CSRF token in a cookie so JavaScript can read it and
    # send it back in the X-CSRFToken header for AJAX/JSON requests.
    # Flask-WTF already checks this header automatically.
    @app.after_request
    def _set_csrf_cookie(response):
        csrf_token = generate_csrf()
        response.set_cookie(
            "csrf_token",
            csrf_token,
            samesite="Lax",
            secure=True,
            httponly=False,  # JS must be able to read it
        )
        return response

    # Registering OAuth
    oauth.register(
        name="google",
        client_id=app.config["GOOGLE_CLIENT_ID"],
        client_secret=app.config["GOOGLE_CLIENT_SECRET"],
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

    from app.auth.routes import auth
    from app.challenges.routes import challenges
    from app.main.routes import main

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(challenges)

    @app.context_processor
    def inject_nav_user():
        """Make the current user available in every template as `nav_user`."""
        from app.models import User

        nav_user = None
        user_id = session.get("user_id")
        if user_id:
            nav_user = User.query.get(user_id)
        return dict(nav_user=nav_user)

    return app
