"""
Initializing app
"""

from authlib.integrations.flask_client import OAuth
from config import Config
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix

db = SQLAlchemy()
migrate = Migrate()
oauth = OAuth()


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
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    # app.permanent_session_lifetime = timedelta(days=14)

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

    return app
