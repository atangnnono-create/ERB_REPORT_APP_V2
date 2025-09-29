from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    reports = relationship("Report", back_populates="owner")
    competencies = relationship("Competency", back_populates="owner")


class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)   # optional (keeps merged version)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="reports")
    competencies = relationship("Competency", back_populates="report")


class Competency(Base):
    __tablename__ = "competencies"
    id = Column(Integer, primary_key=True, index=True)
    competency_key = Column(String, index=True)       # e.g. "A1_1"
    competency_title = Column(String, nullable=False)
    user_response = Column(Text, nullable=False)

    owner_id = Column(Integer, ForeignKey("users.id"))
    report_id = Column(Integer, ForeignKey("reports.id"))
    report = relationship("Report", back_populates="competencies")
    owner = relationship("User", back_populates="competencies")
