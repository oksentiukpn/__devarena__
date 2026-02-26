import re

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

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
            current_app.logger.info(
                f"New user created: {email} with username {username}"
            )

        session["user_id"] = user.id
        flash("Successfull login with Google.", "success")
        return redirect(url_for("main.home"))
    except Exception as e:
        current_app.logger.error(f"Google login failed: {e}")
        flash(f"Failed Authentification: {e}", "danger")
        return redirect(url_for("auth.login"))


@auth.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        flash("You are already logged in.", "info")
        return redirect(url_for("main.home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        if any(letter.isupper() for letter in email):
            flash("Email must be in lowercase.", "danger")
            return render_template("auth/sign_up.html", username=username, email=email)
        password = request.form.get("password", "")
        # ///
        # data validation
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_regex, email):
            flash("Invalid email address.", "danger")
            return render_template("auth/sign_up.html", username=username, email=email)

        if not re.match(r"^\w+$", username):
            flash(
                "Username can only contain letters, numbers and underscores.", "danger"
            )
            return render_template("auth/sign_up.html", username=username, email=email)

        for value in (username, email, password):
            if not value or len(value) < 8:
                flash("All fields must be at least 8 characters long.", "danger")
                return render_template(
                    "auth/sign_up.html", username=username, email=email
                )

        # Check if email or username already exists
        if User.query.filter_by(email=email).first():
            flash("Email already exists. Please choose a different one.", "danger")
            return render_template("auth/sign_up.html", username=username, email=email)
        if User.query.filter_by(username=username).first():
            flash("Username already exists. Please choose a different one.", "danger")
            return render_template("auth/sign_up.html", username=username, email=email)

        # ///
        user = User(username=username, email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        current_app.logger.info(
            f"New user registered: {email} with username {username}"
        )
        flash(f"Account with name <{username}> was successfully created!", "success")
        return render_template("auth/login.html", email=email)
    # if not sending data, just give html
    return render_template("auth/sign_up.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("main.home"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()

        if user and not user.password_hash:
            flash(
                "This account has no password and was registered via Google. Please use Google login.",
                "danger",
            )
            return redirect(url_for("auth.login"), email=email)

        if user and user.check_password(password):
            session["user_id"] = user.id
            flash("Successfull login!", "success")
            current_app.logger.info(f"User logged in: {email}")
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("main.home"))
        current_app.logger.warning(f"Failed login attempt for email: {email}")
        flash("Login failed: Invalid password or email", "danger")
        return redirect(url_for("auth.login"), email=email)

    # if not sending data, just give html
    return render_template("auth/login.html")


@auth.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Successfull logout", "success")
    return redirect(url_for("main.home"))
