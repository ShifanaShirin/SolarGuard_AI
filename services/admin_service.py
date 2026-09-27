from database.db import get_connection


class AdminService:

    @staticmethod
    def get_dashboard_stats():

        connection = get_connection()

        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT

            (SELECT COUNT(*) FROM users WHERE role='User') AS users,

            (SELECT COUNT(*) FROM solar_panels) AS panels,

            (SELECT COUNT(*)
             FROM maintenance_requests
             WHERE request_status='Pending') AS pending_requests,

            (SELECT COUNT(*)
             FROM users
             WHERE role='Technician') AS technicians
        """

        cursor.execute(query)

        stats = cursor.fetchone()

        cursor.close()
        connection.close()

        return stats

    @staticmethod
    def get_all_maintenance_requests():

        connection = get_connection()

        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                mr.request_id,
                mr.issue_type,
                mr.description,
                mr.priority,
                mr.request_status,
                mr.image_path,
                mr.request_date,

                u.full_name AS user_name,
                u.email AS user_email,

                sp.panel_name,
                sp.location,
                sp.capacity

            FROM maintenance_requests mr

            INNER JOIN users u
                ON mr.user_id = u.user_id

            INNER JOIN solar_panels sp
                ON mr.panel_id = sp.panel_id

            ORDER BY mr.request_date DESC
        """

        cursor.execute(query)

        requests = cursor.fetchall()

        cursor.close()
        connection.close()

        return requests

    @staticmethod
    def get_maintenance_request_details(request_id):

        connection = get_connection()

        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                mr.request_id,
                mr.issue_type,
                mr.description,
                mr.priority,
                mr.request_status,
                mr.image_path,
                mr.request_date,

                u.user_id,
                u.full_name AS user_name,
                u.email AS user_email,
                u.phone AS user_phone,

                sp.panel_id,
                sp.panel_name,
                sp.manufacturer,
                sp.model_number,
                sp.capacity,
                sp.installation_date,
                sp.location,
                sp.serial_number

            FROM maintenance_requests mr

            INNER JOIN users u
                ON mr.user_id = u.user_id

            INNER JOIN solar_panels sp
                ON mr.panel_id = sp.panel_id

            WHERE mr.request_id = %s
        """

        cursor.execute(
            query,
            (request_id,)
        )

        maintenance_request = cursor.fetchone()

        cursor.close()
        connection.close()

        return maintenance_request

    @staticmethod
    def update_request_status(request_id, status):

        connection = get_connection()

        if connection is None:
            return False

        try:

            cursor = connection.cursor(dictionary=True)

            # Get the user who created the request
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

            # Update request status
            cursor.execute(
                """
                UPDATE maintenance_requests
                SET request_status = %s
                WHERE request_id = %s
                AND request_status = 'Pending'
                """,
                (
                    status,
                    request_id
                )
            )
            if cursor.rowcount == 0:
                return False


            # Create notification
            if status == "Approved":

                title = "Maintenance Request Approved"

                message = (
                    f"Your maintenance request #{request_id} "
                    "has been approved by the administrator."
                )

            elif status == "Rejected":

                title = "Maintenance Request Rejected"

                message = (
                    f"Your maintenance request #{request_id} "
                    "has been rejected by the administrator."
                )

            else:

                title = "Maintenance Request Updated"

                message = (
                    f"Your maintenance request #{request_id} "
                    f"status has been changed to {status}."
                )

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
                    title,
                    message,
                    "Maintenance",
                    0
                )
            )

            connection.commit()

            return True

        except Exception as e:

            print("Admin status update error:", e)

            connection.rollback()

            return False

        finally:

            cursor.close()
            connection.close()

    @staticmethod
    def get_technicians():

        connection = get_connection()

        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                user_id,
                full_name,
                email,
                phone
            FROM users
            WHERE role = 'Technician'
            AND status = 'Active'
            ORDER BY full_name
            """
        )

        technicians = cursor.fetchall()

        cursor.close()
        connection.close()

        return technicians

    @staticmethod
    def assign_technician(request_id, technician_id, assigned_by):

        connection = get_connection()

        if connection is None:
            return False

        cursor = None

        try:

            cursor = connection.cursor(dictionary=True)

            # =====================================================
            # 1. Check maintenance request
            # =====================================================

            cursor.execute(
                """
                SELECT
                    request_id,
                    user_id,
                    request_status
                FROM maintenance_requests
                WHERE request_id = %s
                """,
                (request_id,)
            )

            maintenance_request = cursor.fetchone()

            if not maintenance_request:

                print("Maintenance request not found.")

                return False


            # =====================================================
            # 2. Check request status
            # =====================================================

            if maintenance_request["request_status"] != "Approved":

                print(
                    "Technician can only be assigned "
                    "to an approved maintenance request."
                )

                return False


            # =====================================================
            # 3. Check for existing active assignment
            # =====================================================

            cursor.execute(
                """
                SELECT
                    assignment_id,
                    technician_id,
                    assignment_status
                FROM technician_assignments
                WHERE request_id = %s
                AND assignment_status IN (
                    'Assigned',
                    'Accepted',
                    'In Progress'
                )
                """,
                (request_id,)
            )

            existing_assignment = cursor.fetchone()

            if existing_assignment:

                print(
                    "Technician already assigned to this request."
                )

                return False


            # =====================================================
            # 4. Check technician
            # =====================================================

            cursor.execute(
                """
                SELECT
                    user_id,
                    full_name,
                    email
                FROM users
                WHERE user_id = %s
                AND role = 'Technician'
                AND status = 'Active'
                """,
                (technician_id,)
            )

            technician = cursor.fetchone()

            if not technician:

                print(
                    "Technician not found or technician is inactive."
                )

                return False


            # =====================================================
            # 5. Create technician assignment
            # =====================================================

            cursor.execute(
                """
                INSERT INTO technician_assignments
                (
                    request_id,
                    technician_id,
                    assigned_by,
                    assignment_status
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    request_id,
                    technician_id,
                    assigned_by,
                    "Assigned"
                )
            )


            # =====================================================
            # 6. Update maintenance request status
            # =====================================================

            cursor.execute(
                """
                UPDATE maintenance_requests
                SET request_status = 'Assigned'
                WHERE request_id = %s
                """,
                (request_id,)
            )


            # =====================================================
            # 7. Notification for technician
            # =====================================================

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
                    technician_id,
                    "New Maintenance Assignment",
                    (
                        f"You have been assigned "
                        f"maintenance request #{request_id}."
                    ),
                    "Assignment",
                    0
                )
            )


            # =====================================================
            # 8. Notification for customer
            # =====================================================

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
                    maintenance_request["user_id"],
                    "Technician Assigned",
                    (
                        f"A technician has been assigned "
                        f"to your maintenance request "
                        f"#{request_id}."
                    ),
                    "Maintenance",
                    0
                )
            )


            # =====================================================
            # 9. Commit everything
            # =====================================================

            connection.commit()

            print(
                f"Technician {technician['full_name']} "
                f"assigned to request #{request_id}"
            )

            return True


        except Exception as e:

            print(
                "Technician assignment error:",
                e
            )

            connection.rollback()

            return False


        finally:

            if cursor:

                cursor.close()

            connection.close()

    # =========================================================
    # GET ALL USERS
    # =========================================================

    @staticmethod
    def get_all_users():

        connection = get_connection()

        if connection is None:
            return []

        cursor = None

        try:

            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT

                    u.user_id,
                    u.full_name,
                    u.email,
                    u.phone,
                    u.role,

                    COUNT(DISTINCT sp.panel_id)
                        AS panel_count,

                    COUNT(DISTINCT mr.request_id)
                        AS maintenance_count,

                    COUNT(
                        DISTINCT CASE
                            WHEN mr.request_status = 'Completed'
                            THEN mr.request_id
                        END
                    ) AS completed_count,

                    COUNT(
                        DISTINCT CASE
                            WHEN mr.request_status = 'Pending'
                            THEN mr.request_id
                        END
                    ) AS pending_count

                FROM users u

                LEFT JOIN solar_panels sp
                    ON u.user_id = sp.user_id

                LEFT JOIN maintenance_requests mr
                    ON u.user_id = mr.user_id

                WHERE u.role != 'Admin'

                GROUP BY
                    u.user_id,
                    u.full_name,
                    u.email,
                    u.phone,
                    u.role

                ORDER BY u.user_id DESC
            """

            cursor.execute(query)

            return cursor.fetchall()

        finally:

            if cursor:
                cursor.close()

            connection.close()


    # =========================================================
    # GET USER DETAILS
    # =========================================================

    @staticmethod
    def get_user_details(user_id):

        connection = get_connection()

        if connection is None:
            return None

        cursor = None

        try:

            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT

                    user_id,
                    full_name,
                    email,
                    phone,
                    role

                FROM users

                WHERE user_id = %s

                AND role != 'Admin'
            """

            cursor.execute(
                query,
                (user_id,)
            )

            return cursor.fetchone()

        finally:

            if cursor:
                cursor.close()

            connection.close()


    # =========================================================
    # GET USER PANELS
    # =========================================================

    @staticmethod
    def get_user_panels(user_id):

        connection = get_connection()

        if connection is None:
            return []

        cursor = None

        try:

            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT

                    panel_id,
                    panel_name,
                    manufacturer,
                    model_number,
                    capacity,
                    location,
                    installation_date

                FROM solar_panels

                WHERE user_id = %s

                ORDER BY panel_id DESC
            """

            cursor.execute(
                query,
                (user_id,)
            )

            return cursor.fetchall()

        finally:

            if cursor:
                cursor.close()

            connection.close()


    # =========================================================
    # GET USER MAINTENANCE REQUESTS
    # =========================================================

    @staticmethod
    def get_user_maintenance_requests(user_id):

        connection = get_connection()

        if connection is None:
            return []

        cursor = None

        try:

            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT

                    mr.request_id,
                    mr.issue_type,
                    mr.description,
                    mr.priority,
                    mr.request_status,
                    mr.request_date,

                    sp.panel_name

                FROM maintenance_requests mr

                INNER JOIN solar_panels sp
                    ON mr.panel_id = sp.panel_id

                WHERE mr.user_id = %s

                ORDER BY mr.request_date DESC
            """

            cursor.execute(
                query,
                (user_id,)
            )

            return cursor.fetchall()

        finally:

            if cursor:
                cursor.close()

            connection.close()

    # =========================================================
    # GET ALL TECHNICIANS
    # =========================================================

    @staticmethod
    def get_all_technicians():

        connection = get_connection()

        if connection is None:
            return []

        cursor = None

        try:

            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT

                    u.user_id AS technician_id,
                    u.full_name,
                    u.email,
                    u.phone,

                    COUNT(ta.assignment_id) AS total_jobs,

                    COALESCE(
                        SUM(
                            ta.assignment_status = 'Assigned'
                        ),
                        0
                    ) AS assigned_jobs,

                    COALESCE(
                        SUM(
                            ta.assignment_status = 'Accepted'
                        ),
                        0
                    ) AS accepted_jobs,

                    COALESCE(
                        SUM(
                            ta.assignment_status = 'In Progress'
                        ),
                        0
                    ) AS in_progress_jobs,

                    COALESCE(
                        SUM(
                            ta.assignment_status = 'Completed'
                        ),
                        0
                    ) AS completed_jobs

                FROM users u

                LEFT JOIN technician_assignments ta
                    ON u.user_id = ta.technician_id

                WHERE u.role = 'Technician'

                GROUP BY
                    u.user_id,
                    u.full_name,
                    u.email,
                    u.phone

                ORDER BY
                    u.full_name ASC
            """

            cursor.execute(query)

            technicians = cursor.fetchall()

            return technicians

        finally:

            if cursor:
                cursor.close()

            connection.close()


    # =========================================================
    # GET TECHNICIAN DETAILS
    # =========================================================

    @staticmethod
    def get_technician_details(technician_id):

        connection = get_connection()

        if connection is None:
            return None

        cursor = None

        try:

            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT

                    user_id AS technician_id,
                    full_name,
                    email,
                    phone,
                    role

                FROM users

                WHERE user_id = %s

                AND role = 'Technician'
            """

            cursor.execute(
                query,
                (technician_id,)
            )

            return cursor.fetchone()

        finally:

            if cursor:
                cursor.close()

            connection.close()


    # =========================================================
    # GET TECHNICIAN JOBS
    # =========================================================

    @staticmethod
    def get_technician_jobs(technician_id):

        connection = get_connection()

        if connection is None:
            return []

        cursor = None

        try:

            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT

                    ta.assignment_id,
                    ta.request_id,
                    ta.assigned_date,
                    ta.assignment_status,

                    mr.issue_type,
                    mr.priority,
                    mr.request_status,
                    mr.request_date,

                    sp.panel_name,
                    sp.location,

                    u.full_name AS customer_name

                FROM technician_assignments ta

                INNER JOIN maintenance_requests mr
                    ON ta.request_id = mr.request_id

                INNER JOIN solar_panels sp
                    ON mr.panel_id = sp.panel_id

                INNER JOIN users u
                    ON mr.user_id = u.user_id

                WHERE ta.technician_id = %s

                ORDER BY ta.assigned_date DESC
            """

            cursor.execute(
                query,
                (technician_id,)
            )

            return cursor.fetchall()

        finally:

            if cursor:
                cursor.close()

            connection.close()