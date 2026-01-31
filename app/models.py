from werkzeug.security import check_password_hash, generate_password_hash

from app import db


def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(
        db.String(255), nullable=False, default="default.jpg")
    password_hash = db.Column(
        db.String(256), nullable=True)  # hashed of course

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"
