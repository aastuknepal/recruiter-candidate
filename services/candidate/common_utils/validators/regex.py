from django.core.validators import RegexValidator

# Name: only alphabets
name_validator = RegexValidator(
    regex=r"^[A-Za-z]+$",
    message="Only alphabets are allowed."
)

# Phone: exactly 10 digits
phone_validator = RegexValidator(
    regex=r"^\d{10}$",
    message="Phone number must be 10 digits"
)

# Username: letters, numbers, underscore, 4-20 chars
username_validator = RegexValidator(
    regex=r"^[a-zA-Z0-9_]{4,20}$",
    message="Username must be 4-20 characters and can contain letters, numbers, and underscores only."
)

# Password: minimum 8 chars, at least 1 uppercase, 1 lowercase, 1 digit, 1 special char
password_validator = RegexValidator(
    regex=r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$",
    message=(
        "Password must be at least 8 characters long and contain "
        "an uppercase letter, a lowercase letter, a number, and a special character."
    )
)

# Optional: Nepal citizenship number (basic numeric check)
citizenship_validator = RegexValidator(
    regex=r"^\d{6,12}$",
    message="Citizenship number must contain 6–12 digits."
)