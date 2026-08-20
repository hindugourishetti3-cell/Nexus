from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from .database import db
from .models import Workspace, Page

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

    pages = Page.query.filter_by(
        workspace_id=selected_workspace.id
    ).all()

    return render_template(
        "workspace_detail.html",
        workspace=selected_workspace,
        pages=pages
    )
@workspace.route("/workspace/<int:workspace_id>/page/create", methods=["GET", "POST"])
@login_required
def create_page(workspace_id):

    selected_workspace = Workspace.query.get_or_404(workspace_id)

    if request.method == "POST":

        title = request.form["title"]
        content = request.form["content"]

        new_page = Page(
            title=title,
            content=content,
            workspace_id=selected_workspace.id
        )

        db.session.add(new_page)
        db.session.commit()

        return redirect(
            url_for(
                "workspace.workspace_detail",
                workspace_id=selected_workspace.id
            )
        )

    return render_template(
        "create_page.html",
        workspace=selected_workspace
    )
@workspace.route("/page/<int:page_id>")
@login_required
def view_page(page_id):

    page = Page.query.get_or_404(page_id)

    return render_template(
        "page.html",
        page=page
    )
@workspace.route("/page/<int:page_id>/edit", methods=["GET", "POST"])
@login_required
def edit_page(page_id):

    page = Page.query.get_or_404(page_id)

    if request.method == "POST":

        page.title = request.form["title"]
        page.content = request.form["content"]

        db.session.commit()

        return redirect(
            url_for(
                "workspace.view_page",
                page_id=page.id
            )
        )

    return render_template(
        "create_page.html",
        page=page
    )
@workspace.route("/page/<int:page_id>/delete", methods=["POST"])
@login_required
def delete_page(page_id):

    page = Page.query.get_or_404(page_id)

    workspace_id = page.workspace_id

    db.session.delete(page)
    db.session.commit()

    return redirect(
        url_for(
            "workspace.workspace_detail",
            workspace_id=workspace_id
        )
    )
@workspace.route("/workspace/<int:workspace_id>/edit", methods=["GET", "POST"])
@login_required
def edit_workspace(workspace_id):

    selected_workspace = Workspace.query.get_or_404(workspace_id)

    if request.method == "POST":

        selected_workspace.name = request.form["name"]
        selected_workspace.description = request.form["description"]

        db.session.commit()

        return redirect(
            url_for(
                "workspace.workspace_detail",
                workspace_id=selected_workspace.id
            )
        )

    return render_template(
        "edit_workspace.html",
        workspace=selected_workspace
    )
@workspace.route("/workspace/<int:workspace_id>/delete", methods=["POST"])
@login_required
def delete_workspace(workspace_id):

    selected_workspace = Workspace.query.get_or_404(workspace_id)

    Page.query.filter_by(
        workspace_id=selected_workspace.id
    ).delete()

    db.session.delete(selected_workspace)
    db.session.commit()

    return redirect(url_for("workspace.workspaces"))
@workspace.route("/search")
@login_required
def search():

    query = request.args.get("q", "").strip()

    workspaces = []
    pages = []

    if query:

        workspaces = Workspace.query.filter(
            Workspace.owner_id == current_user.id,
            Workspace.name.ilike(f"%{query}%") |
            Workspace.description.ilike(f"%{query}%")
        ).all()

        pages = Page.query.join(
            Workspace,
            Page.workspace_id == Workspace.id
        ).filter(
            Workspace.owner_id == current_user.id,
            Page.title.ilike(f"%{query}%") |
            Page.content.ilike(f"%{query}%")
        ).all()

    return render_template(
        "search.html",
        query=query,
        workspaces=workspaces,
        pages=pages
    )