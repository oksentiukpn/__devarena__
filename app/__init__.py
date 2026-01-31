from authlib.integrations.flask_client import OAuth
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import Config

db = SQLAlchemy()
migrate = Migrate()
oauth = OAuth()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initalising some needed features
    db.init_app(app)
    migrate.init_app(app, db)
    oauth.init_app(app)

    # Registering OAuth
    oauth.register(
        name="google",
        client_id=app.config["GOOGLE_CLIENT_ID"],
        client_secret=app.config["GOOGLE_CLIENT_SECRET"],
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

    from app.auth.routes import auth
    from app.main.routes import main

    app.register_blueprint(main)
    app.register_blueprint(auth)

    return app
