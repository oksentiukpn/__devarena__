from flask import Blueprint, flash, render_template, request

from app.auth.utils import login_required
from app.main.utils import check_data

main = Blueprint("main", __name__)


@main.route("/")
def home():
    return render_template("test_pages/main_test.html")


@main.route("/privacy")
def privacy_policy():
    return render_template("main/privacy.html")


@main.route("/feed")
@login_required
def feed_page():
    return render_template("feed.html")


@main.route("/post", methods=["GET", "POST"])
@login_required
def post():
    if request.method == "POST":
        checked = check_data(request)
        if not isinstance(checked, bool):
            flash(checked)
    return render_template("post.html")
