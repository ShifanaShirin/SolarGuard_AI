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

from io import BytesIO

from flask import send_file

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image
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


@ai_bp.route("/ai/history/<int:detection_id>/pdf")
@login_required
def download_report(detection_id):

    from io import BytesIO
    from xml.sax.saxutils import escape

    from flask import current_app, send_file
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import (
        getSampleStyleSheet,
        ParagraphStyle
    )
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        Image,
        KeepTogether
    )

    import os

    # --------------------------------------------------
    # 1. FETCH REPORT AND VERIFY OWNERSHIP
    # --------------------------------------------------

    user_id = session["user_id"]

    detection = AIDetectionService.get_detection_by_id(
        detection_id
    )

    if not detection:
        flash("AI detection report not found.", "danger")
        return redirect(url_for("ai.history"))

    panel = PanelService.get_panel_by_id(
        detection["panel_id"],
        user_id
    )

    if not panel:
        flash(
            "You are not authorized to download this report.",
            "danger"
        )
        return redirect(url_for("ai.history"))

    # --------------------------------------------------
    # 2. COLORS AND PAGE SETUP
    # --------------------------------------------------

    navy = colors.HexColor("#101B30")
    green = colors.HexColor("#13A765")
    light_green = colors.HexColor("#EAF7EF")
    light_blue = colors.HexColor("#F2F5FA")
    dark_text = colors.HexColor("#243247")
    muted = colors.HexColor("#64748B")
    border = colors.HexColor("#DCE4EC")
    white = colors.white

    pdf_buffer = BytesIO()

    document = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=42,
        leftMargin=42,
        topMargin=92,
        bottomMargin=58,
        title=f"SolarGuard AI Report {detection_id}",
        author="SolarGuard AI"
    )

    # --------------------------------------------------
    # 3. PROFESSIONAL TEXT STYLES
    # --------------------------------------------------

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="ReportSection",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=navy,
        spaceBefore=8,
        spaceAfter=10
    ))

    styles.add(ParagraphStyle(
        name="ReportBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        leading=14,
        textColor=dark_text
    ))

    styles.add(ParagraphStyle(
        name="ReportLabel",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=muted
    ))

    styles.add(ParagraphStyle(
        name="ReportValue",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=navy
    ))

    styles.add(ParagraphStyle(
        name="ReportSmall",
        parent=styles["BodyText"],
        fontSize=8,
        leading=12,
        textColor=muted
    ))

    styles.add(ParagraphStyle(
        name="ReportCaption",
        parent=styles["BodyText"],
        fontSize=8,
        leading=11,
        alignment=TA_CENTER,
        textColor=muted
    ))

    styles.add(ParagraphStyle(
        name="ReportWhiteTitle",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=19,
        leading=23,
        textColor=white
    ))

    styles.add(ParagraphStyle(
        name="ReportWhiteSubtitle",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#DCE8F5")
    ))

    styles.add(ParagraphStyle(
        name="ReportRecommendation",
        parent=styles["BodyText"],
        fontSize=9,
        leading=14,
        textColor=dark_text
    ))

    story = []

    # --------------------------------------------------
    # 4. REPORT TITLE
    # --------------------------------------------------

    story.append(Paragraph(
        "SOLAR PANEL AI DETECTION REPORT",
        styles["ReportSection"]
    ))

    story.append(Paragraph(
        f"Report ID: SG-{detection_id:05d}",
        styles["ReportSmall"]
    ))

    story.append(Spacer(1, 12))

    # --------------------------------------------------
    # 5. PANEL IMAGE
    # --------------------------------------------------

    story.append(Paragraph(
        "ANALYZED SOLAR PANEL",
        styles["ReportSection"]
    ))

    image_name = os.path.basename(
        detection.get("image_path") or ""
    )

    image_path = os.path.join(
        current_app.root_path,
        "static",
        "uploads",
        "ai",
        image_name
    )

    if (
        image_name
        and os.path.isfile(image_path)
        and image_name.lower().endswith(
            (".jpg", ".jpeg", ".png", ".webp")
        )
    ):
        try:
            panel_image = Image(
                image_path,
                width=4.5 * inch,
                height=2.5 * inch,
                kind="proportional"
            )

            panel_image.hAlign = "CENTER"

            story.append(panel_image)
            story.append(Spacer(1, 5))

            story.append(Paragraph(
                "Uploaded image used for AI analysis",
                styles["ReportCaption"]
            ))

            story.append(Spacer(1, 14))

        except Exception as image_error:
            current_app.logger.warning(
                "Could not add report image: %s",
                image_error
            )

    # --------------------------------------------------
    # 6. RESULT SUMMARY CARDS
    # --------------------------------------------------

    condition = str(
        detection.get("detected_defect") or "N/A"
    )

    confidence = detection.get("confidence_score")
    efficiency = detection.get("estimated_efficiency")

    confidence_text = (
        f"{float(confidence):.2f}%"
        if confidence is not None else "N/A"
    )

    efficiency_text = (
        f"{float(efficiency):.2f}%"
        if efficiency is not None else "N/A"
    )

    maintenance = str(
        detection.get("maintenance_required") or "N/A"
    )

    maintenance_color = (
        colors.HexColor("#B45309")
        if maintenance == "Yes"
        else green
        if maintenance == "No"
        else muted
    )

    def make_card(label, value, value_color=navy):
        card_value_style = ParagraphStyle(
            "CardValue",
            parent=styles["ReportValue"],
            textColor=value_color,
            fontSize=12
        )

        return [
            Paragraph(escape(label), styles["ReportLabel"]),
            Spacer(1, 5),
            Paragraph(escape(str(value)), card_value_style)
        ]

    cards = Table(
        [[
            make_card("DETECTED CONDITION", condition),
            make_card("AI CONFIDENCE", confidence_text),
            make_card("EST. EFFICIENCY", efficiency_text)
        ]],
        colWidths=[
            document.width / 3,
            document.width / 3,
            document.width / 3
        ]
    )

    cards.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), light_blue),
        ("BOX", (0, 0), (-1, -1), 0.7, border),
        ("INNERGRID", (0, 0), (-1, -1), 0.7, border),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12)
    ]))

    story.append(cards)
    story.append(Spacer(1, 17))

    # --------------------------------------------------
    # 7. PANEL AND ANALYSIS DETAILS
    # --------------------------------------------------

    story.append(Paragraph(
        "PANEL & ANALYSIS DETAILS",
        styles["ReportSection"]
    ))

    analyzed_at = detection.get("analyzed_at")

    if analyzed_at:
        if hasattr(analyzed_at, "strftime"):
            analysis_date = analyzed_at.strftime(
                "%d %b %Y, %I:%M %p"
            )
        else:
            analysis_date = str(analyzed_at)
    else:
        analysis_date = "N/A"

    panel_name = str(panel.get("panel_name") or "N/A")
    location = str(panel.get("location") or "N/A")

    detail_rows = [
        ["Solar Panel", panel_name],
        ["Location", location],
        ["Detected Condition", condition],
        ["Confidence Score", confidence_text],
        ["Estimated Efficiency", efficiency_text],
        ["Maintenance Required", maintenance],
        ["Analysis Date", analysis_date]
    ]

    details = Table(
        [
            [
                Paragraph(
                    escape(label),
                    styles["ReportBody"]
                ),
                Paragraph(
                    escape(value),
                    styles["ReportBody"]
                )
            ]
            for label, value in detail_rows
        ],
        colWidths=[
            document.width * 0.36,
            document.width * 0.64
        ]
    )

    details.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), light_green),
        ("BACKGROUND", (1, 0), (1, -1), white),
        ("GRID", (0, 0), (-1, -1), 0.5, border),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8)
    ]))

    story.append(details)
    story.append(Spacer(1, 17))

    # --------------------------------------------------
    # 8. MAINTENANCE STATUS
    # --------------------------------------------------

    story.append(Paragraph(
        "MAINTENANCE STATUS",
        styles["ReportSection"]
    ))

    status_style = ParagraphStyle(
        "MaintenanceStatus",
        parent=styles["ReportValue"],
        textColor=maintenance_color,
        fontSize=11
    )

    status_box = Table(
        [[Paragraph(
            "Maintenance required: "
            + escape(maintenance),
            status_style
        )]],
        colWidths=[document.width]
    )

    status_box.setStyle(TableStyle([
        (
            "BACKGROUND",
            (0, 0), (-1, -1),
            light_green
            if maintenance == "No"
            else colors.HexColor("#FFF5E5")
            if maintenance == "Yes"
            else light_blue
        ),
        ("BOX", (0, 0), (-1, -1), 0.7, border),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10)
    ]))

    story.append(status_box)
    story.append(Spacer(1, 15))

    # --------------------------------------------------
    # 9. AI RECOMMENDATION
    # --------------------------------------------------

    story.append(Paragraph(
        "AI RECOMMENDATION",
        styles["ReportSection"]
    ))

    recommendation = str(
        detection.get("ai_recommendation")
        or "No recommendation available."
    )

    recommendation_box = Table(
        [[Paragraph(
            escape(recommendation),
            styles["ReportRecommendation"]
        )]],
        colWidths=[document.width]
    )

    recommendation_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), light_green),
        (
            "BOX",
            (0, 0), (-1, -1),
            1,
            colors.HexColor("#A8DDBB")
        ),
        ("LINEBEFORE", (0, 0), (0, -1), 4, green),
        ("LEFTPADDING", (0, 0), (-1, -1), 13),
        ("RIGHTPADDING", (0, 0), (-1, -1), 13),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12)
    ]))

    story.append(KeepTogether([
        recommendation_box,
        Spacer(1, 15),
        Paragraph(
            "<b>Important Note</b>",
            styles["ReportBody"]
        ),
        Spacer(1, 4),
        Paragraph(
            "The estimated efficiency is an AI-based estimate, "
            "not a direct measurement of actual electrical output. "
            "Possible electrical or physical damage should be "
            "verified by a qualified technician.",
            styles["ReportSmall"]
        )
    ]))

    # --------------------------------------------------
    # 10. HEADER AND FOOTER
    # --------------------------------------------------

    def draw_page(canvas, doc):
        canvas.saveState()

        page_width, page_height = A4

        # Header background
        canvas.setFillColor(navy)
        canvas.rect(
            0,
            page_height - 72,
            page_width,
            72,
            fill=1,
            stroke=0
        )

        # Green accent
        canvas.setFillColor(green)
        canvas.rect(
            0,
            page_height - 75,
            page_width,
            3,
            fill=1,
            stroke=0
        )

        canvas.setFillColor(white)
        canvas.setFont("Helvetica-Bold", 19)
        canvas.drawString(42, page_height - 34, "SolarGuard AI")

        canvas.setFillColor(
            colors.HexColor("#DCE8F5")
        )
        canvas.setFont("Helvetica", 8)
        canvas.drawString(
            42,
            page_height - 51,
            "SOLAR PANEL MAINTENANCE & PERFORMANCE MONITORING"
        )

        canvas.setFillColor(green)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawRightString(
            page_width - 42,
            page_height - 37,
            f"REPORT SG-{detection_id:05d}"
        )

        # Footer
        canvas.setStrokeColor(border)
        canvas.setLineWidth(0.6)
        canvas.line(
            42, 39,
            page_width - 42, 39
        )

        canvas.setFillColor(muted)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(
            42,
            25,
            "SolarGuard AI | AI-generated analysis"
        )

        canvas.drawRightString(
            page_width - 42,
            25,
            f"Page {doc.page}"
        )

        canvas.restoreState()

    # --------------------------------------------------
    # 11. GENERATE AND DOWNLOAD PDF
    # --------------------------------------------------

    document.build(
        story,
        onFirstPage=draw_page,
        onLaterPages=draw_page
    )

    pdf_buffer.seek(0)

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=(
            f"SolarGuard_AI_Report_{detection_id}.pdf"
        )
    )
