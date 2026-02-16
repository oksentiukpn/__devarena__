"""
Defining models for database
"""

from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from app import db


def load_user(user_id):
    """Loading user func"""
    return User.query.get(int(user_id))


class Reaction(db.Model):
    """
    Reaction model
    This model is used to store reactions to posts.
    Example:
        Reaction(emoji="👍", user_id=1, post_id=1)
    """

    __tablename__ = "reactions"
    id = db.Column(db.Integer, primary_key=True)
    emoji = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)

    # Only one user one emoji
    __table_args__ = (
        db.UniqueConstraint(
            "user_id", "post_id", "emoji", name="unique_user_post_emoji"
        ),
    )


class User(db.Model):
    """
    User model
    This model is used to store users.
    Example:
        User(username="John", email="john@example.com", password="password"
    """

    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(255), nullable=False, default="default.jpg")
    password_hash = db.Column(db.String(256), nullable=True)  # hashed of course
    languages = db.Column(db.String(1024), nullable=True)

    def set_password(self, password: str) -> None:
        """Set password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Check password"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class Post(db.Model):
    """
    Post model
    This model is used to store posts.
    Example:
        Post(title="Hello World", description="This is a post", language="python",
            code="print('Hello World')", tags="python, hello world, programming",
            feedback_type="code", visibility="public", created_at=datetime.utcnow(),
            user_id=1)
    """

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
    comments = db.relationship(
        "Comment",
        backref="post",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="Comment.created_at.asc()",
    )

    @property
    def reactions_summary(self):
        """Get reactions summary"""
        summary = {}
        for reaction in self.reactions:
            if reaction.emoji not in summary:
                summary[reaction.emoji] = {"count": 0, "user_ids": set()}
            summary[reaction.emoji]["count"] += 1
            summary[reaction.emoji]["user_ids"].add(reaction.user_id)
        return summary

    def __repr__(self):
        return f"Post('{self.title}', '{self.created_at}')"


class Comment(db.Model):
    """
    Comment model
    This model is used to store comments.
    Example:
        Comment(content="This is a comment", created_at=datetime.utcnow(), user_id=1,
            post_id=1)
    """

    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)

    author = db.relationship("User", backref="comments", lazy=True)


class Battle(db.Model):
    """
    Battle model
    Stores coding challenges created by users.
    """

    __tablename__ = "battles"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    time_limit = db.Column(db.String(20), nullable=False)
    language = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    tags = db.Column(db.String(200))
    visibility = db.Column(db.String(20), default="public", nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationship
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    author = db.relationship("User", backref="battles", lazy=True)

    def __repr__(self):
        return f"Battle('{self.title}', '{self.difficulty}')"
