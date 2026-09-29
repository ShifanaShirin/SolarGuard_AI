from datetime import date

from database.db import get_connection


class PanelService:

    @staticmethod
    def register_panel(data):

        required_fields = [
            "panel_name",
            "manufacturer",
            "model_number",
            "capacity",
            "installation_date",
            "location",
            "serial_number",
            "user_id"
        ]

        # Required field validation
        for field in required_fields:

            if not data.get(field):
                return f"{field.replace('_', ' ').title()} is required."

        # Capacity validation
        try:

            capacity = float(data["capacity"])

            if capacity <= 0:
                return "Capacity must be greater than zero."

        except ValueError:

            return "Invalid capacity."

        # Installation date validation
        installation_date = date.fromisoformat(
            data["installation_date"]
        )

        if installation_date > date.today():

            return "Installation date cannot be in the future."

        # Calculate panel age
        panel_age = (
            date.today().year -
            installation_date.year
        )

        connection = get_connection()

        if connection is None:
            return "Database connection failed."

        try:

            cursor = connection.cursor(dictionary=True)

            # Duplicate Serial Number
            cursor.execute(
                """
                SELECT panel_id
                FROM solar_panels
                WHERE serial_number=%s
                """,
                (data["serial_number"],)
            )

            panel = cursor.fetchone()

            if panel:
                return "Serial Number already exists."

            cursor.execute(
                """
                INSERT INTO solar_panels
                (
                    user_id,
                    panel_name,
                    manufacturer,
                    model_number,
                    capacity,
                    installation_date,
                    location,
                    serial_number,
                    panel_age
                )

                VALUES
                (
                    %s,%s,%s,%s,%s,%s,%s,%s,%s
                )
                """,
                (
                    data["user_id"],
                    data["panel_name"],
                    data["manufacturer"],
                    data["model_number"],
                    data["capacity"],
                    data["installation_date"],
                    data["location"],
                    data["serial_number"],
                    panel_age
                )
            )

            connection.commit()

            return "Panel Registered Successfully"

        except Exception as e:

            print(e)

            return "Failed to register panel."

        finally:

            cursor.close()

            connection.close()
    
    @staticmethod
    def get_user_panels(user_id):

        connection = get_connection()

        if connection is None:
            return []

        try:

            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT *
                FROM solar_panels
                WHERE user_id=%s
                ORDER BY created_at DESC
                """,
                (user_id,)
            )

            panels = cursor.fetchall()

            return panels

        finally:

            cursor.close()
            connection.close()
    
    @staticmethod
    def get_panel_by_id(panel_id, user_id):

        connection = get_connection()

        if connection is None:
            return None

        try:

            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT *
                FROM solar_panels
                WHERE panel_id=%s
                AND user_id=%s
                """,
                (
                    panel_id,
                    user_id
                )
            )

            return cursor.fetchone()

        finally:

            cursor.close()
            connection.close()

    @staticmethod
    def get_panel(panel_id, user_id):

        connection = get_connection()

        if connection is None:
            return None

        try:

            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT *
                FROM solar_panels
                WHERE panel_id=%s
                AND user_id=%s
                """,
                (panel_id, user_id)
            )

            return cursor.fetchone()

        finally:

            cursor.close()
            connection.close()


    @staticmethod
    def update_panel(panel_id, user_id, data):

        required_fields = [
            "panel_name",
            "manufacturer",
            "model_number",
            "capacity",
            "installation_date",
            "location",
            "serial_number"
        ]

        for field in required_fields:

            if not data.get(field):
                return f"{field.replace('_',' ').title()} is required."

        # Capacity Validation

        try:

            capacity = float(data["capacity"])

            if capacity <= 0:
                return "Capacity must be greater than zero."

        except ValueError:

            return "Invalid Capacity."

        # Installation Date Validation

        installation_date = date.fromisoformat(
            data["installation_date"]
        )

        if installation_date > date.today():

            return "Installation date cannot be in the future."

        connection = get_connection()

        if connection is None:
            return "Database connection failed."

        try:

            cursor = connection.cursor(dictionary=True)

            # Duplicate Serial Number Check

            cursor.execute(
                """
                SELECT panel_id

                FROM solar_panels

                WHERE serial_number=%s

                AND panel_id<>%s
                """,
                (
                    data["serial_number"],
                    panel_id
                )
            )

            existing = cursor.fetchone()

            if existing:

                return "Serial Number already exists."

            # Calculate Panel Age

            panel_age = (
                date.today().year -
                installation_date.year
            )

            cursor.execute(
                """
                UPDATE solar_panels

                SET

                    panel_name=%s,
                    manufacturer=%s,
                    model_number=%s,
                    capacity=%s,
                    installation_date=%s,
                    location=%s,
                    serial_number=%s,
                    panel_age=%s

                WHERE

                    panel_id=%s

                    AND user_id=%s
                """,
                (
                    data["panel_name"],
                    data["manufacturer"],
                    data["model_number"],
                    data["capacity"],
                    data["installation_date"],
                    data["location"],
                    data["serial_number"],
                    panel_age,
                    panel_id,
                    user_id
                )
            )

            connection.commit()

            return "Panel Updated Successfully"

        finally:

            cursor.close()
            connection.close()

    @staticmethod
    def delete_panel(panel_id, user_id):

        connection = get_connection()

        if connection is None:
            return "Database connection failed."

        try:

            cursor = connection.cursor()

            cursor.execute(
                """
                DELETE

                FROM solar_panels

                WHERE panel_id=%s

                AND user_id=%s
                """,
                (
                    panel_id,
                    user_id
                )
            )

            connection.commit()

            return "Panel Deleted Successfully"

        finally:

            cursor.close()
            connection.close()

    # =========================================================
    # PANEL PERFORMANCE ANALYTICS
    # =========================================================

    @staticmethod
    def get_panel_performance_analytics(panel_id):

        connection = get_connection()

        if connection is None:
            return {
                "total_analyses": 0,
                "current_efficiency": None,
                "average_efficiency": None,
                "highest_efficiency": None,
                "lowest_efficiency": None,
                "maintenance_required": 0,
                "clean_count": 0,
                "fault_count": 0,
                "detections": []
            }

        cursor = None

        try:

            cursor = connection.cursor(dictionary=True)

            # -------------------------------------------------
            # Get all AI analyses for this panel
            # -------------------------------------------------

            cursor.execute(
                """
                SELECT
                    detection_id,
                    detected_defect,
                    confidence_score,
                    estimated_efficiency,
                    maintenance_required,
                    analyzed_at

                FROM ai_detection_results

                WHERE panel_id = %s

                ORDER BY analyzed_at ASC
                """,
                (panel_id,)
            )

            detections = cursor.fetchall()

            # -------------------------------------------------
            # No AI analysis available
            # -------------------------------------------------

            if not detections:

                return {
                    "total_analyses": 0,
                    "current_efficiency": None,
                    "average_efficiency": None,
                    "highest_efficiency": None,
                    "lowest_efficiency": None,
                    "maintenance_required": 0,
                    "clean_count": 0,
                    "fault_count": 0,
                    "detections": []
                }

            # -------------------------------------------------
            # Efficiency values
            # -------------------------------------------------

            efficiency_values = []

            for detection in detections:

                if detection["estimated_efficiency"] is not None:

                    efficiency_values.append(
                        float(
                            detection["estimated_efficiency"]
                        )
                    )

            # -------------------------------------------------
            # Latest efficiency
            # -------------------------------------------------

            current_efficiency = None

            for detection in reversed(detections):

                if detection["estimated_efficiency"] is not None:

                    current_efficiency = float(
                        detection["estimated_efficiency"]
                    )

                    break

            # -------------------------------------------------
            # Average / highest / lowest
            # -------------------------------------------------

            if efficiency_values:

                average_efficiency = round(
                    sum(efficiency_values)
                    / len(efficiency_values),
                    2
                )

                highest_efficiency = max(
                    efficiency_values
                )

                lowest_efficiency = min(
                    efficiency_values
                )

            else:

                average_efficiency = None
                highest_efficiency = None
                lowest_efficiency = None

            # -------------------------------------------------
            # Maintenance required count
            # -------------------------------------------------

            maintenance_required = sum(
                1
                for detection in detections
                if detection["maintenance_required"] == "Yes"
            )

            # -------------------------------------------------
            # Clean / fault count
            # -------------------------------------------------

            clean_count = sum(
                1
                for detection in detections
                if detection["detected_defect"] == "Clean"
            )

            fault_count = (
                len(detections)
                - clean_count
            )

            # -------------------------------------------------
            # Prepare chart/trend data
            # -------------------------------------------------

            trend = []

            for detection in detections:

                if detection["estimated_efficiency"] is not None:

                    trend.append(
                        {
                            "date": detection["analyzed_at"],
                            "efficiency": float(
                                detection["estimated_efficiency"]
                            ),
                            "defect": detection["detected_defect"]
                        }
                    )

            return {
                "total_analyses": len(detections),

                "current_efficiency":
                    current_efficiency,

                "average_efficiency":
                    average_efficiency,

                "highest_efficiency":
                    highest_efficiency,

                "lowest_efficiency":
                    lowest_efficiency,

                "maintenance_required":
                    maintenance_required,

                "clean_count":
                    clean_count,

                "fault_count":
                    fault_count,

                "detections":
                    trend
            }

        except Exception as e:

            print(
                "Panel Performance Analytics Error:",
                e
            )

            return {
                "total_analyses": 0,
                "current_efficiency": None,
                "average_efficiency": None,
                "highest_efficiency": None,
                "lowest_efficiency": None,
                "maintenance_required": 0,
                "clean_count": 0,
                "fault_count": 0,
                "detections": []
            }

        finally:

            if cursor:
                cursor.close()

            connection.close()