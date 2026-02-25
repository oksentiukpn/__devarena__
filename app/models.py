"""
Defining models for database
"""

from datetime import datetime, timedelta

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

    points = db.Column(db.Integer, default=0, server_default="0", nullable=False)
    subscribed_to_daily_prompt = db.Column(db.Boolean, default=True)



    points = db.Column(db.Integer, default=0, nullable=False)


    rating = db.Column(db.Integer, default=1000, nullable=False)
    wins = db.Column(db.Integer, default=0, nullable=False)
    losses = db.Column(db.Integer, default=0, nullable=False)
    total_battles = db.Column(db.Integer, default=0, nullable=False)

    @staticmethod
    def update_battle_stats(winner_id, loser_id):
        winner = User.query.get(winner_id)
        loser = User.query.get(loser_id)

        if winner and loser:
            winner.rating += 25
            winner.wins += 1
            winner.total_battles += 1

            loser.rating = max(0, loser.rating - 10)
            loser.losses += 1
            loser.total_battles += 1

            db.session.commit()

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

    def update_popularity_points(self):
        """
        Calculates popularity-based points for the author:
        1 reaction = 5 points, 1 comment = 10 points.

        Recomputes the author's total points balance from all of their posts
        to avoid double-counting when this method is called multiple times.
        """

        total_points = 0

        # Recalculate total popularity points across all posts by this author
        for post in self.author.posts:
            if hasattr(post.reactions, "count"):
                count_reactions = post.reactions.count()
            else:
                count_reactions = len(list(post.reactions))

            count_comments = len(post.comments)
            total_points += (count_reactions * 5) + (count_comments * 10)

        self.author.points = total_points
        db.session.commit()


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
    opponent_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    author = db.relationship(
        "User", foreign_keys=[user_id], backref="battles", lazy=True
    )
    status = db.Column(
        db.String(20), default="waiting"
    )  # waiting, ready, in_progress, in_review, completed

    creator_ready = db.Column(db.Boolean, default=False)
    opponent_ready = db.Column(db.Boolean, default=False)

    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)

    creator_code = db.Column(db.Text, nullable=True)
    opponent_code = db.Column(db.Text, nullable=True)

    opponent = db.relationship(
        "User", foreign_keys=[opponent_id], backref="joined_battles"
    )
    creator_submitted = db.Column(db.Boolean, default=False)
    opponent_submitted = db.Column(db.Boolean, default=False)
    review_end_time = db.Column(db.DateTime, nullable=True)
    winner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    winner = db.relationship("User", foreign_keys=[winner_id])

    def __repr__(self):
        return f"Battle('{self.title}', '{self.status}')"


class BattleVote(db.Model):
    __tablename__ = "battle_votes"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    battle_id = db.Column(db.Integer, db.ForeignKey("battles.id"), nullable=False)
    voted_for_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Ensure a user can only vote once per battle
    __table_args__ = (
        db.UniqueConstraint("user_id", "battle_id", name="unique_user_battle_vote"),
    )


class BattleComment(db.Model):
    __tablename__ = "battle_comments"
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    battle_id = db.Column(db.Integer, db.ForeignKey("battles.id"), nullable=False)

    author = db.relationship("User", backref="battle_comments", lazy=True)
    battle = db.relationship(
        "Battle",
        backref=db.backref("comments", lazy="dynamic", cascade="all, delete-orphan"),
    )
