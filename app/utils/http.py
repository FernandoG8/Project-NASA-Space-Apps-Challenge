from __future__ import annotations
import time
from typing import Any, Dict, Optional
import requests

class HttpError(Exception):
    pass

def get_json(
    url: str,
    timeout: int = 30,
    retries: int = 3,
    backoff: float = 1.6,
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    GET JSON con reintentos y backoff exponencial.
    Lanza HttpError si la solicitud falla.
    """
    last_exc: Optional[Exception] = None
    for i in range(retries):
        try:
            r = requests.get(url, timeout=timeout, headers=headers)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_exc = e
            if i < retries - 1:
                time.sleep(backoff ** (i + 1))
    raise HttpError(f"GET failed after {retries} attempts for URL: {url} :: {last_exc}")
