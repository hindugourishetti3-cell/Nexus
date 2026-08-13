from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user
from .database import db
from .models import User

auth = Blueprint("auth", __name__)


@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            return "Username or email already exists"

        password_hash = generate_password_hash(password)

        user = User(
            username=username,
            email=email,
            password_hash=password_hash
        )

        db.session.add(user)
        db.session.commit()

        login_user(user)

        return redirect(url_for("home"))

    return render_template("register.html")