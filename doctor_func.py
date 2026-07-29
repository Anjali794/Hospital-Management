from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
import models
from security import RoleChecker
from schemas import Patient, PatientUpdate

router = APIRouter(prefix="/doctor", tags=["Doctor Operations"])

require_doctor = Depends(RoleChecker(allowed_roles=["doctor"]))

@router.put('/edit/{patient_id}')
def update_patient(patient_id: str, patient_update: PatientUpdate, db: Session = Depends(get_db), current_user: dict = require_doctor):
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

@router.get('/patient/{patient_id}')
def view_patient(patient_id: str, db: Session = Depends(get_db), current_user: dict = require_doctor):
    db_patient = db.query(models.DBPatient).filter(models.DBPatient.id == patient_id).first()
    if not db_patient:
        raise HTTPException(status_code=404, detail='Patient not found')
    return db_patient

@router.get('/sort')
def sort_patients(
    sort_by: str = Query(..., description='Sort on the basis of height, weight or bmi'), 
    order: str = Query('asc', description='sort in asc or desc order'), 
    db: Session = Depends(get_db),
    current_user: dict = require_doctor
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
