from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()   # ✅ Correct place — no import from app



class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)  # client / worker / admin
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    aadhar = db.Column(db.String(20), nullable=False)
    skills = db.Column(db.Text)
    is_approved = db.Column(db.Boolean, default=False)
    bio = db.Column(db.Text, default="")
    profile_image = db.Column(db.String(200), default="default.png")
    phone = db.Column(db.String(30), nullable=True)
    govt_id_image = db.Column(db.String(255), nullable=True)

    # relationships
    # ratings where this user is the receiver (worker/client)
    ratings_received = db.relationship("Rating", backref="recipient", foreign_keys="Rating.recipient_id", lazy="dynamic")
    ratings_given = db.relationship("Rating", backref="author", foreign_keys="Rating.author_id", lazy="dynamic")

    def avg_rating(self):
        """Return float average (rounded to 1 decimal) or None"""
        rows = self.ratings_received.all()
        if not rows:
            return None
        total = sum(r.score for r in rows)
        avg = total / len(rows)
        return round(avg, 1)

    def rating_count(self):
        return self.ratings_received.count()
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Hire(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    worker_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'))
    status = db.Column(db.String(20), default="pending")

    client = db.relationship("User", foreign_keys=[client_id])
    worker = db.relationship("User", foreign_keys=[worker_id])
    job = db.relationship("Job", foreign_keys=[job_id])


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(200), nullable=True)  # ✅ Add this
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    client = db.relationship("User", backref=db.backref("jobs_posted", lazy='dynamic'), foreign_keys=[client_id])
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_open = db.Column(db.Boolean, default=True)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    worker_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # ✅ Add this
    status = db.Column(db.String(20), default='applied')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    worker = db.relationship("User", foreign_keys=[worker_id])
    client = db.relationship("User", foreign_keys=[client_id])
    job = db.relationship("Job", foreign_keys=[job_id])


class Message(db.Model):
    __tablename__ = 'message'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)


class Rating(db.Model):
    __tablename__ = 'rating'
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # who receives the rating
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)     # who gave the rating
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=True)
    score = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    __tablename__ = 'notification'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
