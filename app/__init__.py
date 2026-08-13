from flask import Flask
from .config import Config
from .database import db
from .models import User
from .auth import auth
from flask_login import LoginManager


login_manager = LoginManager()


def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)

    login_manager.init_app(app)

    login_manager.login_view = "auth.register"

    app.register_blueprint(auth)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        db.create_all()

    @app.route("/")
    def home():
        return "<h1>Nexus is Alive 🚀</h1>"

    return app