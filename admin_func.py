from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Literal, Optional

from database import get_db
import models
from security import RoleChecker
from schemas import Patient, PatientUpdate  # Shared Pydantic schemas

# Initialize the router with a prefix and documentation tags
router = APIRouter(prefix="/admin", tags=["Admin Operations"])

# Define Role Guards specific to these administrative actions
require_medical_staff = Depends(RoleChecker(allowed_roles=["admin", "master_admin", "doctor"]))
require_admin_only = Depends(RoleChecker(allowed_roles=["admin", "master_admin"]))
require_master_admin = Depends(RoleChecker(allowed_roles=["master_admin"]))

# 1. CREATE NEW PATIENT (Allowed: admin, doctor)
@router.post('/create', status_code=status.HTTP_201_CREATED)
def create_patient(patient: Patient, db: Session = Depends(get_db), current_user: dict = require_admin_only):
    # Ensure patient record doesn't already exist with this ID
    db_patient = db.query(models.DBPatient).filter(models.DBPatient.id == patient.id).first()
    if db_patient:
        raise HTTPException(status_code=400, detail='Patient record already exists')
        
    # Ensure the user has signed up for an account
    patient_email = str(patient.email).lower()
    db_user = db.query(models.DBUser).filter(models.DBUser.email == patient_email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail='User must sign up for an account first')
    if db_user.role != 'patient':
        raise HTTPException(status_code=400, detail='User role must be patient')
        
    # Ensure no existing patient record is attached to this email
    existing_patient_by_email = db.query(models.DBPatient).filter(models.DBPatient.email == patient_email).first()
    if existing_patient_by_email:
        raise HTTPException(status_code=400, detail='A patient profile is already linked to this email')
    
    new_patient = models.DBPatient(
        id=patient.id, email=patient_email, name=patient.name, city=patient.city, age=patient.age,
        gender=patient.gender, height=patient.height, weight=patient.weight,
        disease_injury=patient.disease_injury
    )
    # Ensure computed fields are stored in the DB (DB has NOT NULL constraints)
    new_patient.bmi = patient.bmi
    new_patient.verdict = patient.verdict
    db.add(new_patient)
    db.commit()
    return {"message": "Patient created successfully"}

# 2. EDIT PATIENT DETAILS (Allowed: admin, doctor)
@router.put('/edit/{patient_id}')
def update_patient(patient_id: str, patient_update: PatientUpdate, db: Session = Depends(get_db), current_user: dict = require_admin_only):
    db_patient = db.query(models.DBPatient).filter(models.DBPatient.id == patient_id).first()
    if not db_patient:
        raise HTTPException(status_code=404, detail='Patient not found')
        
    update_data = patient_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_patient, key, value)
        
    # Recompute derived fields after applying updates
    re_validated = Patient(
        id=db_patient.id, email=db_patient.email, name=db_patient.name, city=db_patient.city, age=db_patient.age,
        gender=db_patient.gender, height=db_patient.height, weight=db_patient.weight,
        disease_injury=db_patient.disease_injury
    )
    db_patient.bmi = re_validated.bmi
    db_patient.verdict = re_validated.verdict

    db.commit()
    return {"message": "Patient record updated"}

# 3. DELETE PATIENT (Allowed: admin only)
@router.delete('/delete/{patient_id}')
def delete_patient(patient_id: str, db: Session = Depends(get_db), current_user: dict = require_admin_only):
    db_patient = db.query(models.DBPatient).filter(models.DBPatient.id == patient_id).first()
    if not db_patient:
        raise HTTPException(status_code=404, detail='Patient not found')
        
    db.delete(db_patient)
    db.commit()
    return {"message": "Patient records purged"}

# 4. VIEW SINGLE PATIENT (Allowed: admin, doctor)
@router.get('/patient/{patient_id}')
def view_patient(patient_id: str, db: Session = Depends(get_db), current_user: dict = require_admin_only):
    db_patient = db.query(models.DBPatient).filter(models.DBPatient.id == patient_id).first()
    if not db_patient:
        raise HTTPException(status_code=404, detail='Patient not found')
    return db_patient

# 5. SORT PATIENTS (Allowed: admin, doctor)
@router.get('/sort')
def sort_patients(
    sort_by: str = Query(..., description='Sort on the basis of height, weight or bmi'), 
    order: str = Query('asc', description='sort in asc or desc order'), 
    db: Session = Depends(get_db),
    current_user: dict = require_admin_only
):
    if sort_by not in ['height', 'weight', 'bmi']:
        raise HTTPException(status_code=400, detail='Invalid sort target')
        
    query = db.query(models.DBPatient)
    column_attr = getattr(models.DBPatient, sort_by)
    
    if order == 'desc':
        query = query.order_by(column_attr.desc())
    else:
        query = query.order_by(column_attr.asc())
        
    return query.all()

# 6. DELETE USER (Allowed: master_admin only)
@router.delete('/delete_user/{email}')
def delete_user(email: str, db: Session = Depends(get_db), current_user: dict = require_master_admin):
    email = email.lower()
    
    db_user = db.query(models.DBUser).filter(models.DBUser.email == email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail='User not found')
        
    # 1. Delete associated medical record first to satisfy Foreign Key constraints
    db_patient = db.query(models.DBPatient).filter(models.DBPatient.email == email).first()
    if db_patient:
        db.delete(db_patient)
        
    # 2. Delete the user
    db.delete(db_user)
    db.commit()
    
    return {"message": f"User {email} and all associated records have been purged"}