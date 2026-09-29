from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from utils.auth import login_required
from services.panel_service import PanelService

panel_bp = Blueprint("panel", __name__)


@panel_bp.route("/panels")
@login_required
def my_panels():

    panels = PanelService.get_user_panels(
        session["user_id"]
    )

    return render_template(
        "panels/my_panels.html",
        panels=panels
    )


@panel_bp.route("/panels/register", methods=["GET", "POST"])
@login_required
def register_panel():

    if request.method == "POST":

        data = {

            "user_id": session["user_id"],

            "panel_name":
                request.form.get("panel_name", "").strip(),

            "manufacturer":
                request.form.get("manufacturer", "").strip(),

            "model_number":
                request.form.get("model_number", "").strip(),

            "capacity":
                request.form.get("capacity"),

            "installation_date":
                request.form.get("installation_date"),

            "location":
                request.form.get("location", "").strip(),

            "serial_number":
                request.form.get("serial_number", "").strip()
        }

        result = PanelService.register_panel(data)

        if result == "Panel Registered Successfully":

            flash(result, "success")

            return redirect(
                url_for("panel.my_panels")
            )

        return render_template(
            "panels/register_panel.html",
            error=result,
            form_data=data
        )

    return render_template(
        "panels/register_panel.html",
        form_data={}
    )

@panel_bp.route(
    "/panels/edit/<int:panel_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_panel(panel_id):

    panel = PanelService.get_panel(
        panel_id,
        session["user_id"]
    )

    if panel is None:

        flash(
            "Panel not found.",
            "danger"
        )

        return redirect(
            url_for("panel.my_panels")
        )

    if request.method == "POST":

        data = {

            "panel_name":
                request.form.get("panel_name", "").strip(),

            "manufacturer":
                request.form.get("manufacturer", "").strip(),

            "model_number":
                request.form.get("model_number", "").strip(),

            "capacity":
                request.form.get("capacity"),

            "installation_date":
                request.form.get("installation_date"),

            "location":
                request.form.get("location", "").strip(),

            "serial_number":
                request.form.get("serial_number", "").strip()
        }

        result = PanelService.update_panel(
            panel_id,
            session["user_id"],
            data
        )

        flash(result, "success")

        return redirect(
            url_for("panel.my_panels")
        )

    return render_template(
        "panels/edit_panel.html",
        panel=panel
    )

@panel_bp.route("/panels/delete/<int:panel_id>")
@login_required
def delete_panel(panel_id):

    result = PanelService.delete_panel(

        panel_id,

        session["user_id"]

    )

    flash(result, "success")

    return redirect(
        url_for("panel.my_panels")
    )

@panel_bp.route("/panels/view/<int:panel_id>")
@login_required
def view_panel(panel_id):

    panel = PanelService.get_panel_by_id(
        panel_id,
        session["user_id"]
    )

    if panel is None:

        flash(
            "Panel not found.",
            "danger"
        )

        return redirect(
            url_for("panel.my_panels")
        )

    return render_template(
        "panels/panel_details.html",
        panel=panel
    )

# =========================================================
# PANEL PERFORMANCE ANALYTICS
# =========================================================

@panel_bp.route(
    "/panels/view/<int:panel_id>/analytics"
)
@login_required
def panel_analytics(panel_id):

    user_id = session["user_id"]

    # -----------------------------------------------------
    # Verify panel belongs to logged-in user
    # -----------------------------------------------------

    panel = PanelService.get_panel_by_id(
        panel_id,
        user_id
    )

    if panel is None:

        flash(
            "Panel not found.",
            "danger"
        )

        return redirect(
            url_for("panel.my_panels")
        )

    # -----------------------------------------------------
    # Get performance analytics
    # -----------------------------------------------------

    analytics = (
        PanelService.get_panel_performance_analytics(
            panel_id
        )
    )

    return render_template(
        "panels/panel_analytics.html",
        panel=panel,
        analytics=analytics
    )