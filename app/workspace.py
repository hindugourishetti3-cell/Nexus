from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from .database import db
from .models import Workspace

workspace = Blueprint("workspace", __name__)


@workspace.route("/workspaces")
@login_required
def workspaces():
    user_workspaces = Workspace.query.filter_by(
        owner_id=current_user.id
    ).all()

    return render_template(
        "workspaces.html",
        workspaces=user_workspaces
    )


@workspace.route("/workspace/create", methods=["GET", "POST"])
@login_required
def create_workspace():

    if request.method == "POST":

        name = request.form["name"]
        description = request.form["description"]

        new_workspace = Workspace(
            name=name,
            description=description,
            owner_id=current_user.id
        )

        db.session.add(new_workspace)
        db.session.commit()

        return redirect(url_for("workspace.workspaces"))

    return render_template("create_workspace.html")

@workspace.route("/workspace/<int:workspace_id>")
@login_required
def workspace_detail(workspace_id):

    selected_workspace = Workspace.query.get_or_404(workspace_id)

    return render_template(
        "workspace_detail.html",
        workspace=selected_workspace
    )