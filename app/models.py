from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from .database import Base


class Complaint(Base):
    __tablename__ = "complaint"

    complaint_id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer)
    machine_id = Column(Integer, nullable=False)
    location_name = Column(String(255))
    location_id = Column(Integer)
    complaint_description = Column(Text, nullable=False)
    type = Column(Integer, nullable=False)
    status = Column(String(50), default="Open")
    time_of_complaint = Column(DateTime(timezone=True), server_default=func.now())


class ConversationState(Base):
    __tablename__ = "conversation_state"

    id = Column(Integer, primary_key=True, index=True)
    user_phone = Column(String(40), unique=True, index=True, nullable=False)
    current_step = Column(String(100), nullable=False)
    collected_data = Column(Text, nullable=False)


class Resources(Base):
    __tablename__ = "resources"

    machid = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    activation_status = Column(String(50))


class LabIncharge(Base):
    __tablename__ = "lab_incharge"

    locationid = Column(Integer, primary_key=True, index=True)
    location = Column(String(255), nullable=False)
    memberid = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False)
