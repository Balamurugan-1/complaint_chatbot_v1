from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from .database import Base

class Complaint(Base):
    __tablename__ = "complaint"

    complaint_id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer)
    machine_id = Column(Integer)
    complaint_description = Column(Text)
    type = Column(Integer)
    status = Column(String(50), default="Open")
    time_of_complaint = Column(DateTime(timezone=True), server_default=func.now())


class ConversationState(Base):
    __tablename__ = "conversation_state"

    id = Column(Integer, primary_key=True, index=True)
    user_phone = Column(String(20), unique=True)
    current_step = Column(String(100))
    collected_data = Column(Text)  # store JSON string

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from .database import Base


class Resources(Base):
    __tablename__ = "resources"

    machid = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    location = Column(Integer)
    activation_status = Column(String(50))


class LabIncharge(Base):
    __tablename__ = "lab_incharge"

    id = Column(Integer, primary_key=True, index=True)
    location = Column(String(255))
    memberid = Column(Integer)
    faculty_incharge = Column(String(255))
    locationid = Column(Integer)
