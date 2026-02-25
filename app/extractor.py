import re
from sqlalchemy import or_
from . import models

def extract_fields(message: str, machine_list: list, location_list: list):
    message_lower = message.lower()

    extracted = {
        "machine_name": None,
        "location": None,
        "description": message,
    }

    for machine in machine_list:
        if machine.lower() in message_lower:
            extracted["machine_name"] = machine
            break

    for location in location_list:
        if location.lower() in message_lower:
            extracted["location"] = location
            break

    return extracted


def extract_machine_db(message, db):
    words = re.findall(r'\w+', message.lower())

    conditions = [
        models.Resources.name.ilike(f"%{word}%")
        for word in words
    ]

    if not conditions:
        return []

    matched = db.query(models.Resources).filter(or_(*conditions)).all()

    return matched
