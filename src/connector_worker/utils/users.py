def get_user_login_from_email(user_email: str) -> str:
    if '@' in user_email:
        return user_email.split('@')[0]
    return user_email
