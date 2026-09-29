import os
import uuid

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    current_app
)

from werkzeug.utils import secure_filename

from utils.auth import login_required
from services.panel_service import PanelService
from services.ai_detection_service import AIDetectionService
from ai.prediction.predict import predict_image
from database.db import get_connection

# ============================================================
# BLUEPRINT
# ============================================================

ai_bp = Blueprint(
    "ai",
    __name__
)


# ============================================================
# AI DETECTION
# ============================================================

@ai_bp.route(
    "/ai/detection",
    methods=["GET", "POST"]
)
@login_required
def detection():

    user_id = session["user_id"]

    # --------------------------------------------------------
    # Get user's registered panels
    # --------------------------------------------------------

    panels = PanelService.get_user_panels(
        user_id
    )


    # ========================================================
    # POST - ANALYZE IMAGE
    # ========================================================

    if request.method == "POST":

        panel_id = request.form.get(
            "panel_id"
        )

        image = request.files.get(
            "image"
        )


        # ----------------------------------------------------
        # Validate panel
        # ----------------------------------------------------

        if not panel_id:

            flash(
                "Please select a solar panel.",
                "danger"
            )

            return redirect(
                url_for("ai.detection")
            )


        # ----------------------------------------------------
        # Validate image
        # ----------------------------------------------------

        if not image or image.filename == "":

            flash(
                "Please upload a solar panel image.",
                "danger"
            )

            return redirect(
                url_for("ai.detection")
            )


        # ----------------------------------------------------
        # Verify panel ownership
        # ----------------------------------------------------

        panel = PanelService.get_panel_by_id(
            panel_id,
            user_id
        )


        if not panel:

            flash(
                "Invalid solar panel selected.",
                "danger"
            )

            return redirect(
                url_for("ai.detection")
            )


        # ----------------------------------------------------
        # Allowed image extensions
        # ----------------------------------------------------

        allowed_extensions = {
            "jpg",
            "jpeg",
            "png",
            "webp"
        }


        filename = secure_filename(
            image.filename
        )


        if "." not in filename:

            flash(
                "Invalid image file.",
                "danger"
            )

            return redirect(
                url_for("ai.detection")
            )


        extension = filename.rsplit(
            ".",
            1
        )[1].lower()


        if extension not in allowed_extensions:

            flash(
                "Only JPG, JPEG, PNG and WEBP images are allowed.",
                "danger"
            )

            return redirect(
                url_for("ai.detection")
            )


        # ----------------------------------------------------
        # Upload directory
        # ----------------------------------------------------

        upload_folder = os.path.join(
            current_app.root_path,
            "static",
            "uploads",
            "ai"
        )


        os.makedirs(
            upload_folder,
            exist_ok=True
        )


        # ----------------------------------------------------
        # Generate unique filename
        # ----------------------------------------------------

        unique_filename = (
            str(uuid.uuid4())
            + "."
            + extension
        )


        image_path = os.path.join(
            upload_folder,
            unique_filename
        )


        # ----------------------------------------------------
        # Save image
        # ----------------------------------------------------

        image.save(
            image_path
        )


        # ====================================================
        # AI PREDICTION
        # ====================================================

        try:

            result = predict_image(
                image_path
            )

        except Exception as e:

            print(
                "AI Prediction Error:",
                e
            )

            if os.path.exists(
                image_path
            ):
                os.remove(
                    image_path
                )


            flash(
                "AI analysis failed. Please try again.",
                "danger"
            )

            return redirect(
                url_for("ai.detection")
            )


        # ----------------------------------------------------
        # Validate prediction result
        # ----------------------------------------------------

        if not result:

            if os.path.exists(
                image_path
            ):
                os.remove(
                    image_path
                )


            flash(
                "AI could not analyze the image.",
                "danger"
            )

            return redirect(
                url_for("ai.detection")
            )


        detected_defect = result[
            "prediction"
        ]

        confidence = result[
            "confidence"
        ]


        # ====================================================
        # ESTIMATED EFFICIENCY
        # ====================================================

        efficiency_map = {

            "Clean": 95.0,

            "Dusty": 82.0,

            "Bird-Drop": 88.0,

            "Electrical-Damage": 65.0,

            "Physical-Damage": 55.0
        }


        estimated_efficiency = (
            efficiency_map.get(
                detected_defect,
                70.0
            )
        )


        # ====================================================
        # MAINTENANCE & RECOMMENDATION
        # ====================================================

        if detected_defect == "Clean":

            maintenance_required = "No"

            recommendation = (
                "The solar panel appears clean and "
                "does not show a major visible defect. "
                "Continue regular monitoring and maintenance."
            )


        elif detected_defect == "Dusty":

            maintenance_required = "Yes"

            recommendation = (
                "Dust or dirt accumulation has been detected. "
                "Cleaning the solar panel is recommended "
                "to maintain efficient power generation."
            )


        elif detected_defect == "Bird-Drop":

            maintenance_required = "Yes"

            recommendation = (
                "Bird-drop contamination has been detected. "
                "Clean the affected panel surface and inspect "
                "the panel for any additional damage."
            )


        elif detected_defect == "Electrical-Damage":

            maintenance_required = "Yes"

            recommendation = (
                "Possible electrical damage has been detected. "
                "The panel should be inspected by a qualified "
                "technician before further operation."
            )


        elif detected_defect == "Physical-Damage":

            maintenance_required = "Yes"

            recommendation = (
                "Physical damage has been detected. "
                "A technician should inspect the panel "
                "and determine whether repair or replacement "
                "is required."
            )


        else:

            maintenance_required = "Yes"

            recommendation = (
                "An abnormal condition was detected. "
                "Further inspection is recommended."
            )


        # ====================================================
        # DATABASE IMAGE PATH
        # ====================================================

        relative_image_path = (
            "uploads/ai/"
            + unique_filename
        )


        # ====================================================
        # SAVE AI RESULT
        # ====================================================

        detection_id = (
            AIDetectionService.save_detection(

                panel_id=panel_id,

                request_id=None,

                image_path=relative_image_path,

                detected_defect=detected_defect,

                confidence_score=confidence,

                estimated_efficiency=estimated_efficiency,

                maintenance_required=maintenance_required,

                ai_recommendation=recommendation
            )
        )


        # ----------------------------------------------------
        # Database save failure
        # ----------------------------------------------------

        if not detection_id:

            flash(
                "AI result could not be saved.",
                "danger"
            )

            return redirect(
                url_for("ai.detection")
            )

        # ====================================================
        # LOW EFFICIENCY ALERT
        # ====================================================

        LOW_EFFICIENCY_THRESHOLD = 70.0

        if estimated_efficiency < LOW_EFFICIENCY_THRESHOLD:

            connection = get_connection()

            if connection:

                cursor = None

                try:

                    cursor = connection.cursor()

                    cursor.execute(
                        """
                        INSERT INTO notifications
                        (
                            user_id,
                            title,
                            message,
                            notification_type,
                            is_read
                        )
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            user_id,
                            "Low Panel Efficiency Alert",
                            (
                                f"Solar panel '{panel['panel_name']}' "
                                f"has an estimated efficiency of "
                                f"{estimated_efficiency}%. "
                                "Maintenance may be required."
                            ),
                            "AI Alert",
                            0
                        )
                    )

                    connection.commit()

                except Exception as e:

                    if connection:
                        connection.rollback()

                    print(
                        "Low efficiency notification error:",
                        e
                    )

                finally:

                    if cursor:
                        cursor.close()

                    connection.close()

        # ====================================================
        # SHOW RESULT
        # ====================================================

        return render_template(

            "ai/detection_result.html",

            result=result,

            panel=panel,

            detection_id=detection_id,

            image_path=relative_image_path,

            maintenance_required=maintenance_required,

            recommendation=recommendation,

            estimated_efficiency=estimated_efficiency
        )


    # ========================================================
    # GET - DETECTION PAGE
    # ========================================================

    return render_template(
        "ai/detection.html",
        panels=panels
    )


# ============================================================
# AI ANALYSIS HISTORY
# ============================================================

@ai_bp.route("/ai/history")
@login_required
def history():

    user_id = session["user_id"]

    detections = AIDetectionService.get_user_detections(
        user_id
    )

    return render_template(
        "ai/history.html",
        detections=detections
    )

# ============================================================
# AI ANALYSIS DETAIL
# ============================================================

@ai_bp.route("/ai/history/<int:detection_id>")
@login_required
def analysis_detail(detection_id):

    user_id = session["user_id"]

    detection = AIDetectionService.get_detection_by_id(
        detection_id
    )

    # --------------------------------------------------------
    # Detection does not exist
    # --------------------------------------------------------

    if not detection:

        flash(
            "AI detection not found.",
            "danger"
        )

        return redirect(
            url_for("ai.history")
        )


    # --------------------------------------------------------
    # Security: verify that this detection belongs
    # to the logged-in user
    # --------------------------------------------------------

    panel = PanelService.get_panel_by_id(
        detection["panel_id"],
        user_id
    )


    if not panel:

        flash(
            "You are not authorized to view this detection.",
            "danger"
        )

        return redirect(
            url_for("ai.history")
        )


    # --------------------------------------------------------
    # Show detailed analysis
    # --------------------------------------------------------

    return render_template(
        "ai/analysis_detail.html",
        detection=detection,
        panel=panel
    )