
from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    session
)

from services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        data = {
            "full_name": request.form.get("full_name", "").strip(),
            "email": request.form.get("email", "").strip().lower(),
            "phone": request.form.get("phone", "").strip(),
            "password": request.form.get("password", ""),
            "confirm_password": request.form.get("confirm_password", ""),
            "role": request.form.get("role", "").strip()
        }

        result = AuthService.register_user(data)

        if result == "Registration Successful":
            flash(
                "Registration Successful. Please log in.",
                "success"
            )
            return redirect(url_for("auth.login"))

        return render_template(
            "auth/register.html",
            error=result,
            form_data=data
        )

    return render_template(
        "auth/register.html",
        form_data={}
    )


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        data = {
            "email": request.form.get("email", "").strip().lower(),
            "password": request.form.get("password", "")
        }

        result = AuthService.login_user(data)

        if isinstance(result, str):
            return render_template(
                "auth/login.html",
                error=result
            )

        session["user_id"] = result["user_id"]
        session["full_name"] = result["full_name"]
        session["role"] = result["role"]

        flash(
            f"Welcome {result['full_name']}!",
            "success"
        )

        if result["role"] == "Admin":
            return redirect(url_for("admin.dashboard"))

        elif result["role"] == "Technician":
            return redirect(url_for("technician.dashboard"))

        else:
            return redirect(url_for("user.dashboard"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out successfully.",
        "success"
    )

    return redirect(url_for("auth.login"))
