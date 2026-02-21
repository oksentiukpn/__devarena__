from datetime import datetime, timedelta

from flask import flash, jsonify, redirect, render_template, request, session, url_for

from app import db
from app.auth.utils import login_required
from app.challenges import challenges
from app.main.form import BattleForm
from app.models import Battle, User


def parse_time_limit(limit_str):
    if "min" in limit_str:
        return int(limit_str.split()[0])
    elif "hour" in limit_str:
        return int(limit_str.split()[0]) * 60
    return 60  # Default 60 mins


@challenges.route("/battle/create", methods=["GET", "POST"])
@login_required
def create_battle():
    form = BattleForm()

    if form.validate_on_submit():
        # Clean tags logic (similar to Post logic)
        raw_tags = [
            tag
            for tag in form.tags.data.replace("#", " ").split()
            if tag not in ("", " ")
        ]
        # Joining with comma to ensure template compatibility: post.tags.split(',')
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
            flash("Battle created successfully!", "success")
            # Redirecting to feed for now, or a specific battles list if it exists
            return redirect(url_for("main.battles"))
        except Exception as e:
            db.session.rollback()
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
        battle.status = "ready"  # Move from waiting to ready state
        db.session.commit()
        flash("Joined the battle!", "success")

    elif battle.opponent_id != session["user_id"]:
        flash("This battle is already full.", "danger")
        return redirect(url_for("main.battles"))

    return redirect(url_for("challenges.arena", battle_id=battle.id))


@challenges.route("/battle/<int:battle_id>/arena")
@login_required
def arena(battle_id):
    battle = Battle.query.get_or_404(battle_id)

    # Security check: only participants can view the arena
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

    db.session.commit()
    return jsonify({"success": True, "status": battle.status})
