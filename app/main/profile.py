# from flask import request
from app import db
from app.auth.utils import login_required

@app.post("/profile/update")
@login_required
def update_profile():
    username = request.form.get("username")
    bio = request.form.get("bio")

    current_user.username = username
    current_user.bio = bio

    db.session.commit()
    return redirect("/settings")
