from __future__ import annotations
from datetime import date

def to_yyyymmdd(d: date) -> str:
    return d.strftime("%Y%m%d")
