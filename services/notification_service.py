from database.db import get_connection


class NotificationService:

    @staticmethod
    def get_user_notifications(user_id):

        connection = get_connection()

        if connection is None:
            return []

        cursor = None

        try:

            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT
                    notification_id,
                    title,
                    message,
                    notification_type,
                    is_read,
                    created_at

                FROM notifications

                WHERE user_id = %s

                ORDER BY created_at DESC
                """,
                (user_id,)
            )

            return cursor.fetchall()

        finally:

            if cursor:
                cursor.close()

            connection.close()

    @staticmethod
    def get_unread_count(user_id):

        connection = get_connection()

        if connection is None:
            return 0

        cursor = None

        try:

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM notifications

                WHERE user_id = %s
                AND is_read = 0
                """,
                (user_id,)
            )

            result = cursor.fetchone()

            return result[0] if result else 0

        finally:

            if cursor:
                cursor.close()

            connection.close()

    @staticmethod
    def mark_as_read(notification_id, user_id):

        connection = get_connection()

        if connection is None:
            return False

        cursor = None

        try:

            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE notifications

                SET is_read = 1

                WHERE notification_id = %s
                AND user_id = %s
                """,
                (
                    notification_id,
                    user_id
                )
            )

            connection.commit()

            return cursor.rowcount > 0

        finally:

            if cursor:
                cursor.close()

            connection.close()

    @staticmethod
    def mark_all_as_read(user_id):

        connection = get_connection()

        if connection is None:
            return False

        cursor = None

        try:

            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE notifications

                SET is_read = 1

                WHERE user_id = %s
                AND is_read = 0
                """,
                (user_id,)
            )

            connection.commit()

            return True

        finally:

            if cursor:
                cursor.close()

            connection.close()