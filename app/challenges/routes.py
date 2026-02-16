from flask import flash, redirect, render_template, session, url_for

from app import db
from app.auth.utils import login_required
from app.challenges import challenges
from app.main.form import BattleForm
from app.models import Battle


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

        new_battle = Battle(
            title=form.title.data,
            description=form.description.data,
            time_limit=form.time_limit.data,
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
            return redirect(url_for("main.feed_page"))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred creating the battle: {e}", "danger")

    return render_template("main/create_battle.html", form=form)
