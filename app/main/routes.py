from datetime import datetime, timedelta

from flask import (
    Blueprint,
    Response,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from itsdangerous import URLSafeSerializer
from sqlalchemy import case, desc, func, or_
from sqlalchemy.orm import joinedload

from app.main.profile import count_battles, count_reactions

from app import db
from app.auth.utils import login_required
from app.main.form import PostForm
from app.models import Battle, Comment, Post, Reaction, User

main = Blueprint("main", __name__)


@main.route("/")
def home():
    return render_template("home.html")


@main.route("/privacy")
def privacy():
    return render_template("main/privacy.html")


@main.route("/terms")
def terms():
    return render_template("main/terms.html")


@main.route("/feed")
@login_required
def feed_page():
    current_user = User.query.get(session["user_id"])
    post_count = Post.query.filter_by(user_id=session["user_id"]).count()

    # Active battles for the sidebar
    active_battles = (
        Battle.query.options(joinedload(Battle.author))
        .filter(
            Battle.visibility == "public",
            Battle.status.in_(["waiting", "ready", "in_progress", "in_review"]),
        )
        .order_by(Battle.created_at.desc())
        .limit(5)
        .all()
    )

    sort = request.args.get("sort", "recommended")
    if sort not in ("latest", "top", "recommended"):
        sort = "recommended"

    base_query = Post.query.options(joinedload(Post.author)).filter(
        Post.visibility == "public"
    )

    if sort == "latest":
        feed_posts = base_query.order_by(Post.created_at.desc()).limit(20).all()

    elif sort == "top":
        # Rank by total engagement: reactions + comments (all time)
        reaction_count = (
            db.session.query(
                Reaction.post_id,
                func.count(Reaction.id).label("r_count"),
            )
            .group_by(Reaction.post_id)
            .subquery()
        )
        comment_count = (
            db.session.query(
                Comment.post_id,
                func.count(Comment.id).label("c_count"),
            )
            .group_by(Comment.post_id)
            .subquery()
        )

        engagement = (
            func.coalesce(reaction_count.c.r_count, 0) * 5
            + func.coalesce(comment_count.c.c_count, 0) * 10
        )

        feed_posts = (
            base_query.outerjoin(reaction_count, Post.id == reaction_count.c.post_id)
            .outerjoin(comment_count, Post.id == comment_count.c.post_id)
            .order_by(desc(engagement), Post.created_at.desc())
            .limit(20)
            .all()
        )

    else:
        # --- Recommended algorithm ---
        # Signals combined into a single score:
        #   1. Language affinity  – posts in languages the user writes get +40
        #   2. Tag overlap        – posts sharing tags with user's posts get +30
        #   3. Engagement quality – (reactions*5 + comments*10), capped contribution
        #   4. Recency boost      – posts from the last 3 days get +25, last 7 days +10
        #   5. Slight penalty for user's own posts so others' work surfaces first

        # Gather user's languages
        user_languages = (
            db.session.query(Post.language)
            .filter_by(user_id=session["user_id"])
            .distinct()
            .all()
        )
        user_languages = [lang[0] for lang in user_languages]

        # Gather user's tags for tag-overlap signal
        user_tags_raw = (
            db.session.query(Post.tags).filter_by(user_id=session["user_id"]).all()
        )
        user_tags = set()
        for (tags_str,) in user_tags_raw:
            if tags_str:
                for t in tags_str.split(","):
                    stripped = t.strip().lower()
                    if stripped:
                        user_tags.add(stripped)

        # Language affinity score
        if user_languages:
            lang_score = case(
                (Post.language.in_(user_languages), 40),
                else_=0,
            )
        else:
            lang_score = 0

        # Tag overlap score – match any of the user's tags
        if user_tags:
            tag_conditions = [
                Post.tags.ilike(f"%{tag}%") for tag in list(user_tags)[:20]
            ]
            # OR across all tag patterns; if any match → +30
            tag_score = case(
                (or_(*tag_conditions), 30),
                else_=0,
            )
        else:
            tag_score = 0

        # Engagement sub-queries
        reaction_count = (
            db.session.query(
                Reaction.post_id,
                func.count(Reaction.id).label("r_count"),
            )
            .group_by(Reaction.post_id)
            .subquery()
        )
        comment_count = (
            db.session.query(
                Comment.post_id,
                func.count(Comment.id).label("c_count"),
            )
            .group_by(Comment.post_id)
            .subquery()
        )

        # Engagement score (cap at 50 so viral posts don't completely dominate)
        raw_engagement = (
            func.coalesce(reaction_count.c.r_count, 0) * 5
            + func.coalesce(comment_count.c.c_count, 0) * 10
        )
        engagement_score = case(
            (raw_engagement > 50, 50),
            else_=raw_engagement,
        )

        # Recency boost
        now = datetime.utcnow()
        recency_score = case(
            (Post.created_at >= now - timedelta(days=3), 25),
            (Post.created_at >= now - timedelta(days=7), 10),
            else_=0,
        )

        # Small penalty for own posts so discovery of others is prioritised
        own_post_penalty = case(
            (Post.user_id == session["user_id"], -15),
            else_=0,
        )

        total_score = (
            lang_score + tag_score + engagement_score + recency_score + own_post_penalty
        )

        feed_posts = (
            base_query.outerjoin(reaction_count, Post.id == reaction_count.c.post_id)
            .outerjoin(comment_count, Post.id == comment_count.c.post_id)
            .order_by(desc(total_score), Post.created_at.desc())
            .limit(20)
            .all()
        )

    return render_template(
        "feed.html",
        posts=feed_posts,
        post_count=post_count,
        current_user=current_user,
        sort=sort,
        active_battles=active_battles,
    )


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
        clean_tags = ",".join([tag.strip() for tag in raw_tags])
        feedback_str = ",".join(form.feedback.data)

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
            current_app.logger.info(
                f"New post created: '{new_post.title}' by user_id {session['user_id']}"
            )
            flash("Your project has been posted!", "success")
            return redirect(url_for("main.feed_page"))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating post: {e}")
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
        return jsonify({"error": "Comment can't be empty"}), 400

    new_comment = Comment(
        content=content.strip(), user_id=session["user_id"], post_id=post_id
    )

    db.session.add(new_comment)

    current_app.logger.info(
        f"New comment added to post_id {post_id} by user_id {session['user_id']}"
    )

    return jsonify(
        {
            "id": new_comment.id,
            "content": new_comment.content,
            "author": new_comment.author.username,
            "created_at": new_comment.created_at.strftime("%b %d"),
            "avatar_letter": new_comment.author.username[:2],
        }
    )


@main.route("/profile")
@login_required
def profile():
    user = User.query.get(session["user_id"])
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).all()
    battles_count = count_battles(user)
    reactions_count = count_reactions(user)


    return render_template(
        "main/profile.html",
        user=user,
        posts=posts,
        battles_count=battles_count,
        reactions_count=reactions_count,
    )


@main.route("/user/<username>")
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).all()
    return render_template("main/profile.html", user=user, posts=posts)


@main.route("/post/<int:post_id>", methods=["DELETE"])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    current_user = User.query.get(session["user_id"])

    # Security Check: Ensure current user is the author
    if post.user_id != current_user.id and not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        db.session.delete(post)
        db.session.commit()
        current_app.logger.info(
            f"Post with id {post_id} deleted by user_id {session['user_id']}"
        )
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@main.route("/post/<int:post_id>", methods=["GET"])
def view_post(post_id):
    post = Post.query.options(joinedload(Post.author)).get_or_404(post_id)
    return render_template("main/view_post.html", post=post)


@main.route("/comment/<int:comment_id>", methods=["DELETE"])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    current_user = User.query.get(session["user_id"])

    # Security Check: Ensure current user is the author
    if comment.user_id != current_user.id and not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        post_id = comment.post_id

        db.session.delete(comment)
        db.session.commit()

        count = Comment.query.filter_by(post_id=post_id).count()
        return jsonify({"success": True, "count": count, "post_id": post_id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@main.route("/battles")
@login_required
def battles():
    user_id = session.get("user_id")

    feed_battles = (
        Battle.query.options(joinedload(Battle.author))
        .filter(Battle.visibility == "public")
        .order_by(Battle.created_at.desc())
        .limit(20)
        .all()
    )

    battles_won = Battle.query.filter(Battle.winner_id == user_id).count()

    battles_participated = Battle.query.filter(
        or_(Battle.user_id == user_id, Battle.opponent_id == user_id)
    ).count()

    top_warriors = (
        db.session.query(
            User,
            func.count(Battle.winner_id).label("wins"),
        )
        .join(Battle, Battle.winner_id == User.id)
        .group_by(User.id)
        .order_by(desc("wins"))
        .limit(5)
        .all()
    )

    return render_template(
        "battles.html",
        battles=feed_battles,
        battles_won=battles_won,
        battles_participated=battles_participated,
        top_warriors=top_warriors,
    )


@main.route("/sitemap.xml")
def sitemap():
    users = User.query.all()
    posts = Post.query.filter_by(visibility="public").all()

    xml_content = render_template("sitemap.xml", users=users, posts=posts)

    return Response(xml_content, mimetype="application/xml")


@main.route("/robots.txt")
def robots():
    robots_content = """User-agent: *
Disallow: /login
Disallow: /register
Allow: /

Sitemap: https://devarena.pp.ua/sitemap.xml
"""
    return Response(robots_content, mimetype="text/plain")


@main.route("/unsubscribe/<token>", methods=["GET", "POST"])
def unsubscribe(token):
    ser = URLSafeSerializer(current_app.config["SECRET_KEY"])
    try:
        user_id = ser.loads(token, salt="unsubscribe-daily-prompt")
    except Exception:
        flash("Invalid or corrupted unsubscribe link.", "danger")
        return redirect(url_for("main.home"))

    user = User.query.get(user_id)
    if user:
        user.subscribed_to_daily_prompt = False
        db.session.commit()

    if request.method == "POST":
        return "Unsubscribed successfully", 200

    current_app.logger.info(f"User with id {user_id} unsubscribed from daily prompts.")
    flash("You have been successfully unsubscribed from daily prompts.", "success")
    return redirect(url_for("main.home"))


@main.route("/settings")
@login_required
def settings():
    return "Not implemented yet"


@main.route("/authors")
def authors():
    return "Not implemented yet"


@main.route("/leaderboard")
def leaderboard():
    users_list = User.query.order_by(User.points.desc()).limit(10).all()
    return render_template("leaderboard.html", users=users_list)
