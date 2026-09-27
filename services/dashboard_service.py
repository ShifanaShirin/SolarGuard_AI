from database.db import get_connection


class DashboardService:

    @staticmethod
    def get_dashboard_stats(user_id):

        connection = get_connection()

        if connection is None:

            return {
                "panels": 0,
                "maintenance": 0,
                "detections": 0,
                "efficiency": "--"
            }

        try:

            cursor = connection.cursor(dictionary=True)

            # Registered Panels

            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM solar_panels
                WHERE user_id=%s
                """,
                (user_id,)
            )

            panels = cursor.fetchone()["total"]

            # Maintenance Requests

            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM maintenance_requests
                WHERE user_id=%s
                """,
                (user_id,)
            )

            maintenance = cursor.fetchone()["total"]

            # AI Detections

            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM ai_detection_results adr
                JOIN solar_panels sp
                ON adr.panel_id = sp.panel_id
                WHERE sp.user_id=%s
                """,
                (user_id,)
            )

            detections = cursor.fetchone()["total"]

            # Average Efficiency

            cursor.execute(
                """
                SELECT
                    ROUND(
                        AVG(estimated_efficiency),
                        2
                    ) AS avg_efficiency

                FROM ai_detection_results adr

                JOIN solar_panels sp

                ON adr.panel_id=sp.panel_id

                WHERE sp.user_id=%s
                """,
                (user_id,)
            )

            efficiency = cursor.fetchone()["avg_efficiency"]

            if efficiency is None:
                efficiency = "--"

            return {

                "panels": panels,

                "maintenance": maintenance,

                "detections": detections,

                "efficiency": efficiency

            }

        finally:

            cursor.close()
            connection.close()
    
    @staticmethod
    def get_recent_panels(user_id):

        connection = get_connection()

        if connection is None:
            return []

        try:

            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT
                    panel_name,
                    capacity,
                    installation_date,
                    location
                FROM solar_panels
                WHERE user_id=%s
                ORDER BY created_at DESC
                LIMIT 5
                """,
                (user_id,)
            )

            return cursor.fetchall()

        finally:

            cursor.close()
            connection.close()