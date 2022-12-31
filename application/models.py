from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
import enum
from sqlalchemy import Enum, DateTime


class StreamType(enum.Enum):
    video = 1
    rtsp = 2
    clip = 3


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    areas = db.relationship("Area")
    medias = db.relationship("Media")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    users = db.relationship('User')
    time_created = db.Column(db.DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=func.now())


class Area(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    description = db.Column(db.String(300), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    long = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    medias = db.relationship('Media')
    time_created = db.Column(DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(DateTime(timezone=True), onupdate=func.now())


class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    path = db.Column(db.String(1000), nullable=False, unique=True)
    media_type = db.Column(Enum(StreamType))
    lat = db.Column(db.Float, nullable=False)
    long = db.Column(db.Float, nullable=False)
    area_id = db.Column(db.Integer, db.ForeignKey('area.id'), nullable=False)
    area = db.relationship('Area', back_populates="medias")
    user = db.relationship('User', back_populates='medias')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    time_created = db.Column(DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
