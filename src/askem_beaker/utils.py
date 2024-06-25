import os
from base64 import b64encode
from typing import TYPE_CHECKING, Any, Dict
from requests.auth import HTTPBasicAuth

class TerariumAuth:
    username: str
    password: str

    def __init__(self) -> None:
        self.username = os.environ.get("AUTH_USERNAME", None)
        self.password = os.environ.get("AUTH_PASSWORD", None)

    def auth_header(self) -> dict[str, str]:
        if self.username and self.password:
            token = b64encode(f"{self.username}:{self.password}".encode('utf-8')).decode("ascii")
            return {"Authorization": f"Basic {token}"}
        else:
            return None

    def requests_auth(self) -> HTTPBasicAuth:
        if self.username and self.password:
            return HTTPBasicAuth(self.username, self.password)
        else:
            return None


def get_auth() -> TerariumAuth|None:
    try:
        return TerariumAuth()
    except ValueError:
        return None
