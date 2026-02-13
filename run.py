"""
Runner
"""

from os import environ

from app import create_app

app = create_app()

if __name__ == "__main__":
    debug_mode = environ.get("FLASK_DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", debug=debug_mode)
