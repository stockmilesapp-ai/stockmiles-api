from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.core.settings import settings


def verify_google_token(token: str) -> dict:
    """Return the token's claims, or raise ValueError if it is not valid."""
    return id_token.verify_oauth2_token(
        token, google_requests.Request(), settings.google_client_id
    )
