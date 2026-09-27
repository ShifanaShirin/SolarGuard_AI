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