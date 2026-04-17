"""Local JSON store for scheduling demo: food postings + driver/rider offers."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA_PATH = BASE / "data"
STORE_FILE = DATA_PATH / "marketplace.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ensure_data_dir() -> None:
    DATA_PATH.mkdir(parents=True, exist_ok=True)


def save_state(state: dict) -> None:
    """Write JSON store (does not call load_state — avoids recursion)."""
    _ensure_data_dir()
    STORE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def load_state() -> dict:
    _ensure_data_dir()
    if not STORE_FILE.is_file():
        save_state({"pickups": [], "offers": []})
        return {"pickups": [], "offers": []}
    try:
        return json.loads(STORE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"pickups": [], "offers": []}


def add_pickup(
    *,
    business: str,
    city: str,
    zip_code: str,
    pounds: float,
    window: str,
    contact: str,
    disposal_per_lb: float,
    trip_cost_estimate: float,
) -> dict:
    state = load_state()
    oid = str(uuid.uuid4())[:8]
    waste_proxy = round(pounds * disposal_per_lb, 2)
    net_vs_waste = round(waste_proxy - trip_cost_estimate, 2)
    row = {
        "id": oid,
        "type": "pickup",
        "business": business.strip() or "Anonymous donor",
        "city": city,
        "zip": zip_code.strip(),
        "pounds": float(pounds),
        "window": window.strip(),
        "contact": contact.strip(),
        "created": _now_iso(),
        "waste_cost_proxy_usd": waste_proxy,
        "trip_cost_estimate_usd": round(float(trip_cost_estimate), 2),
        "net_vs_landfill_proxy_usd": net_vs_waste,
        "status": "open",
    }
    state.setdefault("pickups", []).insert(0, row)
    save_state(state)
    return row


def add_offer(
    *,
    name: str,
    city: str,
    capacity_lbs: float,
    window: str,
    contact: str,
    notes: str,
) -> dict:
    state = load_state()
    oid = str(uuid.uuid4())[:8]
    row = {
        "id": oid,
        "type": "driver",
        "name": name.strip() or "Volunteer",
        "city": city,
        "capacity_lbs": float(capacity_lbs),
        "window": window.strip(),
        "contact": contact.strip(),
        "notes": notes.strip(),
        "created": _now_iso(),
        "status": "available",
    }
    state.setdefault("offers", []).insert(0, row)
    save_state(state)
    return row


def mask_contact(s: str, visible: int = 3) -> str:
    s = (s or "").strip()
    if len(s) <= visible:
        return "—" if not s else s
    return s[:visible] + "…"


def clear_all_demo() -> None:
    save_state({"pickups": [], "offers": []})
