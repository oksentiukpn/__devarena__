from flask import (Blueprint, flash, jsonify, redirect, render_template,
                   request, session, url_for)
from sqlalchemy import case, desc
from sqlalchemy.orm import joinedload

from app import db
from app.auth.utils import login_required
from app.main.form import PostForm
from app.models import Comment, Post, Reaction, User

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
        Post.query.options(joinedload(Post.author))
        .filter(Post.visibility == "public")
        .filter(Post.user_id != session["user_id"])
        .order_by(desc(score_case), Post.created_at.desc())
        .limit(20)
        .all()
    )

    return render_template("feed.html", posts=feed_posts)


@main.route("/post", methods=["GET", "POST"])
@login_required
def post():
    form = PostForm()
    if request.method == "POST":
        raw_tags = form.tags.data.replace("#", " ").split()
        clean_tags = ",".join([tag.strip() for tag in raw_tags])
        feedback_str = ",".join(form.feedback.data)

        # 3. Create Post
        new_post = Post(
            title=form.project_name.data,
            description=form.description.data,
            language=form.language.data,
            code=form.code.data,
            tags=clean_tags,
            feedback_type=feedback_str,
            visibility=form.visibility.data,
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


@main.route("/post/<int:post_id>/react", methods=["POST"])
@login_required
def toggle_reaction(post_id):
    data = request.json
    emoji = data.get("emoji")

    if not emoji:
        return jsonify({"error": "Emoji is required"}), 400

    existing_reaction = Reaction.query.filter_by(
        user_id=session["user_id"], post_id=post_id, emoji=emoji
    ).first()

    status = ""
    if existing_reaction:
        db.session.delete(existing_reaction)
        status = "removed"
    else:
        new_reaction = Reaction(
            user_id=session["user_id"], post_id=post_id, emoji=emoji
        )
        db.session.add(new_reaction)
        status = "added"

    db.session.commit()

    count = Reaction.query.filter_by(post_id=post_id, emoji=emoji).count()

    return jsonify({"status": status, "emoji": emoji, "count": count})


@main.route("/post/<int:post_id>/comment", methods=["POST"])
@login_required
def add_comment(post_id):
    data = request.json
    content = data.get("content")

    if not content or not content.strip():
        return jsonify({"error": "Comment can`t be empty"}, 400)

    new_comment = Comment(
        content=content.strip(), user_id=session["user_id"], post_id=post_id
    )

    db.session.add(new_comment)
    db.session.commit()

    return jsonify(
        {
            "id": new_comment.content,
            "content": new_comment.content,
            "author": new_comment.author.username,
            "created_at": new_comment.created_at.strftime("%b %d"),
            "avatar_letter": new_comment.author.username[:2],
        }
    )


# Current User
@main.route("/profile")
@login_required
def profile():
    user = User.query.get(session["user_id"])

    posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).all()

    return render_template("main/profile.html", user=user, posts=posts)


# Other users
@main.route("/user/<username>")
@login_required
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).all()
    return render_template("main/profile.html", user=user, posts=posts)


@main.route("/battles")
def battles():
    return redirect("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s")
