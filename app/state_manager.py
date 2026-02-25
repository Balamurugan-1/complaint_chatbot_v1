import json
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from . import models


def get_state(db: Session, user_id: str) -> Optional[models.ConversationState]:
    return (
        db.query(models.ConversationState)
        .filter(models.ConversationState.user_phone == user_id)
        .first()
    )


def parse_collected_data(state: models.ConversationState) -> Dict[str, Any]:
    try:
        return json.loads(state.collected_data or "{}")
    except json.JSONDecodeError:
        return {}


def upsert_state(db: Session, user_id: str, step: str, data: Dict[str, Any]) -> models.ConversationState:
    state = get_state(db, user_id)

    if state is None:
        state = models.ConversationState(
            user_phone=user_id,
            current_step=step,
            collected_data=json.dumps(data),
        )
        db.add(state)
    else:
        state.current_step = step
        state.collected_data = json.dumps(data)

    db.commit()
    db.refresh(state)
    return state


def clear_state(db: Session, user_id: str) -> None:
    state = get_state(db, user_id)
    if state is None:
        return

    db.delete(state)
    db.commit()
