from database.db import get_connection
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


class AuthService:

    @staticmethod
    def register_user(data):

        required_fields = [
            "full_name",
            "email",
            "phone",
            "password",
            "confirm_password",
            "role"
        ]

        # Required field validation
        for field in required_fields:
            if not data.get(field):
                return f"{field.replace('_', ' ').title()} is required."

        # Password validation
        if data["password"] != data["confirm_password"]:
            return "Passwords do not match."

        connection = get_connection()

        if connection is None:
            return "Database connection failed."

        try:

            cursor = connection.cursor(dictionary=True)

            # Check duplicate email
            cursor.execute(
                "SELECT user_id FROM users WHERE email=%s",
                (data["email"],)
            )

            user = cursor.fetchone()

            if user:
                return "Email already registered."

            # Hash password
            hashed_password = generate_password_hash(data["password"])

            # Insert user
            cursor.execute(
                """
                INSERT INTO users
                (full_name, email, phone, password, role)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    data["full_name"],
                    data["email"],
                    data["phone"],
                    hashed_password,
                    data["role"]
                )
            )

            connection.commit()

            return "Registration Successful"

        except Exception as e:
            print(e)
            return "Registration Failed."

        finally:
            cursor.close()
            connection.close()
    
    @staticmethod
    def login_user(data):

        if not data.get("email") or not data.get("password"):
            return "Email and Password are required."

        connection = get_connection()

        if connection is None:
            return "Database connection failed."

        try:

            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                "SELECT * FROM users WHERE email=%s",
                (data["email"],)
            )

            user = cursor.fetchone()

            if not user:
                return "Invalid email or password."

            # Verify password
            if not check_password_hash(
                user["password"],
                data["password"]
            ):
                return "Invalid email or password."

            return user

        finally:
            cursor.close()
            connection.close()