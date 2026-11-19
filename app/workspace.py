
from flask import Blueprint, render_template, request, redirect, url_for
import markdown
import bleach
import re
import html

from flask_login import login_required, current_user
from sqlalchemy import func

from .database import db
from .models import Workspace, Page, PageVersion

workspace = Blueprint("workspace", __name__)


# Retrieve only the logged-in user's workspace
def get_owned_workspace(workspace_id):
    return Workspace.query.filter_by(
        id=workspace_id,
        owner_id=current_user.id
    ).first_or_404()


# Retrieve only pages belonging to the logged-in user
def get_owned_page(page_id):
    return Page.query.join(
        Workspace,
        Page.workspace_id == Workspace.id
    ).filter(
        Page.id == page_id,
        Workspace.owner_id == current_user.id
    ).first_or_404()

# Convert [[Page Title]] into clickable internal links
def render_internal_links(content, workspace_id):
    pattern = re.compile(r"\[\[\s*(.*?)\s*\]\]")

    def replace_link(match):
        title = match.group(1).strip()

        if not title:
            return html.escape(match.group(0))

        target_page = Page.query.filter(
            Page.workspace_id == workspace_id,
            func.lower(Page.title) == title.lower()
        ).first()

        if target_page:
            link = url_for(
                "workspace.view_page",
                page_id=target_page.id
            )

            return (
                f'<a href="{link}">'
                f'{html.escape(target_page.title)}</a>'
            )

        return html.escape(match.group(0))

    return pattern.sub(replace_link, content or "")


# Find pages that link to the current page
def get_backlinks(page):
    candidate_pages = Page.query.filter(
        Page.workspace_id == page.workspace_id,
        Page.id != page.id
    ).all()

    pattern = re.compile(
        r"\[\[\s*" + re.escape(page.title) + r"\s*\]\]",
        re.IGNORECASE
    )

    return [
        candidate
        for candidate in candidate_pages
        if pattern.search(candidate.content or "")
    ]

# Display all workspaces
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


# Create a workspace
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


# Display workspace and its main pages
@workspace.route("/workspace/<int:workspace_id>")
@login_required
def workspace_detail(workspace_id):
    selected_workspace = get_owned_workspace(workspace_id)

    pages = Page.query.filter_by(
        workspace_id=selected_workspace.id,
        parent_id=None
    ).all()

    return render_template(
        "workspace_detail.html",
        workspace=selected_workspace,
        pages=pages
    )


# Create a main page inside a workspace
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
            workspace_id=selected_workspace.id,
            parent_id=None
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


# Create a child page inside an existing page
@workspace.route(
    "/page/<int:page_id>/child/create",
    methods=["GET", "POST"]
)
@login_required
def create_child_page(page_id):
    parent_page = get_owned_page(page_id)

    selected_workspace = get_owned_workspace(
        parent_page.workspace_id
    )

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "")

        if not title:
            return render_template(
                "create_page.html",
                workspace=selected_workspace,
                parent_page=parent_page
            )

        new_page = Page(
            title=title,
            content=content,
            workspace_id=selected_workspace.id,
            parent_id=parent_page.id
        )

        db.session.add(new_page)
        db.session.commit()

        return redirect(
            url_for(
                "workspace.view_page",
                page_id=parent_page.id
            )
        )

    return render_template(
        "create_page.html",
        workspace=selected_workspace,
        parent_page=parent_page
    )


# View a page
@workspace.route("/page/<int:page_id>")
@login_required
def view_page(page_id):
    page = get_owned_page(page_id)

    # Convert internal links before Markdown rendering
    linked_content = render_internal_links(
        page.content,
        page.workspace_id
    )

    raw_html = markdown.markdown(
        linked_content,
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

    backlinks = get_backlinks(page)

    return render_template(
        "page.html",
        page=page,
        rendered_content=rendered_content,
        child_pages=page.children,
        backlinks=backlinks
    )


@workspace.route("/page/<int:page_id>/edit", methods=["GET", "POST"])
@login_required
def edit_page(page_id):
    page = get_owned_page(page_id)
    selected_workspace = get_owned_workspace(page.workspace_id)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "")

        if not title:
            return render_template(
                "create_page.html",
                page=page,
                workspace=selected_workspace
            )

        # Save the previous version before updating
        old_version = PageVersion(
            page_id=page.id,
            title=page.title,
            content=page.content or ""
        )

        db.session.add(old_version)

        page.title = title
        page.content = content

        db.session.commit()

        return redirect(url_for("workspace.view_page", page_id=page.id))

    return render_template(
        "create_page.html",
        page=page,
        workspace=selected_workspace
    )


# Delete a page and its nested children
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


# Edit a workspace
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


# Delete a workspace and its pages
@workspace.route(
    "/workspace/<int:workspace_id>/delete",
    methods=["POST"]
)
@login_required
def delete_workspace(workspace_id):
    selected_workspace = get_owned_workspace(workspace_id)

    root_pages = Page.query.filter_by(
        workspace_id=selected_workspace.id,
        parent_id=None
    ).all()

    for page in root_pages:
        db.session.delete(page)

    db.session.delete(selected_workspace)
    db.session.commit()

    return redirect(url_for("workspace.workspaces"))


# Search the current user's content
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
@workspace.route("/page/<int:page_id>/history")
@login_required
def page_history(page_id):
    page = get_owned_page(page_id)

    versions = PageVersion.query.filter_by(
        page_id=page.id
    ).order_by(PageVersion.created_at.desc()).all()

    return render_template(
        "page_history.html",
        page=page,
        versions=versions
    )


@workspace.route("/page/<int:page_id>/history/<int:version_id>")
@login_required
def view_version(page_id, version_id):
    page = get_owned_page(page_id)

    version = PageVersion.query.filter_by(
        id=version_id,
        page_id=page.id
    ).first_or_404()

    return render_template(
        "view_version.html",
        page=page,
        version=version
    )


@workspace.route(
    "/page/<int:page_id>/history/<int:version_id>/restore",
    methods=["POST"]
)
@login_required
def restore_version(page_id, version_id):
    page = get_owned_page(page_id)

    version = PageVersion.query.filter_by(
        id=version_id,
        page_id=page.id
    ).first_or_404()

    # Save current content before restoring
    current_version = PageVersion(
        page_id=page.id,
        title=page.title,
        content=page.content or ""
    )

    db.session.add(current_version)

    page.title = version.title
    page.content = version.content

    db.session.commit()

    return redirect(url_for("workspace.view_page", page_id=page.id))