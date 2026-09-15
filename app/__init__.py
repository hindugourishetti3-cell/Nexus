from flask import Flask, render_template
from .config import Config
from .database import db
from .models import User, Workspace, Page
from .auth import auth
from flask_login import LoginManager, login_required, current_user
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

        user_workspaces = Workspace.query.filter_by(
            owner_id=current_user.id
        ).all()

        workspace_count = len(user_workspaces)

        page_count = Page.query.join(
            Workspace,
            Page.workspace_id == Workspace.id
        ).filter(
            Workspace.owner_id == current_user.id
        ).count()

        recent_pages = Page.query.join(
            Workspace,
            Page.workspace_id == Workspace.id
        ).filter(
            Workspace.owner_id == current_user.id
        ).order_by(
            Page.created_at.desc()
        ).limit(5).all()

        return render_template(
            "dashboard.html",
            workspace_count=workspace_count,
            page_count=page_count,
            recent_pages=recent_pages,
            workspaces=user_workspaces
        )

    return app