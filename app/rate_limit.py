# app/rate_limit.py
from time import time
from collections import defaultdict
from typing import Tuple

# Ventana deslizante simple en memoria (por proceso)
# En producción usa Redis (slowapi/limits) para multi-worker.
WINDOW_SEC = 60
MAX_ATTEMPTS = 10  # p. ej., 10 intentos/min por IP

_attempts: dict[str, list[float]] = defaultdict(list)

def check_and_count(ip: str) -> Tuple[bool, int]:
    now = time()
    bucket = _attempts[ip]
    # limpia intentos viejos
    i = 0
    while i < len(bucket) and now - bucket[i] > WINDOW_SEC:
        i += 1
    if i:
        del bucket[:i]
    # verifica límite
    if len(bucket) >= MAX_ATTEMPTS:
        # retorna False y segundos restantes (aprox)
        ttl = WINDOW_SEC - int(now - bucket[0])
        return False, max(ttl, 1)
    bucket.append(now)
    return True, 0
