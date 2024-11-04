import requests

from config.settings.base import env


def validate_recaptcha(token: str) -> bool:
    """Validate the recaptcha token"""
    secret_key = env("RECAPTCHA_SECRET_KEY")
    payload = {"secret": secret_key, "response": token}
    response = requests.post("https://www.google.com/recaptcha/api/siteverify", data=payload)
    result = response.json()
    return result.get("success", False)
