import re
from typing import Iterable, List, Optional

from . import models


TYPE_MAPPING = {
    "hardware": 1,
    "process": 2,
    "electrical": 3,
}

TYPE_SYNONYMS = {
    "hardware": {"hardware", "mechanical", "machine", "part"},
    "process": {"process", "workflow", "procedure", "operation"},
    "electrical": {"electrical", "electric", "power", "wiring"},
}


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _tokenize(value: str) -> set:
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def extract_machine_candidates(message: str, machines: Iterable[models.Resources]) -> List[models.Resources]:
    """Return unique machine matches using exact-name and token-overlap heuristics."""
    msg_norm = _normalize_text(message)
    msg_tokens = _tokenize(message)

    exact_matches: List[models.Resources] = []
    partial_matches: List[models.Resources] = []

    for machine in machines:
        name_norm = _normalize_text(machine.name or "")
        if not name_norm:
            continue

        exact_pattern = rf"\b{re.escape(name_norm)}\b"
        if re.search(exact_pattern, msg_norm):
            exact_matches.append(machine)
            continue

        name_tokens = _tokenize(name_norm)
        if name_tokens and len(name_tokens.intersection(msg_tokens)) >= 1:
            partial_matches.append(machine)

    if exact_matches:
        return exact_matches

    unique = []
    seen = set()
    for machine in partial_matches:
        if machine.machid not in seen:
            seen.add(machine.machid)
            unique.append(machine)
    return unique


def narrow_by_location(message: str, machines: Iterable[models.Resources]) -> List[models.Resources]:
    msg_norm = _normalize_text(message)
    narrowed = []

    for machine in machines:
        location_norm = _normalize_text(machine.location or "")
        if location_norm and location_norm in msg_norm:
            narrowed.append(machine)

    return narrowed


def parse_issue_type(message: str) -> Optional[int]:
    msg_tokens = _tokenize(message)
    if not msg_tokens:
        return None

    for canonical, aliases in TYPE_SYNONYMS.items():
        if msg_tokens.intersection(aliases):
            return TYPE_MAPPING[canonical]

    return None
