import re

from database.db import get_connection
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


class AuthService:

    # EMAIL VALIDATION
    @staticmethod
    def validate_email(email):

        email = (email or "").strip()

        if len(email) > 254:
            return False

        pattern = (
            r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
            r"@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
            r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+$"
        )

        if not re.fullmatch(pattern, email):
            return False

        local_part, domain = email.rsplit("@", 1)

        if len(local_part) > 64:
            return False

        if (
            ".." in local_part
            or local_part.startswith(".")
            or local_part.endswith(".")
            or ".." in domain
        ):
            return False

        suffix = domain.rsplit(".", 1)[-1]

        if not re.fullmatch(r"[A-Za-z]{2,63}", suffix):
            return False

        return True

    # PASSWORD VALIDATION
    @staticmethod
    def validate_password(password):

        if not password or len(password) < 8:
            return False, "Password must contain at least 8 characters."

        if len(password) > 128:
            return False, "Password cannot exceed 128 characters."

        if not re.search(r"[A-Z]", password):
            return False, "Password must contain an uppercase letter."

        if not re.search(r"[a-z]", password):
            return False, "Password must contain a lowercase letter."

        if not re.search(r"[0-9]", password):
            return False, "Password must contain a number."

        if not re.search(r"[^A-Za-z0-9]", password):
            return False, "Password must contain a special character."

        return True, ""

    # REGISTER USER
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

        for field in required_fields:
            if not data.get(field):
                return f"{field.replace('_', ' ').title()} is required."

        
        # Phone number validation
        phone = data["phone"].strip()

        if not re.fullmatch(r"[6-9][0-9]{9}", phone):
            return "Please enter a valid 10-digit Indian mobile number."


        data["email"] = data["email"].strip().lower()

        if not AuthService.validate_email(data["email"]):
            return "Please enter a valid email address, such as name@gmail.com."

        is_valid, message = AuthService.validate_password(
            data["password"]
        )

        if not is_valid:
            return message

        if data["password"] != data["confirm_password"]:
            return "Passwords do not match."

        if data["role"] not in ("User", "Technician"):
            return "Please select a valid registration role."

        connection = get_connection()

        if connection is None:
            return "Database connection failed."

        cursor = None

        try:
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                "SELECT user_id FROM users WHERE email=%s",
                (data["email"],)
            )

            if cursor.fetchone():
                return "Email already registered."

            hashed_password = generate_password_hash(
                data["password"]
            )

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
            connection.rollback()
            print("Registration Error:", e)
            return "Registration Failed."

        finally:
            if cursor:
                cursor.close()

            connection.close()

    # LOGIN USER
    @staticmethod
    def login_user(data):

        if not data.get("email") or not data.get("password"):
            return "Email and Password are required."

        email = data["email"].strip().lower()

        connection = get_connection()

        if connection is None:
            return "Database connection failed."

        cursor = None

        try:
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                "SELECT * FROM users WHERE email=%s",
                (email,)
            )

            user = cursor.fetchone()

            if not user:
                return "Invalid email or password."

            if not check_password_hash(
                user["password"],
                data["password"]
            ):
                return "Invalid email or password."

            return user

        finally:
            if cursor:
                cursor.close()

            connection.close()