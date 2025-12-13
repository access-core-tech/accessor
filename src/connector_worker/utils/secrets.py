import secrets
import string


def generate_username(prefix: str) -> str:
    suffix = ''.join(secrets.choice(string.ascii_lowercase) for _ in range(6))
    return f"{prefix}_{suffix}"


def generate_password(length: int = 16) -> str:
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    password = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*"),
    ]
    password.extend(secrets.choice(chars) for _ in range(length - 4))
    secrets.SystemRandom().shuffle(password)
    return ''.join(password).replace('.', '_')
