
from flask import Blueprint, render_template, request, redirect, url_for
import markdown
import bleach
from flask_login import login_required, current_user
from .database import db
from .models import Workspace, Page

workspace = Blueprint("workspace", __name__)


# Helper: retrieve only the logged-in user's workspace
def get_owned_workspace(workspace_id):
    return Workspace.query.filter_by(
        id=workspace_id,
        owner_id=current_user.id
    ).first_or_404()


# Helper: retrieve only pages belonging to the logged-in user
def get_owned_page(page_id):
    return Page.query.join(
        Workspace,
        Page.workspace_id == Workspace.id
    ).filter(
        Page.id == page_id,
        Workspace.owner_id == current_user.id
    ).first_or_404()


# Display all workspaces belonging to the current user
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


# Create a new workspace
@workspace.route("/workspace/create", methods=["GET", "POST"])
@login_required
def create_workspace():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            return render_template("create_workspace.html")

        new_workspace = Workspace(
            name=name,
            description=description,
            owner_id=current_user.id
        )

        db.session.add(new_workspace)
        db.session.commit()

        return redirect(url_for("workspace.workspaces"))

    return render_template("create_workspace.html")


# Display a workspace and its pages
@workspace.route("/workspace/<int:workspace_id>")
@login_required
def workspace_detail(workspace_id):
    selected_workspace = get_owned_workspace(workspace_id)

    pages = Page.query.filter_by(
        workspace_id=selected_workspace.id
    ).all()

    return render_template(
        "workspace_detail.html",
        workspace=selected_workspace,
        pages=pages
    )


# Create a page inside an owned workspace
@workspace.route(
    "/workspace/<int:workspace_id>/page/create",
    methods=["GET", "POST"]
)
@login_required
def create_page(workspace_id):
    selected_workspace = get_owned_workspace(workspace_id)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "")

        if not title:
            return render_template(
                "create_page.html",
                workspace=selected_workspace
            )

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


# View an owned page
@workspace.route("/page/<int:page_id>")
@login_required
def view_page(page_id):
    page = get_owned_page(page_id)

    raw_html = markdown.markdown(
        page.content or "",
        extensions=["fenced_code", "tables"]
    )

    allowed_tags = [
        "p", "br", "strong", "em", "del",
        "h1", "h2", "h3", "h4", "h5", "h6",
        "ul", "ol", "li", "blockquote",
        "pre", "code",
        "table", "thead", "tbody", "tr", "th", "td",
        "a", "hr"
    ]

    allowed_attributes = {
        "a": ["href", "title"],
        "code": ["class"],
        "pre": ["class"]
    }

    rendered_content = bleach.clean(
        raw_html,
        tags=allowed_tags,
        attributes=allowed_attributes,
        protocols=["http", "https", "mailto"],
        strip=True
    )

    return render_template(
        "page.html",
        page=page,
        rendered_content=rendered_content
    )


# Edit an owned page
@workspace.route("/page/<int:page_id>/edit", methods=["GET", "POST"])
@login_required
def edit_page(page_id):
    page = get_owned_page(page_id)

    if request.method == "POST":
        title = request.form.get("title", "").strip()

        if not title:
            return render_template(
                "create_page.html",
                page=page,
                workspace=Workspace.query.get_or_404(page.workspace_id)
            )

        page.title = title
        page.content = request.form.get("content", "")

        db.session.commit()

        return redirect(
            url_for(
                "workspace.view_page",
                page_id=page.id
            )
        )

    return render_template(
        "create_page.html",
        page=page,
        workspace=Workspace.query.get_or_404(page.workspace_id)
    )


# Delete an owned page
@workspace.route("/page/<int:page_id>/delete", methods=["POST"])
@login_required
def delete_page(page_id):
    page = get_owned_page(page_id)

    workspace_id = page.workspace_id

    db.session.delete(page)
    db.session.commit()

    return redirect(
        url_for(
            "workspace.workspace_detail",
            workspace_id=workspace_id
        )
    )


# Edit an owned workspace
@workspace.route(
    "/workspace/<int:workspace_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def edit_workspace(workspace_id):
    selected_workspace = get_owned_workspace(workspace_id)

    if request.method == "POST":
        name = request.form.get("name", "").strip()

        if not name:
            return render_template(
                "edit_workspace.html",
                workspace=selected_workspace
            )

        selected_workspace.name = name
        selected_workspace.description = request.form.get(
            "description", ""
        ).strip()

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


# Delete an owned workspace and its pages
@workspace.route(
    "/workspace/<int:workspace_id>/delete",
    methods=["POST"]
)
@login_required
def delete_workspace(workspace_id):
    selected_workspace = get_owned_workspace(workspace_id)

    Page.query.filter_by(
        workspace_id=selected_workspace.id
    ).delete()

    db.session.delete(selected_workspace)
    db.session.commit()

    return redirect(url_for("workspace.workspaces"))


# Search only the current user's content
@workspace.route("/search")
@login_required
def search():
    query = request.args.get("q", "").strip()

    workspaces = []
    pages = []

    if query:
        workspaces = Workspace.query.filter(
            Workspace.owner_id == current_user.id,
            (
                Workspace.name.ilike(f"%{query}%") |
                Workspace.description.ilike(f"%{query}%")
            )
        ).all()

        pages = Page.query.join(
            Workspace,
            Page.workspace_id == Workspace.id
        ).filter(
            Workspace.owner_id == current_user.id,
            (
                Page.title.ilike(f"%{query}%") |
                Page.content.ilike(f"%{query}%")
            )
        ).all()

    return render_template(
        "search.html",
        query=query,
        workspaces=workspaces,
        pages=pages
    )
