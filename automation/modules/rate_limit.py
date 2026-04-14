"""Per-IP daily rate limit (file-based)."""
import json
from datetime import date
from pathlib import Path
from threading import Lock

_LOCK = Lock()
DEFAULT_LIMIT = 3


def _state_file() -> Path:
    p = Path(__file__).parent.parent / "logs" / "rate_limit.json"
    p.parent.mkdir(exist_ok=True)
    return p


def _load() -> dict:
    f = _state_file()
    if not f.exists():
        return {"date": "", "ips": {}}
    try:
        s = json.loads(f.read_text(encoding="utf-8"))
        if "ips" not in s:
            s = {"date": "", "ips": {}}
        return s
    except Exception:
        return {"date": "", "ips": {}}


def _save(state: dict) -> None:
    _state_file().write_text(json.dumps(state), encoding="utf-8")


def _rollover(state: dict) -> dict:
    today = date.today().isoformat()
    if state.get("date") != today:
        return {"date": today, "ips": {}}
    return state


def check_and_increment(ip: str, limit: int = DEFAULT_LIMIT) -> tuple[bool, int, int]:
    """Returns (allowed, used_by_ip_today, limit). Increments on success."""
    with _LOCK:
        state = _rollover(_load())
        used = state["ips"].get(ip, 0)
        if used >= limit:
            _save(state)
            return False, used, limit
        state["ips"][ip] = used + 1
        _save(state)
        return True, used + 1, limit


def peek(ip: str, limit: int = DEFAULT_LIMIT) -> tuple[int, int]:
    state = _rollover(_load())
    return state["ips"].get(ip, 0), limit
