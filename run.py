"""
Runner
"""

from os import environ
from time import sleep

import requests
from app import create_app
from app.models import User
from flask import current_app, render_template
from itsdangerous import URLSafeSerializer

app = create_app()


@app.cli.command("send-daily-prompt")
def send_daily_prompt():
    """Send email to all users with daily prompt"""
    users = User.query.filter_by(subscribed_to_daily_prompt=True).all()
    api_key = environ.get("EMAIL_API_KEY")

    if not api_key:
        current_app.logger.error("EMAIL_API_KEY is not found.")
        print("Error: EMAIL_API_KEY is not found.")
        return
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    ser = URLSafeSerializer(app.config["SECRET_KEY"])

    success_count = 0
    for user in users:
        token = ser.dumps(user.id, salt="unsubscribe-daily-prompt")
        unsubscribe_url = f"https://devarena.pp.ua/unsubscribe/{token}"
        html_content = render_template(
            "email/daily_prompt.html", user=user, unsubscribe_url=unsubscribe_url
        )

        payload = {
            "from": "DevArena <notifications@devarena.pp.ua>",
            "to": [user.email],
            "subject": "Time to Code!",
            "html": html_content,
            "headers": {
                "List-Unsubscribe": f"<{unsubscribe_url}>",
                "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
            },
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            success_count += 1
        except Exception as e:
            current_app.logger.error(f"Failed sending to user {user.email}: {e}")
            print(f"Failed sending to user {user.email}: {e}")
        sleep(1)
    current_app.logger.info(f"Successfully sent {success_count}/{len(users)} messages.")
    print(f"Successfully sent {success_count}/{len(users)} messages.")


@app.cli.command("send-prompt-to")
def send_prompt_to():
    """Send email to specific user with daily prompt"""
    email = input("Enter user email: ")
    user = User.query.filter_by(email=email).first()
    if not user:
        print("User not found.")
        return

    api_key = environ.get("EMAIL_API_KEY")
    if not api_key:
        current_app.logger.error("EMAIL_API_KEY is not found.")
        print("Error: EMAIL_API_KEY is not found.")
        return

    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    ser = URLSafeSerializer(app.config["SECRET_KEY"])
    token = ser.dumps(user.id, salt="unsubscribe-daily-prompt")
    unsubscribe_url = f"https://devarena.pp.ua/unsubscribe/{token}"
    html_content = render_template(
        "email/daily_prompt.html", user=user, unsubscribe_url=unsubscribe_url
    )

    payload = {
        "from": "DevArena <notifications@devarena.pp.ua>",
        "to": [user.email],
        "subject": "Time to Code!",
        "html": html_content,
        "headers": {
            "List-Unsubscribe": f"<{unsubscribe_url}>",
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
        },
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        current_app.logger.info(f"Successfully sent to {user.email}")
        print(f"Successfully sent to {user.email}")
    except Exception as e:
        current_app.logger.error(f"Failed sending to {user.email}: {e}")
        print(f"Failed sending to {user.email}: {e}")


if __name__ == "__main__":
    debug_mode = environ.get("FLASK_DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", debug=debug_mode)
