from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
import models
from security import RoleChecker

router = APIRouter(prefix="/patient", tags=["Patient Operations"])

require_patient = Depends(RoleChecker(allowed_roles=["master_admin", "admin", "doctor", "patient"]))

@router.get('/view/me')
def view_patient(db: Session = Depends(get_db), current_user: dict = require_patient):
    """
    Allows a patient to view their own details.
    """
    user_email = current_user.get("sub")
    db_patient = db.query(models.DBPatient).filter(models.DBPatient.email == user_email).first()
    if not db_patient:
        raise HTTPException(status_code=404, detail='Patient profile not found. Please contact administration.')
        
    return db_patient
