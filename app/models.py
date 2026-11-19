
from .database import db
from datetime import datetime
from flask_login import UserMixin


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Workspace(db.Model):
    __tablename__ = "workspaces"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    owner_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )


class Page(db.Model):
    __tablename__ = "page"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    workspace_id = db.Column(
        db.Integer,
        db.ForeignKey("workspaces.id"),
        nullable=False
    )

    parent_id = db.Column(
        db.Integer,
        db.ForeignKey("page.id"),
        nullable=True
    )

    children = db.relationship(
        "Page",
        backref=db.backref("parent", remote_side=[id]),
        cascade="all, delete-orphan"
    )


class PageVersion(db.Model):
    __tablename__ = "page_versions"

    id = db.Column(db.Integer, primary_key=True)

    page_id = db.Column(
        db.Integer,
        db.ForeignKey("page.id"),
        nullable=False
    )

    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    page = db.relationship(
        "Page",
        backref=db.backref(
            "versions",
            lazy=True,
            cascade="all, delete-orphan"
        )
    )
