from flask import Flask
from .config import Config
from .database import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.route("/")
    def home():
        return "<h1>Nexus is Alive 🚀</h1>"

    return app