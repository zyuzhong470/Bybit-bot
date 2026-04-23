from enum import Enum
from state import atomic_update, load_state

class TradeState(Enum):
    IDLE = "IDLE"
    WAIT_ENTRY = "WAIT_ENTRY"
    IN_POSITION = "IN_POSITION"
    WAIT_EXIT = "WAIT_EXIT"
    COOLDOWN = "COOLDOWN"

def get_state():
    s = load_state()
    return s.get("state", "IDLE")

def set_state(new_state):
    def _set(s):
        s["state"] = new_state
        return s
    atomic_update(_set)

def can_transition(from_state, to_state):
    allowed = {
        "IDLE": ["WAIT_ENTRY", "COOLDOWN"],
        "WAIT_ENTRY": ["IN_POSITION", "IDLE", "COOLDOWN"],
        "IN_POSITION": ["WAIT_EXIT", "COOLDOWN"],
        "WAIT_EXIT": ["IDLE", "COOLDOWN"],
        "COOLDOWN": ["IDLE"],
    }
    return to_state in allowed.get(from_state, [])

def transition(to_state):
    current = get_state()
    if can_transition(current, to_state):
        set_state(to_state)
        return True
    return False
