from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import case, desc
from sqlalchemy.orm import joinedload

from app import db
from app.auth.utils import login_required
from app.main.form import PostForm
from app.models import Comment, Post, Reaction, User
from app.main.utils import save_profile_picture
import re
# from app.main.search import search_posts, search_users

main = Blueprint("main", __name__)
sttgs = Blueprint("settings", __name__)

@main.route("/")
def home():
    return render_template("test_pages/main_test.html")


@main.route("/privacy")
def privacy_policy():
    return render_template("main/privacy.html")

@main.route("/authors")
def authors():
    return render_template("main/authors.html")

@main.route("/terms")
def terms_of_service():
    return render_template("main/terms.html")


@main.route("/settings")
@login_required
def settings_page():
    user = User.query.get(session["user_id"])
    return render_template("main/settings.html", user=user)

# @main.route("/settings")
# @login_required
# def settings_page():
    # user_languages = (
    #     db.session.query(Post.language)
    #     .filter_by(user_id=session["user_id"])
    #     .distinct()
    #     .all()
    # )
    # user_languages = [lang[0] for lang in user_languages]
    # return render_template("main/settings.html")

@sttgs.route("/profile_save_changes")
@login_required
def save_changes():


    return redirect(url_for("settings.html"))
    # return render_template("main/settings.html")

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
        raw_tags = [
            tag
            for tag in form.tags.data.replace("#", " ").split()
            if tag not in ("", " ")
        ]
        clean_tags = "".join([tag.strip() for tag in raw_tags])
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
            "id": new_comment.id,
            "content": new_comment.content,
            "author": new_comment.author.username,
            "created_at": new_comment.created_at.strftime("%b %d"),
            "avatar_letter": new_comment.author.username[:2],
        }
    )

# @sttgs.route("/settings", methods=["GET", "POST"])
# @login_required
# def settings():
#     if request.method == "POST":
#         new_username = (request.form.get("username") or "").strip()
#         new_bio = (request.form.get("bio") or "").strip()

#         # basic validation
#         if not (3 <= len(new_username) <= 20):
#             flash("Username must be 3–20 characters.", "error")
#             return redirect(url_for("settings.settings", _anchor="profile"))

#         if len(new_bio) > 1024:
#             flash("Bio is too long (max 1024 chars).", "error")
#             return redirect(url_for("settings.settings", _anchor="profile"))

#         username_taken = (
#             User.query.filter(User.username == new_username, User.id != current_user.id).first()
#         )
#         if username_taken:
#             flash("That username is already taken.", "error")
#             return redirect(url_for("settings.settings", _anchor="profile"))

#         # save
#         current_user.username = new_username
#         current_user.bio = new_bio
#         db.session.commit()

#         flash("Profile updated.", "success")
#         return redirect(url_for("settings.settings", _anchor="profile"))

#     return render_template("settings.html")  # current_user is available in template


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


@main.route("/post/<int:post_id>", methods=["DELETE"])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)

    # Security Check: Ensure current user is the author
    if post.user_id != session["user_id"]:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        db.session.delete(post)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@main.route("/comment/<int:comment_id>", methods=["DELETE"])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    # Security Check: Ensure current user is the author
    if comment.user_id != session["user_id"]:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        # We need the post_id to update the UI counter if needed,
        # though strictly not required for the DB delete
        post_id = comment.post_id
        db.session.delete(comment)
        db.session.commit()

        # Get new comment count for the UI
        count = Comment.query.filter_by(post_id=post_id).count()
        return jsonify({"success": True, "count": count, "post_id": post_id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@main.route("/battles")
def battles():
    # rick-roll
    return redirect(url_for("challenges.create_battle"))


@main.route("/profile_save_changes", methods=["POST"])
@login_required
def profile_save_changes():
    user = User.query.get(session["user_id"])

    # 1) read inputs
    new_username = request.form.get("username", "").strip()
    new_bio = request.form.get("bio", "").strip()

    # 2) validate username if changed
    if new_username and new_username != user.username:
        if not re.match(r"^\w+$", new_username):
            flash("Username can only contain letters, numbers and underscores.", "danger")
            return redirect(url_for("main.settings_page", _anchor="profile"))

        if User.query.filter_by(username=new_username).first():
            flash("Username already exists.", "danger")
            return redirect(url_for("main.settings_page", _anchor="profile"))

        user.username = new_username

    # 3) update bio (bio is non-null, so store empty string if blank)
    user.bio = new_bio

    # 4) handle image upload (optional)
    file = request.files.get("profile_picture")
    if file and file.filename:
        try:
            filename = save_profile_picture(file)
            user.image_file = filename
        except Exception as e:
            flash(f"Image upload failed: {e}", "danger")
            return redirect(url_for("main.settings_page", _anchor="profile"))

    # 5) commit safely
    try:
        db.session.commit()
        flash("Profile updated!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Database error: {e}", "danger")

    return redirect(url_for("main.settings_page", _anchor="profile"))


# @main.route("/search")
# def search_page():
#     q = (request.args.get("q") or "").strip()
#     tab = (request.args.get("tab") or "posts").strip()  # "posts" or "users"

#     posts = []
#     users = []

#     if q:
#         if tab == "users":
#             users = search_users(q, limit=20)
#         else:
#             posts = search_posts(q, limit=20)

#     return render_template("main/search.html", q=q, tab=tab, posts=posts, users=users)
