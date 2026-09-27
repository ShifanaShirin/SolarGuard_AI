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

