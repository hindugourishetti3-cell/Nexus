from flask import Flask
from .config import Config
from .database import db
from .models import User,Workspace
from .auth import auth
from flask_login import LoginManager, login_required
from .workspace import workspace


login_manager = LoginManager()


def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)

    login_manager.init_app(app)

    login_manager.login_view = "auth.login"

    app.register_blueprint(auth)
    app.register_blueprint(workspace)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        db.create_all()

    @app.route("/")
    def home():
        return "<h1>Nexus is Alive 🚀</h1>"

    @app.route("/dashboard")
    @login_required
    def dashboard():
        return "<h1>Welcome to your Nexus Dashboard 🚀</h1>"
    return app