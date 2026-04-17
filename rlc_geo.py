"""ZIP → lat/lon using offline US postal database (pgeocode)."""

from __future__ import annotations

import pandas as pd
import pgeocode

_nomi: pgeocode.Nominatim | None = None


def _nominatim() -> pgeocode.Nominatim:
    global _nomi
    if _nomi is None:
        _nomi = pgeocode.Nominatim("us")
    return _nomi


def lookup_zips(zipcodes: list[str]) -> pd.DataFrame:
    """Return columns: zip, latitude, longitude, place_name, state_code."""
    nomi = _nominatim()
    rows = []
    seen = set()
    for z in zipcodes:
        if not z or z in seen:
            continue
        seen.add(z)
        r = nomi.query_postal_code(z)
        if pd.isna(r.latitude) or pd.isna(r.longitude):
            continue
        rows.append(
            {
                "zip": z,
                "latitude": float(r.latitude),
                "longitude": float(r.longitude),
                "place_name": r.place_name,
                "state_code": r.state_code,
            }
        )
    return pd.DataFrame(rows)
