from html import escape
from typing import List

from fastapi import Depends, FastAPI, Form
from fastapi.responses import Response
from sqlalchemy import String, cast, func, or_
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import SessionLocal
from app.extractor import TYPE_MAPPING, extract_machine_candidates, parse_issue_type
from app.state_manager import clear_state, get_state, parse_collected_data, upsert_state

app = FastAPI(title="Complaint Chatbot API")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _twiml_message(text: str) -> Response:
    safe_text = escape(text)
    xml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{safe_text}</Message></Response>'
    return Response(content=xml, media_type="application/xml")


def _active_resources(db: Session) -> List[models.Resources]:
    status_text = func.lower(func.trim(cast(models.Resources.activation_status, String)))
    return (
        db.query(models.Resources)
        .filter(
            (models.Resources.activation_status.is_(None))
            | (status_text.in_(["active", "1", "true", "yes"]))
        )
        .all()
    )


def _resolve_lab_location(db: Session, resource_location: str):
    value = (resource_location or "").strip()
    if not value:
        return None, None, None

    rows = (
        db.query(models.LabIncharge)
        .filter(
            or_(
                func.lower(func.trim(models.LabIncharge.location)) == value.lower(),
                cast(models.LabIncharge.locationid, String) == value,
            )
        )
        .all()
    )
    if not rows:
        return None, None, None

    active_row = next(
        (r for r in rows if (r.status or "").strip().lower() == "active"),
        None,
    )
    selected = active_row or rows[0]
    location_name = selected.location
    location_id = selected.locationid
    member_id = selected.memberid if active_row else None
    return location_name, location_id, member_id


def _pick_exact_machine_by_name(message: str, candidates: List[models.Resources]) -> List[models.Resources]:
    exact_name = message.strip().lower()
    if not exact_name:
        return []
    return [m for m in candidates if (m.name or "").strip().lower() == exact_name]


def _machine_name_options(machines: List[models.Resources]) -> str:
    names = sorted({(m.name or "").strip() for m in machines if (m.name or "").strip()})
    return "\n".join([f"- {name}" for name in names])


def _start_conversation(user_id: str, msg: str, db: Session) -> str:
    machines = _active_resources(db)
    matched = extract_machine_candidates(msg, machines)

    if not matched:
        return "I could not identify the machine. Please mention the machine name."

    if len(matched) > 1:
        options = _machine_name_options(matched)
        upsert_state(
            db,
            user_id,
            "waiting_for_exact_name",
            {
                "candidate_machine_ids": [m.machid for m in matched],
            },
        )
        return f"Multiple machines matched. Please type the exact machine name from this list:\n{options}"

    machine = matched[0]
    location_name, location_id, _ = _resolve_lab_location(db, machine.location)
    upsert_state(
        db,
        user_id,
        "waiting_for_description",
        {
            "machine_id": machine.machid,
            "machine_name": machine.name,
            "location": location_name or machine.location,
            "location_id": location_id,
        },
    )
    return (
        f"Machine {machine.name} at {machine.location} identified. "
        "Please describe the issue in one message."
    )


def _process_message(user_id: str, message: str, db: Session) -> str:
    msg = message.strip()
    if not msg:
        return "Please enter a valid message."

    state = get_state(db, user_id)

    if state is None:
        return _start_conversation(user_id, msg, db)

    data = parse_collected_data(state)

    if state.current_step == "waiting_for_exact_name":
        candidate_ids = data.get("candidate_machine_ids", [])
        if not candidate_ids:
            clear_state(db, user_id)
            return "Session expired. Please share machine name again."

        candidates = (
            db.query(models.Resources)
            .filter(models.Resources.machid.in_(candidate_ids))
            .all()
        )
        exact_matches = _pick_exact_machine_by_name(msg, candidates)
        if len(exact_matches) == 0:
            options = _machine_name_options(candidates)
            return f"Please type one exact machine name from this list:\n{options}"

        machine = sorted(exact_matches, key=lambda x: x.machid)[0]
        location_name, location_id, _ = _resolve_lab_location(db, machine.location)
        upsert_state(
            db,
            user_id,
            "waiting_for_description",
            {
                "machine_id": machine.machid,
                "machine_name": machine.name,
                "location": location_name or machine.location,
                "location_id": location_id,
            },
        )
        return (
            f"Machine {machine.name} at {machine.location} identified. "
            "Please describe the issue in one message."
        )

    if state.current_step == "waiting_for_description":
        data["description"] = msg
        upsert_state(db, user_id, "waiting_for_type", data)
        return "Please specify issue type: hardware, process, or electrical."

    if state.current_step == "waiting_for_type":
        issue_type = parse_issue_type(msg)
        if issue_type is None:
            valid = ", ".join(TYPE_MAPPING.keys())
            return f"Invalid type. Please send one of: {valid}."

        location_name, location_id, member_id = _resolve_lab_location(db, data.get("location", ""))

        complaint = models.Complaint(
            member_id=member_id,
            machine_id=data.get("machine_id"),
            location_name=location_name or data.get("location"),
            location_id=data.get("location_id") or location_id,
            complaint_description=data.get("description", ""),
            type=issue_type,
            status="Open",
        )
        db.add(complaint)
        db.commit()

        clear_state(db, user_id)

        assignee_text = (
            f" Assigned to member ID {member_id}."
            if member_id is not None
            else " No active lab incharge found for this location yet."
        )
        return f"Complaint registered successfully.{assignee_text}"

    clear_state(db, user_id)
    return "State reset due to an invalid step. Please start again with machine details."


@app.post("/chat", response_model=schemas.ChatResponse)
def chat(payload: schemas.ChatRequest, db: Session = Depends(get_db)):
    reply = _process_message(payload.user_id, payload.message, db)
    return schemas.ChatResponse(reply=reply)


@app.post("/webhook/twilio")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(...),
    db: Session = Depends(get_db),
):
    reply = _process_message(From, Body, db)
    return _twiml_message(reply)


@app.get("/test-machines", response_model=list[schemas.ResourceOut])
def test_machines(db: Session = Depends(get_db)):
    machines = _active_resources(db)
    return [
        schemas.ResourceOut(machid=m.machid, name=m.name, location=m.location)
        for m in machines
    ]


@app.get("/health")
def health_check():
    return {"status": "ok"}
