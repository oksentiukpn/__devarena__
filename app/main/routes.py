from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy import case, desc

from app import db
from app.auth.utils import login_required
from app.main.utils import check_data
from app.models import Post

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
    user_languages = (
        db.session.query(Post.language)
        .filter_by(user_id=session["user_id"])
        .distinct()
        .all()
    )
    user_languages = [lang[0] for lang in user_languages]

    score_case = case((Post.language.in_(user_languages), 50), else_=0)

    feed_posts = (
        Post.query.filter(Post.visibility == "public")
        .filter(Post.user_id != session["user_id"])
        .order_by(desc(score_case), Post.created_at.desc())
        .limit(20)
        .all()
    )

    return render_template("feed.html", posts=feed_posts)


@main.route("/post", methods=["GET", "POST"])
@login_required
def post():
    if request.method == "POST":
        checked = check_data(request)
        if not isinstance(checked, bool):
            flash(checked, "danger")
        else:
            # adding to db
            feedback_list = request.form.getlist("feedback[]")
            feedback_str = ",".join(feedback_list)
            tags = [tag.strip() for tag in request.form.get("tags").split("#")]
            new_post = Post(
                title=request.form.get("project_name"),
                description=request.form.get("description"),
                language=request.form.get("language"),
                code=request.form.get("code"),
                tags=",".join(tags),
                feedback_type=feedback_str,
                visibility=request.form.get("visibility"),
                user_id=session["user_id"],
            )

            try:
                db.session.add(new_post)
                db.session.commit()
                flash("Your project has been posted!", "success")
                return redirect(url_for("main.feed_page"))
            except Exception as e:
                db.session.rollback()
                flash(f"An error occurred saving the post: {e}", "danger")

    return render_template("post.html")
