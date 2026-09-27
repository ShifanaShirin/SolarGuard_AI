from database.db import get_connection
import os

from flask import current_app

from werkzeug.utils import secure_filename

class MaintenanceService:
    @staticmethod
    def get_user_requests(user_id):

        connection = get_connection()

        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                mr.request_id,
                sp.panel_name,
                mr.issue_type,
                mr.priority,
                mr.request_status,
                mr.request_date
            FROM maintenance_requests mr
            JOIN solar_panels sp
            ON mr.panel_id = sp.panel_id
            WHERE mr.user_id = %s
            ORDER BY mr.request_date DESC
            """

        cursor.execute(query, (user_id,))

        requests = cursor.fetchall()

        cursor.close()
        connection.close()

        return requests

    @staticmethod
    def get_user_panels(user_id):

        connection = get_connection()

        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                panel_id,
                panel_name
            FROM solar_panels
            WHERE user_id=%s
            ORDER BY panel_name
        """

        cursor.execute(query, (user_id,))

        panels = cursor.fetchall()

        cursor.close()
        connection.close()

        return panels

    @staticmethod
    def create_request(user_id, form_data, image_file):

        connection = get_connection()

        cursor = connection.cursor()

        image_path = None

        if image_file and image_file.filename:

            upload_folder = os.path.join(
                current_app.static_folder,
                "uploads",
                "maintenance"
            )

            os.makedirs(upload_folder, exist_ok=True)

            filename = secure_filename(image_file.filename)

            image_file.save(
                os.path.join(upload_folder, filename)
            )

            image_path = f"uploads/maintenance/{filename}"

        query = """
            INSERT INTO maintenance_requests
            (
                panel_id,
                user_id,
                issue_type,
                description,
                priority,
                image_path
            )

            VALUES
            (%s,%s,%s,%s,%s,%s)
        """

        cursor.execute(
            query,
            (
                form_data["panel_id"],
                user_id,
                form_data["issue_type"],
                form_data["description"],
                form_data["priority"],
                image_path
            )
        )

        connection.commit()

        cursor.close()

        connection.close()

        return True

    @staticmethod
    def get_request_by_id(request_id, user_id):

        connection = get_connection()

        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT

            mr.*,

            sp.panel_name,

            sp.location

        FROM maintenance_requests mr

        JOIN solar_panels sp

        ON mr.panel_id = sp.panel_id

        WHERE

            mr.request_id=%s

            AND

            mr.user_id=%s
        """

        cursor.execute(
            query,
            (request_id, user_id)
        )

        request_data = cursor.fetchone()

        cursor.close()

        connection.close()

        return request_data

    @staticmethod
    def update_request(request_id, user_id, form_data):

        connection = get_connection()

        cursor = connection.cursor()

        query = """
        UPDATE maintenance_requests

        SET

            panel_id=%s,

            issue_type=%s,

            description=%s,

            priority=%s

        WHERE

            request_id=%s

            AND

            user_id=%s

            AND

            request_status='Pending'
        """

        cursor.execute(
            query,
            (
                form_data["panel_id"],
                form_data["issue_type"],
                form_data["description"],
                form_data["priority"],
                request_id,
                user_id
            )
        )

        connection.commit()

        updated = cursor.rowcount > 0

        cursor.close()

        connection.close()

        return updated

    @staticmethod
    def cancel_request(request_id, user_id):

        connection = get_connection()

        cursor = connection.cursor()

        query = """
        UPDATE maintenance_requests

        SET request_status='Cancelled'

        WHERE

            request_id=%s

            AND

            user_id=%s

            AND

            request_status='Pending'
        """

        cursor.execute(
            query,
            (
                request_id,
                user_id
            )
        )

        connection.commit()

        success = cursor.rowcount > 0

        cursor.close()

        connection.close()

        return success

    @staticmethod
    def get_request_statistics(user_id):

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT

            COUNT(*) AS total,

            SUM(request_status='Pending') AS pending,

            SUM(request_status='Completed') AS completed,

            SUM(request_status='Cancelled') AS cancelled

        FROM maintenance_requests

        WHERE user_id=%s
        """

        cursor.execute(query, (user_id,))

        stats = cursor.fetchone()

        cursor.close()
        connection.close()

        return stats

    @staticmethod
    def get_maintenance_report(request_id):

        connection = get_connection()

        if connection is None:
            return None

        cursor = None

        try:

            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT

                    mr.report_id,
                    mr.request_id,
                    mr.technician_id,

                    mr.inspection_notes,
                    mr.repair_details,
                    mr.parts_replaced,
                    mr.service_image,
                    mr.completion_date,
                    mr.report_status,
                    mr.created_at,

                    m.issue_type,
                    m.priority,
                    m.request_status,
                    m.request_date,

                    sp.panel_name,
                    sp.manufacturer,
                    sp.model_number,
                    sp.capacity,
                    sp.location,

                    u.user_id,
                    u.full_name AS customer_name,
                    u.email AS customer_email,

                    t.full_name AS technician_name

                FROM maintenance_reports mr

                INNER JOIN maintenance_requests m
                    ON mr.request_id = m.request_id

                INNER JOIN solar_panels sp
                    ON m.panel_id = sp.panel_id

                INNER JOIN users u
                    ON m.user_id = u.user_id

                LEFT JOIN users t
                    ON mr.technician_id = t.user_id

                WHERE mr.request_id = %s
            """

            cursor.execute(
                query,
                (request_id,)
            )

            return cursor.fetchone()

        finally:

            if cursor:
                cursor.close()

            connection.close()