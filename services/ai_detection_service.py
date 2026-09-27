from database.db import get_connection


class AIDetectionService:

    @staticmethod
    def save_detection(
        panel_id,
        request_id,
        image_path,
        detected_defect,
        confidence_score,
        estimated_efficiency,
        maintenance_required,
        ai_recommendation
    ):
        connection = get_connection()

        if connection is None:
            return False

        cursor = None

        try:
            cursor = connection.cursor()

            query = """
                INSERT INTO ai_detection_results
                (
                    panel_id,
                    request_id,
                    image_path,
                    detected_defect,
                    confidence_score,
                    estimated_efficiency,
                    maintenance_required,
                    ai_recommendation
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            values = (
                panel_id,
                request_id,
                image_path,
                detected_defect,
                confidence_score,
                estimated_efficiency,
                maintenance_required,
                ai_recommendation
            )

            cursor.execute(query, values)
            connection.commit()

            return cursor.lastrowid

        except Exception as e:
            connection.rollback()
            print("AI Detection Save Error:", e)
            return False

        finally:
            if cursor:
                cursor.close()

            connection.close()

    @staticmethod
    def get_detection_by_id(detection_id):
        connection = get_connection()

        if connection is None:
            return None

        cursor = None

        try:
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT *
                FROM ai_detection_results
                WHERE detection_id = %s
            """

            cursor.execute(query, (detection_id,))

            return cursor.fetchone()

        except Exception as e:
            print("AI Detection Fetch Error:", e)
            return None

        finally:
            if cursor:
                cursor.close()

            connection.close()

    @staticmethod
    def get_panel_detections(panel_id):
        connection = get_connection()

        if connection is None:
            return []

        cursor = None

        try:
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT *
                FROM ai_detection_results
                WHERE panel_id = %s
                ORDER BY analyzed_at DESC
            """

            cursor.execute(query, (panel_id,))

            return cursor.fetchall()

        except Exception as e:
            print("Panel AI Detection Fetch Error:", e)
            return []

        finally:
            if cursor:
                cursor.close()

            connection.close()

    @staticmethod
    def get_user_detections(user_id):
        connection = get_connection()

        if connection is None:
            return []

        cursor = None

        try:
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT
                    d.*,
                    p.panel_name,
                    p.location
                FROM ai_detection_results d
                INNER JOIN solar_panels p
                    ON d.panel_id = p.panel_id
                WHERE p.user_id = %s
                ORDER BY d.analyzed_at DESC
            """

            cursor.execute(query, (user_id,))

            return cursor.fetchall()

        except Exception as e:
            print("User AI Detection Fetch Error:", e)
            return []

        finally:
            if cursor:
                cursor.close()

            connection.close()