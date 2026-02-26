from datetime import datetime, timedelta

from flask import (
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app import db
from app.auth.utils import login_required
from app.challenges import challenges
from app.main.form import BattleForm
from app.models import Battle, BattleComment, BattleVote


def parse_time_limit(limit_str):
    if "min" in limit_str:
        return int(limit_str.split()[0])
    elif "hour" in limit_str:
        return int(limit_str.split()[0]) * 60
    return 60  # Default 60 mins


@challenges.route("/battle/create", methods=["GET", "POST"])
@login_required
def create_battle():
    """Create battle route
    GET: Render battle creation form
    POST: Handle battle creation logic
    """
    form = BattleForm()

    if form.validate_on_submit():
        # Clean tags logic
        raw_tags = [
            tag
            for tag in form.tags.data.replace("#", " ").split()
            if tag not in ("", " ")
        ]
        # joining with comma to ensure template compatibility: post.tags.split(',')
        clean_tags = ",".join([tag.strip() for tag in raw_tags])

        final_time_limit = form.time_limit.data
        if final_time_limit == "Custom":
            if form.custom_time.data:
                final_time_limit = f"{form.custom_time.data} min"
            else:
                flash(
                    "Please enter a valid number of minutes for custom time.", "danger"
                )
                return render_template("main/create_battle.html", form=form)

        new_battle = Battle(
            title=form.title.data,
            description=form.description.data,
            time_limit=final_time_limit,
            language=form.language.data,
            difficulty=form.difficulty.data,
            tags=clean_tags,
            visibility=form.visibility.data,
            user_id=session["user_id"],
        )

        try:
            db.session.add(new_battle)
            db.session.commit()
            current_app.logger.info(
                f"User {session['user_id']} created battle '{new_battle.title}' (ID: {new_battle.id})"
            )
            flash("Battle created successfully!", "success")
            return redirect(url_for("main.battles"))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating battle: {e}")
            flash(f"An error occurred creating the battle: {e}", "danger")

    return render_template("main/create_battle.html", form=form)


@challenges.route("/battle/<int:battle_id>/join", methods=["POST"])
@login_required
def join_battle(battle_id):
    battle = Battle.query.get_or_404(battle_id)

    # Check if user is the creator or if it's already full
    if battle.user_id == session["user_id"]:
        return redirect(url_for("challenges.arena", battle_id=battle.id))

    if battle.opponent_id is None:
        battle.opponent_id = session["user_id"]
        battle.status = "ready"
        db.session.commit()
        current_app.logger.info(
            f"User {session['user_id']} joined battle '{battle.title}' (ID: {battle.id})"
        )
        flash("Joined the battle!", "success")

    elif battle.opponent_id != session["user_id"]:
        flash("This battle is already full.", "danger")
        return redirect(url_for("main.battles"))

    return redirect(url_for("challenges.arena", battle_id=battle.id))


@challenges.route("/battle/<int:battle_id>/arena")
@login_required
def arena(battle_id):
    battle = Battle.query.get_or_404(battle_id)

    if session["user_id"] not in [battle.user_id, battle.opponent_id]:
        flash("You are not part of this battle.", "danger")
        return redirect(url_for("main.battles"))

    is_creator = session["user_id"] == battle.user_id

    return render_template("main/arena.html", battle=battle, is_creator=is_creator)


@challenges.route("/battle/<int:battle_id>/api/status")
@login_required
def battle_status(battle_id):
    battle = Battle.query.get_or_404(battle_id)

    # Calculate remaining time if in progress
    time_left = 0
    if battle.status == "in_progress" and battle.end_time:
        time_left = (battle.end_time - datetime.utcnow()).total_seconds()
        if time_left <= 0:
            battle.status = "in_review"
            battle.review_end_time = datetime.utcnow() + timedelta(minutes=30)
            db.session.commit()
            time_left = 0

    is_creator = session["user_id"] == battle.user_id

    return jsonify(
        {
            "status": battle.status,
            "opponent_joined": battle.opponent_id is not None,
            "opponent_username": battle.opponent.username if battle.opponent else None,
            "creator_ready": battle.creator_ready,
            "opponent_ready": battle.opponent_ready,
            "opponent_submitted": battle.opponent_submitted
            if is_creator
            else battle.creator_submitted,
            "time_left": max(0, int(time_left)),
        }
    )


@challenges.route("/battle/<int:battle_id>/api/ready", methods=["POST"])
@login_required
def toggle_ready(battle_id):
    battle = Battle.query.get_or_404(battle_id)

    is_creator = session["user_id"] == battle.user_id
    if is_creator:
        battle.creator_ready = not battle.creator_ready
    elif session["user_id"] == battle.opponent_id:
        battle.opponent_ready = not battle.opponent_ready

    # Start battle if both are ready
    if battle.creator_ready and battle.opponent_ready and battle.status == "ready":
        battle.status = "in_progress"
        battle.start_time = datetime.utcnow()
        minutes = parse_time_limit(battle.time_limit)
        battle.end_time = battle.start_time + timedelta(minutes=minutes)

    db.session.commit()
    return jsonify({"success": True})


@challenges.route("/battle/<int:battle_id>/api/submit", methods=["POST"])
@login_required
def submit_code(battle_id):
    battle = Battle.query.get_or_404(battle_id)

    if battle.status != "in_progress":
        return jsonify({"error": "Battle is not in progress"}), 400

    data = request.json
    code = data.get("code", "")

    # Save code and mark as submitted
    is_creator = session["user_id"] == battle.user_id
    if is_creator:
        battle.creator_code = code
        battle.creator_submitted = True
    elif session["user_id"] == battle.opponent_id:
        battle.opponent_code = code
        battle.opponent_submitted = True

    # Check if BOTH players have submitted
    if battle.creator_submitted and battle.opponent_submitted:
        battle.status = "in_review"
        battle.end_time = datetime.utcnow()
        battle.review_end_time = datetime.utcnow() + timedelta(minutes=30)

    db.session.commit()
    return jsonify({"success": True, "status": battle.status})


@challenges.route("/battle/<int:battle_id>/review")
def review(battle_id):
    """Battle review route"""
    battle = Battle.query.get_or_404(battle_id)

    if battle.status in ["waiting", "ready", "in_progress"]:
        flash("This battle is not ready for review yet.", "warning")
        return redirect(url_for("main.battles"))

    # Check if review time is up and we need to declare a winner
    if (
        battle.status == "in_review"
        and battle.review_end_time
        and datetime.utcnow() > battle.review_end_time
    ):
        battle.status = "completed"
        creator_votes = BattleVote.query.filter_by(
            battle_id=battle.id, voted_for_id=battle.user_id
        ).count()
        opponent_votes = BattleVote.query.filter_by(
            battle_id=battle.id, voted_for_id=battle.opponent_id
        ).count()

        if creator_votes > opponent_votes:
            battle.winner_id = battle.user_id
        elif opponent_votes > creator_votes:
            battle.winner_id = battle.opponent_id
        else:
            flash("The battle ended in a tie, so creator wins!", "info")
            battle.winner_id = battle.user_id
        db.session.commit()

    creator_votes = BattleVote.query.filter_by(
        battle_id=battle.id, voted_for_id=battle.user_id
    ).count()
    opponent_votes = BattleVote.query.filter_by(
        battle_id=battle.id, voted_for_id=battle.opponent_id
    ).count()

    user_vote = None
    if "user_id" in session:
        vote = BattleVote.query.filter_by(
            battle_id=battle.id, user_id=session["user_id"]
        ).first()
        if vote:
            user_vote = vote.voted_for_id

    # Time left for voting
    review_time_left = 0
    if battle.status == "in_review" and battle.review_end_time:
        review_time_left = max(
            0, (battle.review_end_time - datetime.utcnow()).total_seconds()
        )

    comments = battle.comments.order_by(BattleComment.created_at.asc()).all()

    return render_template(
        "main/review.html",
        battle=battle,
        creator_votes=creator_votes,
        opponent_votes=opponent_votes,
        user_vote=user_vote,
        review_time_left=review_time_left,
        comments=comments,
    )


@challenges.route("/battle/<int:battle_id>/vote", methods=["POST"])
@login_required
def vote_battle(battle_id):
    battle = Battle.query.get_or_404(battle_id)

    if battle.status != "in_review":
        return jsonify({"error": "Voting is closed."}), 400

    data = request.json
    voted_for_id = data.get("voted_for_id")

    if voted_for_id not in [battle.user_id, battle.opponent_id]:
        return jsonify({"error": "Invalid vote."}), 400

    existing_vote = BattleVote.query.filter_by(
        user_id=session["user_id"], battle_id=battle.id
    ).first()
    if existing_vote:
        existing_vote.voted_for_id = voted_for_id
    else:
        new_vote = BattleVote(
            user_id=session["user_id"], battle_id=battle.id, voted_for_id=voted_for_id
        )
        db.session.add(new_vote)

    db.session.commit()
    return jsonify({"success": True})


@challenges.route("/battle/<int:battle_id>/comment", methods=["POST"])
@login_required
def add_battle_comment(battle_id):
    data = request.json
    content = data.get("content")
    if not content or not content.strip():
        return jsonify({"error": "Comment can't be empty"}), 400

    new_comment = BattleComment(
        content=content.strip(), user_id=session["user_id"], battle_id=battle_id
    )
    db.session.add(new_comment)
    db.session.commit()

    return jsonify(
        {
            "id": new_comment.id,
            "content": new_comment.content,
            "author": new_comment.author.username,
            "created_at": "Just now",
            "avatar_letter": new_comment.author.username[:2].upper(),
        }
    )
