from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from app import db


def load_user(user_id):
    return User.query.get(int(user_id))


class Reaction(db.Model):
    __tablename__ = "reactions"
    id = db.Column(db.Integer, primary_key=True)
    emoji = db.Column(db.String(10), nullable=False)  # Сам символ емодзі
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)

    # Забезпечуємо, щоб один юзер не міг поставити два однакових емодзі на один пост
    __table_args__ = (
        db.UniqueConstraint(
            "user_id", "post_id", "emoji", name="unique_user_post_emoji"
        ),
    )


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(255), nullable=False, default="default.jpg")
    password_hash = db.Column(db.String(256), nullable=True)  # hashed of course
    languages = db.Column(db.String(1024), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class Post(db.Model):
    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(50), nullable=False)
    code = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(200))
    feedback_type = db.Column(db.String(200))  # Stored as comma-separated string
    visibility = db.Column(db.String(20), default="public", nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Foreign Key linking to User
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    author = db.relationship("User", backref="posts", lazy=True)
    reactions = db.relationship(
        "Reaction", backref="post", lazy="dynamic", cascade="all, delete-orphan"
    )

    @property
    def reactions_summary(self):
        summary = {}
        for reaction in self.reactions:
            if reaction.emoji not in summary:
                summary[reaction.emoji] = {"count": 0, "user_ids": set()}
            summary[reaction.emoji]["count"] += 1
            summary[reaction.emoji]["user_ids"].add(reaction.user_id)
        return summary

    def __repr__(self):
        return f"Post('{self.title}', '{self.created_at}')"
