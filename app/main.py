from fastapi import FastAPI, Form
from app.database import SessionLocal
from app import models
import json

from app.extractor import extract_machine_db

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


import json
from fastapi import Form
from app.database import SessionLocal
from app import models
from app.extractor import extract_machine_db


@app.post("/webhook/twilio")
async def whatsapp_webhook(From: str = Form(...), Body: str = Form(...)):
    db = SessionLocal()

    # Check if conversation exists
    state = db.query(models.ConversationState).filter(
        models.ConversationState.user_phone == From
    ).first()

    # -------------------------------
    # START NEW CONVERSATION
    # -------------------------------
    if not state:

        matched = extract_machine_db(Body, db)

        if not matched:
            return {"reply": "Please provide the correct machine name."}

        if len(matched) > 1:
            machine_list = ", ".join(
                [f"{m.name} ({m.location})" for m in matched]
            )
            return {"reply": f"I found multiple machines: {machine_list}. Please specify."}

        machine = matched[0]

        # Create conversation state
        collected_data = {
            "machine_id": machine.machid,
            "description": Body
        }

        new_state = models.ConversationState(
            user_phone=From,
            current_step="waiting_for_type",
            collected_data=json.dumps(collected_data)
        )

        db.add(new_state)
        db.commit()

        return {"reply": f"Machine {machine.name} detected in {machine.location}. Please specify issue type (hardware/process)."}

    # -------------------------------
    # CONTINUE CONVERSATION
    # -------------------------------
    else:
        data = json.loads(state.collected_data)

        if state.current_step == "waiting_for_type":
            TYPE_MAPPING = {
                        "hardware": 1,
                        "process": 2,
                        "electrical": 3
                    }
            data["type"] = Body.strip().lower()
            if data["type"] not in TYPE_MAPPING:
                return {"reply": "Invalid type. Please specify 'hardware', 'process', or 'electrical'."}
            data["type"] = TYPE_MAPPING[data["type"]]

            # Insert complaint
            new_complaint = models.Complaint(
                member_id=1,  # temporary
                machine_id=data["machine_id"],
                complaint_description=data["description"],
                type=data["type"],
                status="Open"
            )

            db.add(new_complaint)
            db.commit()

            # Delete conversation state
            db.delete(state)
            db.commit()

            return {"reply": "Complaint registered successfully."}

    return {"reply": "Something went wrong."}

@app.get("/test-machines")
def test_machines():
    db = SessionLocal()
    machines = db.query(models.Resources).all()

    return [
        {"id": m.machid, "name": m.name, "location": m.location}
        for m in machines ]