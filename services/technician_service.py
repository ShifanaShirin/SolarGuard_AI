from database.db import get_connection


class TechnicianService:

    # =====================================================
    # DASHBOARD STATISTICS
    # =====================================================

    @staticmethod
    def get_dashboard_stats(technician_id):

        connection = get_connection()

        if connection is None:

            return {
                "assigned": 0,
                "accepted": 0,
                "in_progress": 0,
                "completed": 0
            }

        cursor = None

        try:

            cursor = connection.cursor(dictionary=True)

            # Assigned
            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM technician_assignments
                WHERE technician_id = %s
                AND assignment_status = 'Assigned'
                """,
                (technician_id,)
            )

            assigned = cursor.fetchone()["total"]


            # Accepted
            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM technician_assignments
                WHERE technician_id = %s
                AND assignment_status = 'Accepted'
                """,
                (technician_id,)
            )

            accepted = cursor.fetchone()["total"]


            # In Progress
            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM technician_assignments
                WHERE technician_id = %s
                AND assignment_status = 'In Progress'
                """,
                (technician_id,)
            )

            in_progress = cursor.fetchone()["total"]


            # Completed
            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM technician_assignments
                WHERE technician_id = %s
                AND assignment_status = 'Completed'
                """,
                (technician_id,)
            )

            completed = cursor.fetchone()["total"]


            return {
                "assigned": assigned,
                "accepted": accepted,
                "in_progress": in_progress,
                "completed": completed
            }


        finally:

            if cursor:

                cursor.close()

            connection.close()


    # =====================================================
    # ASSIGNED MAINTENANCE REQUESTS
    # =====================================================

    @staticmethod
    def get_assigned_requests(technician_id):

        connection = get_connection()

        if connection is None:

            return []

        cursor = None

        try:

            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT

                    ta.assignment_id,
                    ta.request_id,
                    ta.assigned_date,
                    ta.assignment_status,

                    mr.issue_type,
                    mr.description,
                    mr.priority,
                    mr.request_status,
                    mr.image_path,
                    mr.request_date,

                    sp.panel_id,
                    sp.panel_name,
                    sp.manufacturer,
                    sp.model_number,
                    sp.capacity,
                    sp.location,

                    u.user_id,
                    u.full_name AS customer_name,
                    u.email AS customer_email,
                    u.phone AS customer_phone

                FROM technician_assignments ta

                INNER JOIN maintenance_requests mr
                    ON ta.request_id = mr.request_id

                INNER JOIN solar_panels sp
                    ON mr.panel_id = sp.panel_id

                INNER JOIN users u
                    ON mr.user_id = u.user_id

                WHERE ta.technician_id = %s

                ORDER BY ta.assigned_date DESC
                """,
                (technician_id,)
            )

            return cursor.fetchall()


        finally:

            if cursor:

                cursor.close()

            connection.close()

    # =====================================================
    # MAINTENANCE REQUEST DETAILS
    # =====================================================

    @staticmethod
    def get_request_details(technician_id, request_id):

        connection = get_connection()

        if connection is None:
            return None

        cursor = None

        try:

            cursor = connection.cursor(dictionary=True)

            cursor.execute(
    """
    SELECT

        ta.assignment_id,
        ta.request_id,
        ta.technician_id,
        ta.assigned_by,
        ta.assigned_date,
        ta.assignment_status,

        mr.user_id,
        mr.panel_id,
        mr.issue_type,
        mr.description,
        mr.priority,
        mr.request_status,
        mr.image_path,
        mr.request_date,

        sp.panel_name,
        sp.manufacturer,
        sp.model_number,
        sp.capacity,
        sp.installation_date,
        sp.location,
        sp.serial_number,
        sp.panel_age,

        u.full_name AS customer_name,
        u.email AS customer_email,
        u.phone AS customer_phone,

        mrpt.report_id,
        mrpt.inspection_notes,
        mrpt.repair_details,
        mrpt.parts_replaced,
        mrpt.service_image,
        mrpt.completion_date,
        mrpt.report_status

    FROM technician_assignments ta

    INNER JOIN maintenance_requests mr
        ON ta.request_id = mr.request_id

    INNER JOIN solar_panels sp
        ON mr.panel_id = sp.panel_id

    INNER JOIN users u
        ON mr.user_id = u.user_id

    LEFT JOIN maintenance_reports mrpt
        ON mrpt.request_id = mr.request_id
        AND mrpt.technician_id = ta.technician_id

    WHERE ta.request_id = %s
    AND ta.technician_id = %s

    LIMIT 1
    """,
    (
        request_id,
        technician_id
    )
)

            return cursor.fetchone()

        finally:

            if cursor:
                cursor.close()

            connection.close()

    # =====================================================
    # ACCEPT MAINTENANCE JOB
    # =====================================================

    @staticmethod
    def accept_request(technician_id, request_id):

        connection = get_connection()

        if connection is None:
            return False

        cursor = None

        try:

            cursor = connection.cursor(dictionary=True)

            # -------------------------------------------------
            # Get customer/user ID
            # -------------------------------------------------

            cursor.execute(
                """
                SELECT user_id
                FROM maintenance_requests
                WHERE request_id = %s
                """,
                (request_id,)
            )

            request_data = cursor.fetchone()

            if not request_data:
                return False

            user_id = request_data["user_id"]

            # -------------------------------------------------
            # Accept assignment
            # -------------------------------------------------

            cursor.execute(
                """
                UPDATE technician_assignments

                SET assignment_status = 'Accepted'

                WHERE request_id = %s
                AND technician_id = %s
                AND assignment_status = 'Assigned'
                """,
                (
                    request_id,
                    technician_id
                )
            )

            if cursor.rowcount == 0:
                connection.rollback()
                return False

            # -------------------------------------------------
            # Notification to customer
            # -------------------------------------------------

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
                    "Maintenance Request Accepted",
                    (
                        f"Your maintenance request #{request_id} "
                        "has been accepted by the assigned technician."
                    ),
                    "Maintenance",
                    0
                )
            )

            connection.commit()

            return True

        except Exception as e:

            connection.rollback()

            print("Accept request error:", e)

            return False

        finally:

            if cursor:
                cursor.close()

            connection.close()

    # =====================================================
    # START MAINTENANCE JOB
    # =====================================================

    @staticmethod
    def start_request(technician_id, request_id):

        connection = get_connection()

        if connection is None:
            return False

        cursor = None

        try:

            cursor = connection.cursor(dictionary=True)

            # -------------------------------------------------
            # Get customer/user ID
            # -------------------------------------------------

            cursor.execute(
                """
                SELECT user_id
                FROM maintenance_requests
                WHERE request_id = %s
                """,
                (request_id,)
            )

            request_data = cursor.fetchone()

            if not request_data:
                return False

            user_id = request_data["user_id"]

            # -------------------------------------------------
            # Update technician assignment
            # -------------------------------------------------

            cursor.execute(
                """
                UPDATE technician_assignments

                SET assignment_status = 'In Progress'

                WHERE request_id = %s
                AND technician_id = %s
                AND assignment_status = 'Accepted'
                """,
                (
                    request_id,
                    technician_id
                )
            )

            if cursor.rowcount == 0:

                connection.rollback()

                return False

            # -------------------------------------------------
            # Update maintenance request
            # -------------------------------------------------

            cursor.execute(
                """
                UPDATE maintenance_requests

                SET request_status = 'In Progress'

                WHERE request_id = %s
                """,
                (request_id,)
            )

            # -------------------------------------------------
            # Notification to customer
            # -------------------------------------------------

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
                    "Maintenance Work Started",
                    (
                        f"Maintenance work has started for "
                        f"your request #{request_id}."
                    ),
                    "Maintenance",
                    0
                )
            )

            connection.commit()

            return True

        except Exception as e:

            connection.rollback()

            print("Start request error:", e)

            return False

        finally:

            if cursor:
                cursor.close()

            connection.close()

    # =====================================================
    # COMPLETE MAINTENANCE JOB
    # =====================================================

    @staticmethod
    def complete_request(
        technician_id,
        request_id,
        inspection_notes,
        repair_details,
        parts_replaced,
        service_image
    ):

        connection = get_connection()

        if connection is None:
            return False

        cursor = None

        try:

            cursor = connection.cursor(dictionary=True)

            # -------------------------------------------------
            # Get customer/user ID
            # -------------------------------------------------

            cursor.execute(
                """
                SELECT user_id
                FROM maintenance_requests
                WHERE request_id = %s
                """,
                (request_id,)
            )

            request_data = cursor.fetchone()

            if not request_data:
                return False

            user_id = request_data["user_id"]

            # -------------------------------------------------
            # Check assignment
            # -------------------------------------------------

            cursor.execute(
                """
                SELECT assignment_id
                FROM technician_assignments

                WHERE request_id = %s
                AND technician_id = %s
                AND assignment_status = 'In Progress'
                """,
                (
                    request_id,
                    technician_id
                )
            )

            assignment = cursor.fetchone()

            if not assignment:
                return False

            # -------------------------------------------------
            # Create maintenance report
            # -------------------------------------------------

            cursor.execute(
                """
                INSERT INTO maintenance_reports
                (
                    request_id,
                    technician_id,
                    inspection_notes,
                    repair_details,
                    parts_replaced,
                    service_image,
                    completion_date,
                    report_status
                )

                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    NOW(),
                    'Completed'
                )
                """,
                (
                    request_id,
                    technician_id,
                    inspection_notes,
                    repair_details,
                    parts_replaced,
                    service_image
                )
            )

            # -------------------------------------------------
            # Update technician assignment
            # -------------------------------------------------

            cursor.execute(
                """
                UPDATE technician_assignments

                SET assignment_status = 'Completed'

                WHERE request_id = %s
                AND technician_id = %s
                """,
                (
                    request_id,
                    technician_id
                )
            )

            # -------------------------------------------------
            # Update maintenance request
            # -------------------------------------------------

            cursor.execute(
                """
                UPDATE maintenance_requests

                SET request_status = 'Completed'

                WHERE request_id = %s
                """,
                (request_id,)
            )

            # -------------------------------------------------
            # Notification to customer
            # -------------------------------------------------

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
                    "Maintenance Completed",
                    (
                        f"Your maintenance request #{request_id} "
                        "has been completed. Your service report "
                        "is now available."
                    ),
                    "Maintenance",
                    0
                )
            )

            connection.commit()

            return True

        except Exception as e:

            connection.rollback()

            print("Complete request error:", e)

            return False

        finally:

            if cursor:
                cursor.close()

            connection.close()

    # =====================================================
    # GET MAINTENANCE REPORT
    # =====================================================

    @staticmethod
    def get_maintenance_report(
        technician_id,
        request_id
    ):

        connection = get_connection()

        if connection is None:
            return None

        cursor = None

        try:

            cursor = connection.cursor(
                dictionary=True
            )

            cursor.execute(
                """
                SELECT

                    mrpt.report_id,
                    mrpt.request_id,
                    mrpt.technician_id,
                    mrpt.inspection_notes,
                    mrpt.repair_details,
                    mrpt.parts_replaced,
                    mrpt.service_image,
                    mrpt.completion_date,
                    mrpt.report_status,
                    mrpt.created_at,

                    mr.issue_type,
                    mr.description,
                    mr.priority,

                    sp.panel_name,
                    sp.manufacturer,
                    sp.model_number,
                    sp.capacity,
                    sp.location,

                    u.full_name AS customer_name,
                    u.email AS customer_email,
                    u.phone AS customer_phone

                FROM maintenance_reports mrpt

                INNER JOIN maintenance_requests mr
                    ON mrpt.request_id = mr.request_id

                INNER JOIN solar_panels sp
                    ON mr.panel_id = sp.panel_id

                INNER JOIN users u
                    ON mr.user_id = u.user_id

                WHERE mrpt.request_id = %s
                AND mrpt.technician_id = %s

                LIMIT 1
                """,
                (
                    request_id,
                    technician_id
                )
            )

            return cursor.fetchone()

        finally:

            if cursor:
                cursor.close()

            connection.close()