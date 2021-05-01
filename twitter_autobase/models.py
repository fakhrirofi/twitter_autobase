from . import db
from . import login
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    autobase = db.relationship('Autobase', backref='owner', lazy='dynamic')

    def __repr__(self):
        return f'User <{self.username}>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Autobase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    screen_name = db.Column(db.String(64), index=True, unique=True)
    consumer_key = db.Column(db.String(64))
    consumer_secret = db.Column(db.String(64))
    access_key = db.Column(db.String(64))
    access_secret = db.Column(db.String(64))

    def __repr__(self):
        return f'Autobase <{self.screen_name}>'
