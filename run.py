from app import create_app
from os import environ

app = create_app()

if __name__ == "__main__":
    debug_mode = environ.get("FLASK_DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", debug=debug_mode)
