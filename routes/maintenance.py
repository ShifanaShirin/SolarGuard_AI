from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for,
    request,
    flash
)
from services.maintenance_service import MaintenanceService

maintenance_bp = Blueprint(
    "maintenance",
    __name__,
    url_prefix="/maintenance"
)


@maintenance_bp.route("/")
def my_requests():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    # Get summary statistics
    stats = MaintenanceService.get_request_statistics(user_id)

    # Get all maintenance requests
    requests = MaintenanceService.get_user_requests(user_id)

    return render_template(
        "maintenance/my_requests.html",
        requests=requests,
        stats=stats
    )

@maintenance_bp.route("/create", methods=["GET", "POST"])
def create_request():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "POST":

        success = MaintenanceService.create_request(
            session["user_id"],
            request.form,
            request.files.get("image")
        )

        if success:

            flash(
                "Maintenance request submitted successfully.",
                "success"
            )

            return redirect(
                url_for("maintenance.my_requests")
            )

        flash(
            "Unable to submit request.",
            "danger"
        )

    panels = MaintenanceService.get_user_panels(
        session["user_id"]
    )

    return render_template(
        "maintenance/create_request.html",
        panels=panels
    )

@maintenance_bp.route("/view/<int:request_id>")
def view_request(request_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    request_data = MaintenanceService.get_request_by_id(
        request_id,
        session["user_id"]
    )

    if not request_data:
        flash(
            "Maintenance request not found.",
            "danger"
        )
        return redirect(url_for("maintenance.my_requests"))

    return render_template(
        "maintenance/view_request.html",
        request_data=request_data
    )

@maintenance_bp.route("/edit/<int:request_id>", methods=["GET", "POST"])
def edit_request(request_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    request_data = MaintenanceService.get_request_by_id(
        request_id,
        session["user_id"]
    )

    if not request_data:
        flash("Maintenance request not found.", "danger")
        return redirect(url_for("maintenance.my_requests"))

    if request_data["request_status"] != "Pending":
        flash(
            "Only pending requests can be edited.",
            "warning"
        )
        return redirect(url_for("maintenance.my_requests"))

    if request.method == "POST":

        success = MaintenanceService.update_request(
            request_id,
            session["user_id"],
            request.form
        )

        if success:
            flash(
                "Maintenance request updated successfully.",
                "success"
            )
            return redirect(
                url_for("maintenance.my_requests")
            )

        flash("Unable to update request.", "danger")

    panels = MaintenanceService.get_user_panels(
        session["user_id"]
    )

    return render_template(
        "maintenance/edit_request.html",
        request_data=request_data,
        panels=panels
    )

@maintenance_bp.route("/cancel/<int:request_id>")
def cancel_request(request_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    success = MaintenanceService.cancel_request(
        request_id,
        session["user_id"]
    )

    if success:

        flash(
            "Maintenance request cancelled successfully.",
            "success"
        )

    else:

        flash(
            "Unable to cancel request.",
            "danger"
        )

    return redirect(
        url_for("maintenance.my_requests")
    )

# =========================================================
# USER - VIEW MAINTENANCE REPORT
# =========================================================

@maintenance_bp.route("/report/<int:request_id>")
def view_report(request_id):

    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    user_id = session["user_id"]

    report = MaintenanceService.get_maintenance_report(
        request_id
    )

    if not report:

        flash(
            "Maintenance report not found.",
            "warning"
        )

        return redirect(
            url_for("maintenance.my_requests")
        )

    # -----------------------------------------------------
    # Security check
    # -----------------------------------------------------

    if report["user_id"] != user_id:

        flash(
            "You are not authorized to view this report.",
            "danger"
        )

        return redirect(
            url_for("maintenance.my_requests")
        )

    return render_template(
        "maintenance/report.html",
        report=report
    )