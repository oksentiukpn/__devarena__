"""
Runner
"""

import socket
from os import environ

from app import create_app, mail
from app.models import User
from flask import render_template
from flask_mail import Message

# ---------------------------------- #
# IPV4 Patch to ignore IPV6
old_getaddrinfo = socket.getaddrinfo


def new_getaddrinfo(*args, **kwargs):
    responses = old_getaddrinfo(*args, **kwargs)
    return [response for response in responses if response[0] == socket.AF_INET]


socket.getaddrinfo = new_getaddrinfo
# ---------------------------------- #

app = create_app()


@app.cli.command("send-daily-prompt")
def send_daily_prompt():
    """Send email to all users with daily prompt"""
    users = User.query.all()

    with mail.connect() as conn:
        for user in users:
            msg = Message("Time to Code!", recipients=[user.email])
            msg.body = f"Hello, {user.username}!\n\nIt's your daily DevArena prompt. Check our platform and post your code!\n\nhttps://devarena.pp.ua/post"
            msg.html = render_template("email/daily_prompt.html", user=user)
            try:
                conn.send(msg)
            except Exception as e:
                print(f"Failed sending to {user.email}: {e}")

    print(f"Sent {len(users)} messages.")


if __name__ == "__main__":
    debug_mode = environ.get("FLASK_DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", debug=debug_mode)
