from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    session
)

from services.panel_service import PanelService
from utils.auth import login_required
from services.dashboard_service import DashboardService
from services.notification_service import NotificationService

user_bp = Blueprint("user", __name__)


@user_bp.route("/user/dashboard")
@login_required
def dashboard():

    stats = DashboardService.get_dashboard_stats(
    session["user_id"]
)

    recent_panels = DashboardService.get_recent_panels(
        session["user_id"]
    )

    return render_template(
        "dashboard/user_dashboard.html",
        stats=stats,
        recent_panels=recent_panels
    )


# =========================================================
# USER - NOTIFICATIONS
# =========================================================

@user_bp.route("/notifications")
def notifications():

    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    user_id = session["user_id"]

    notifications = NotificationService.get_user_notifications(
        user_id
    )

    unread_count = NotificationService.get_unread_count(
        user_id
    )

    return render_template(
        "user/notifications.html",
        notifications=notifications,
        unread_count=unread_count
    )


# =========================================================
# USER - MARK NOTIFICATION AS READ
# =========================================================

@user_bp.route(
    "/notifications/read/<int:notification_id>",
    methods=["POST"]
)
def mark_notification_read(notification_id):

    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    NotificationService.mark_as_read(
        notification_id,
        session["user_id"]
    )

    return redirect(
        url_for("user.notifications")
    )


# =========================================================
# USER - MARK ALL NOTIFICATIONS AS READ
# =========================================================

@user_bp.route(
    "/notifications/read-all",
    methods=["POST"]
)
def mark_all_notifications_read():

    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    NotificationService.mark_all_as_read(
        session["user_id"]
    )

    return redirect(
        url_for("user.notifications")
    )