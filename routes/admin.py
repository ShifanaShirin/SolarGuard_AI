from flask import (
    Blueprint,
    redirect,
    url_for,
    render_template,
    session,
    flash,
    request
)

from services.admin_service import AdminService
from services.maintenance_service import MaintenanceService

admin_bp = Blueprint("admin", __name__)


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@admin_bp.route("/dashboard")
def dashboard():

    # Check login
    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    # Check admin role
    if session.get("role") != "Admin":
        flash(
            "Access denied.",
            "danger"
        )

        return redirect(
            url_for("auth.login")
        )

    # Get dashboard statistics
    stats = AdminService.get_dashboard_stats()

    return render_template(
        "dashboard/admin_dashboard.html",
        stats=stats
    )


# =========================================================
# ADMIN - MAINTENANCE REQUESTS
# =========================================================

@admin_bp.route("/maintenance")
def maintenance_requests():

    # Check login
    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    # Check admin role
    if session.get("role") != "Admin":
        flash(
            "Access denied.",
            "danger"
        )

        return redirect(
            url_for("auth.login")
        )

    # Get all maintenance requests
    requests = AdminService.get_all_maintenance_requests()

    return render_template(
        "admin/maintenance_requests.html",
        requests=requests
    )


# =========================================================
# ADMIN - MAINTENANCE REQUEST DETAILS
# =========================================================

@admin_bp.route("/maintenance/<int:request_id>")
def maintenance_request_details(request_id):

    # Check login
    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    # Check admin role
    if session.get("role") != "Admin":
        flash(
            "Access denied.",
            "danger"
        )

        return redirect(
            url_for("auth.login")
        )

    # Get request details
    maintenance_request = (
        AdminService.get_maintenance_request_details(
            request_id
        )
    )

    # Request not found
    if not maintenance_request:

        flash(
            "Maintenance request not found.",
            "danger"
        )

        return redirect(
            url_for("admin.maintenance_requests")
        )

    # Get technicians
    technicians = AdminService.get_technicians()

    return render_template(
        "admin/request_details.html",
        maintenance_request=maintenance_request,
        technicians=technicians
    )


# =========================================================
# ADMIN - UPDATE MAINTENANCE REQUEST STATUS
# =========================================================

@admin_bp.route(
    "/maintenance/<int:request_id>/status",
    methods=["POST"]
)
def update_maintenance_status(request_id):

    # Check login
    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    # Check admin role
    if session.get("role") != "Admin":
        flash(
            "Access denied.",
            "danger"
        )

        return redirect(
            url_for("auth.login")
        )

    status = request.form.get("status")

    # Only these status changes are allowed
    if status not in ["Approved", "Rejected"]:

        flash(
            "Invalid maintenance request status.",
            "danger"
        )

        return redirect(
            url_for(
                "admin.maintenance_request_details",
                request_id=request_id
            )
        )

    success = AdminService.update_request_status(
        request_id,
        status
    )

    if success:

        if status == "Approved":

            flash(
                "Maintenance request approved successfully.",
                "success"
            )

        else:

            flash(
                "Maintenance request rejected.",
                "warning"
            )

    else:

        flash(
            "Unable to update maintenance request.",
            "danger"
        )

    return redirect(
        url_for(
            "admin.maintenance_request_details",
            request_id=request_id
        )
    )


# =========================================================
# ADMIN - ASSIGN TECHNICIAN
# =========================================================

@admin_bp.route(
    "/maintenance/<int:request_id>/assign",
    methods=["POST"]
)
def assign_technician(request_id):

    # Check login
    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    # Check admin role
    if session.get("role") != "Admin":
        flash(
            "Access denied.",
            "danger"
        )

        return redirect(
            url_for("auth.login")
        )

    technician_id = request.form.get("technician_id")

    if not technician_id:

        flash(
            "Please select a technician.",
            "warning"
        )

        return redirect(
            url_for(
                "admin.maintenance_request_details",
                request_id=request_id
            )
        )

    success = AdminService.assign_technician(
        request_id,
        technician_id,
        session["user_id"]
    )

    if success:

        flash(
            "Technician assigned successfully.",
            "success"
        )

    else:

        flash(
            "Unable to assign technician.",
            "danger"
        )

    return redirect(
        url_for(
            "admin.maintenance_request_details",
            request_id=request_id
        )
    )

# =========================================================
# ADMIN - VIEW MAINTENANCE REPORT
# =========================================================

@admin_bp.route(
    "/maintenance/<int:request_id>/report"
)
def view_maintenance_report(request_id):

    # -----------------------------------------------------
    # Check login
    # -----------------------------------------------------

    if "user_id" not in session:

        return redirect(
            url_for("auth.login")
        )

    # -----------------------------------------------------
    # Check Admin role
    # -----------------------------------------------------

    if session.get("role") != "Admin":

        flash(
            "Unauthorized access.",
            "danger"
        )

        return redirect(
            url_for("auth.login")
        )

    # -----------------------------------------------------
    # Get maintenance report
    # -----------------------------------------------------

    report = MaintenanceService.get_maintenance_report(
        request_id
    )

    # -----------------------------------------------------
    # Report not found
    # -----------------------------------------------------

    if not report:

        flash(
            "Maintenance report not found.",
            "warning"
        )

        return redirect(
            url_for("admin.maintenance_requests")
        )

    # -----------------------------------------------------
    # Render report
    # -----------------------------------------------------

    return render_template(
        "admin/maintenance_report.html",
        report=report
    )

# =========================================================
# ADMIN - USERS
# =========================================================

@admin_bp.route("/users")
def users():

    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    users = AdminService.get_all_users()

    return render_template(
        "admin/users.html",
        users=users
    )


# =========================================================
# ADMIN - USER DETAILS
# =========================================================

@admin_bp.route("/users/<int:user_id>")
def user_details(user_id):

    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    user_data = AdminService.get_user_details(
        user_id
    )

    if not user_data:

        flash(
            "User not found.",
            "danger"
        )

        return redirect(
            url_for("admin.users")
        )

    panels = AdminService.get_user_panels(
        user_id
    )

    maintenance_requests = AdminService.get_user_maintenance_requests(
        user_id
    )

    return render_template(
        "admin/user_details.html",
        user=user_data,
        panels=panels,
        maintenance_requests=maintenance_requests
    )

# =========================================================
# ADMIN - TECHNICIANS
# =========================================================

@admin_bp.route("/technicians")
def technicians():

    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    technicians = AdminService.get_all_technicians()

    return render_template(
        "admin/technicians.html",
        technicians=technicians
    )


# =========================================================
# ADMIN - TECHNICIAN DETAILS
# =========================================================

@admin_bp.route("/technicians/<int:technician_id>")
def technician_details(technician_id):

    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    technician = AdminService.get_technician_details(
        technician_id
    )

    if not technician:

        flash(
            "Technician not found.",
            "danger"
        )

        return redirect(
            url_for("admin.technicians")
        )

    jobs = AdminService.get_technician_jobs(
        technician_id
    )

    return render_template(
        "admin/technician_details.html",
        technician=technician,
        jobs=jobs
    )