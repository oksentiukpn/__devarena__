from flask import Blueprint

challenges = Blueprint("challenges", __name__)

from app.challenges import routes
