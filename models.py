from sqlalchemy import Column, Integer, String, Float, ForeignKey
from database import Base

class DBUser(Base):
    __tablename__ = "users"
    
    email = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False) # admin, doctor, patient
    password_hash = Column(String, nullable=False)

class DBPatient(Base):
    __tablename__ = "patients"
    
    id = Column(String, primary_key=True, index=True)
    email = Column(String, ForeignKey("users.email"), nullable=False, unique=True)
    name = Column(String, nullable=False)
    city = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)
    height = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    disease_injury = Column(String, nullable=False)
    bmi = Column(Float, nullable=False)
    verdict = Column(String, nullable=False) 