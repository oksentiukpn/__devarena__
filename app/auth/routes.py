from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError

from app import db, oauth
from app.models import User

auth = Blueprint("auth", __name__)


@auth.route("/login/google")
def google_login():
    redirect_uri = url_for("auth.google_callback", _external=True)

    return oauth.google.authorize_redirect(redirect_uri.replace("http://", "https://"))


@auth.route("/auth/google/callback")
def google_callback():
    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get("userinfo")

        email = user_info["email"]
        name = user_info.get("name", email.split("@")[0])

        # Checking if he already exists
        user = User.query.filter_by(email=email).first()

        if not user:
            # Creating new
            base_username = name.replace(" ", "_").lower()
            username = base_username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}_{counter}"
                counter += 1
            user = User(
                username=username,
                email=email,
                image_file=user_info.get("picture", "default.jpg"),
            )

            db.session.add(user)
            db.session.commit()

        session["user_id"] = user.id
        flash("Successfull login with Google.", "success")
        return redirect(url_for("main.home"))
    except Exception as e:
        flash(f"Failed Authentification: {e}", "danger")
        return redirect(url_for("auth.login"))


@auth.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("main.home"))

    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        # ///
        # Future data validation
        for value in (username, email, password):
            if not value or len(value) < 5:
                return f"{value}: is invalid"

        # ///
        user = User(username=username, email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash(f"Account with name <{username}> was successfully created!", "success")
        return redirect(url_for("auth.login"))
    # if not sending data, just give html
    return render_template("auth/register.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("main.home"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session["user_id"] = user.id
            flash("Successfull login!", "success")
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("main.home"))

        flash("Login failed: Invalid password or email", "danger")

    # if not sending data, just give html
    return render_template("auth/login.html")


@auth.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Successfull logout", "success")
    return redirect(url_for("main.home"))
