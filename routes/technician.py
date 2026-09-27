from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    flash,
    request
)
import os
from werkzeug.utils import secure_filename
from services.technician_service import TechnicianService


technician_bp = Blueprint(
    "technician",
    __name__
)


# =========================================================
# TECHNICIAN DASHBOARD
# =========================================================

@technician_bp.route("/technician/dashboard")
def dashboard():

    # -----------------------------------------------------
    # Check login
    # -----------------------------------------------------

    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    # -----------------------------------------------------
    # Check technician role
    # -----------------------------------------------------

    if session.get("role") != "Technician":
        return redirect(
            url_for("auth.login")
        )

    # -----------------------------------------------------
    # Get technician ID
    # -----------------------------------------------------

    technician_id = session["user_id"]

    # -----------------------------------------------------
    # Get dashboard statistics
    # -----------------------------------------------------

    stats = TechnicianService.get_dashboard_stats(
        technician_id
    )

    # -----------------------------------------------------
    # Get assigned maintenance requests
    # -----------------------------------------------------

    assignments = TechnicianService.get_assigned_requests(
        technician_id
    )

    # -----------------------------------------------------
    # Render dashboard
    # -----------------------------------------------------

    return render_template(
        "dashboard/technician_dashboard.html",
        stats=stats,
        assignments=assignments
    )

# =========================================================
# MY MAINTENANCE JOBS
# =========================================================

@technician_bp.route("/technician/maintenance")
def my_requests():

    # -----------------------------------------------------
    # Check login
    # -----------------------------------------------------

    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    # -----------------------------------------------------
    # Check technician role
    # -----------------------------------------------------

    if session.get("role") != "Technician":
        return redirect(
            url_for("auth.login")
        )

    # -----------------------------------------------------
    # Get technician ID
    # -----------------------------------------------------

    technician_id = session["user_id"]

    # -----------------------------------------------------
    # Get assigned maintenance requests
    # -----------------------------------------------------

    assignments = TechnicianService.get_assigned_requests(
        technician_id
    )

    # -----------------------------------------------------
    # Render maintenance page
    # -----------------------------------------------------

    return render_template(
        "technician/maintenance_jobs.html",
        assignments=assignments
    )

# =========================================================
# MAINTENANCE REQUEST DETAILS
# =========================================================

@technician_bp.route("/technician/request/<int:request_id>")
def request_details(request_id):

    # -----------------------------------------------------
    # Check login
    # -----------------------------------------------------

    if "user_id" not in session:

        return redirect(
            url_for("auth.login")
        )

    # -----------------------------------------------------
    # Check technician role
    # -----------------------------------------------------

    if session.get("role") != "Technician":

        return redirect(
            url_for("auth.login")
        )

    # -----------------------------------------------------
    # Get technician ID
    # -----------------------------------------------------

    technician_id = session["user_id"]

    # -----------------------------------------------------
    # Get request details
    # -----------------------------------------------------

    assignment = TechnicianService.get_request_details(
        technician_id,
        request_id
    )

    # -----------------------------------------------------
    # Request not found / not assigned to technician
    # -----------------------------------------------------

    if assignment is None:

        return redirect(
            url_for("technician.my_requests")
        )

    # -----------------------------------------------------
    # Render details page
    # -----------------------------------------------------

    return render_template(
        "technician/request_details.html",
        assignment=assignment
    )

# =========================================================
# ACCEPT MAINTENANCE REQUEST
# =========================================================

@technician_bp.route(
    "/technician/request/<int:request_id>/accept",
    methods=["POST"]
)
def accept_request(request_id):

    # -----------------------------------------------------
    # Check login
    # -----------------------------------------------------

    if "user_id" not in session:

        return redirect(
            url_for("auth.login")
        )

    # -----------------------------------------------------
    # Check technician role
    # -----------------------------------------------------

    if session.get("role") != "Technician":

        return redirect(
            url_for("auth.login")
        )

    # -----------------------------------------------------
    # Get technician ID
    # -----------------------------------------------------

    technician_id = session["user_id"]

    # -----------------------------------------------------
    # Accept request
    # -----------------------------------------------------

    success = TechnicianService.accept_request(
        technician_id,
        request_id
    )

    if success:

        flash(
            "Maintenance job accepted successfully.",
            "success"
        )

    else:

        flash(
            "Unable to accept this maintenance job.",
            "danger"
        )

    return redirect(
        url_for(
            "technician.request_details",
            request_id=request_id
        )
    )

# =========================================================
# START MAINTENANCE REQUEST
# =========================================================

@technician_bp.route(
    "/technician/request/<int:request_id>/start",
    methods=["POST"]
)
def start_request(request_id):

    # -----------------------------------------------------
    # Check login
    # -----------------------------------------------------

    if "user_id" not in session:

        return redirect(
            url_for("auth.login")
        )

    # -----------------------------------------------------
    # Check technician role
    # -----------------------------------------------------

    if session.get("role") != "Technician":

        return redirect(
            url_for("auth.login")
        )

    # -----------------------------------------------------
    # Get technician ID
    # -----------------------------------------------------

    technician_id = session["user_id"]

    # -----------------------------------------------------
    # Start maintenance job
    # -----------------------------------------------------

    success = TechnicianService.start_request(
        technician_id,
        request_id
    )

    if success:

        flash(
            "Maintenance job started successfully.",
            "success"
        )

    else:

        flash(
            "Unable to start this maintenance job.",
            "danger"
        )

    return redirect(
        url_for(
            "technician.request_details",
            request_id=request_id
        )
    )

# =========================================================
# COMPLETE MAINTENANCE REQUEST
# =========================================================

# =========================================================
# COMPLETE MAINTENANCE REQUEST
# =========================================================

@technician_bp.route(
    "/technician/request/<int:request_id>/complete",
    methods=["GET", "POST"]
)
def complete_request(request_id):

    # -----------------------------------------------------
    # Check login
    # -----------------------------------------------------

    if "user_id" not in session:

        return redirect(
            url_for("auth.login")
        )

    # -----------------------------------------------------
    # Check technician role
    # -----------------------------------------------------

    if session.get("role") != "Technician":

        return redirect(
            url_for("auth.login")
        )

    technician_id = session["user_id"]

    # -----------------------------------------------------
    # Get request details
    # -----------------------------------------------------

    assignment = TechnicianService.get_request_details(
        technician_id,
        request_id
    )

    if assignment is None:

        flash(
            "Maintenance request not found.",
            "danger"
        )

        return redirect(
            url_for("technician.my_requests")
        )

    # -----------------------------------------------------
    # GET
    # -----------------------------------------------------

    if request.method == "GET":

        if assignment["assignment_status"] != "In Progress":

            flash(
                "This job is not currently in progress.",
                "warning"
            )

            return redirect(
                url_for(
                    "technician.request_details",
                    request_id=request_id
                )
            )

        return render_template(
            "technician/complete_request.html",
            assignment=assignment
        )

    # -----------------------------------------------------
    # POST
    # -----------------------------------------------------

    inspection_notes = request.form.get(
        "inspection_notes",
        ""
    ).strip()

    repair_details = request.form.get(
        "repair_details",
        ""
    ).strip()

    parts_replaced = request.form.get(
        "parts_replaced",
        ""
    ).strip()

    # -----------------------------------------------------
    # Validate inspection notes
    # -----------------------------------------------------

    if not inspection_notes:

        flash(
            "Inspection notes are required.",
            "danger"
        )

        return redirect(
            url_for(
                "technician.complete_request",
                request_id=request_id
            )
        )

    # -----------------------------------------------------
    # Handle service image
    # -----------------------------------------------------

    service_image_path = None

    image = request.files.get("service_image")

    if image and image.filename:

        filename = secure_filename(
            image.filename
        )

        upload_folder = os.path.join(
            "static",
            "uploads",
            "maintenance"
        )

        os.makedirs(
            upload_folder,
            exist_ok=True
        )

        # -------------------------------------------------
        # Create unique filename
        # -------------------------------------------------

        import uuid

        extension = os.path.splitext(
            filename
        )[1]

        unique_filename = (
            f"request_{request_id}_"
            f"{uuid.uuid4().hex}"
            f"{extension}"
        )

        file_path = os.path.join(
            upload_folder,
            unique_filename
        )

        image.save(file_path)

        # Path stored in database

        service_image_path = (
            f"uploads/maintenance/{unique_filename}"
        )

    # -----------------------------------------------------
    # Complete request
    # -----------------------------------------------------

    success = TechnicianService.complete_request(
        technician_id,
        request_id,
        inspection_notes,
        repair_details,
        parts_replaced,
        service_image_path
    )

    if success:

        flash(
            "Maintenance job completed successfully.",
            "success"
        )

    else:

        flash(
            "Unable to complete the maintenance job.",
            "danger"
        )

    return redirect(
        url_for(
            "technician.request_details",
            request_id=request_id
        )
    )

# =========================================================
# VIEW MAINTENANCE REPORT
# =========================================================

@technician_bp.route(
    "/technician/request/<int:request_id>/report"
)
def view_report(request_id):

    # -----------------------------------------------------
    # Check login
    # -----------------------------------------------------

    if "user_id" not in session:

        return redirect(
            url_for("auth.login")
        )

    # -----------------------------------------------------
    # Check technician role
    # -----------------------------------------------------

    if session.get("role") != "Technician":

        return redirect(
            url_for("auth.login")
        )

    technician_id = session["user_id"]

    # -----------------------------------------------------
    # Get maintenance report
    # -----------------------------------------------------

    report = TechnicianService.get_maintenance_report(
        technician_id,
        request_id
    )

    if report is None:

        flash(
            "Maintenance report not found.",
            "warning"
        )

        return redirect(
            url_for(
                "technician.dashboard"
            )
        )

    return render_template(
        "technician/maintenance_report.html",
        report=report
    )