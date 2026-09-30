import httpx

TACHI_BASE = "https://boku.tachi.ac/api/v1"

class TachiError(Exception):
    def __init__(self, status_code: int, description: str):
        super().__init__(description)
        self.status_code = status_code

def tachi_get(path: str, api_key: str, params: dict | None = None):
    response = httpx.get(
        f"{TACHI_BASE}{path}",
        headers={"Authorization": f"Bearer {api_key}"},
        params=params,
        timeout=10
    )
    data = response.json()

    if not data.get("success"):
        raise TachiError(response.status_code, data.get("description", "Unknown error"))

    return data["body"]