from fastapi import FastAPI, APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, computed_field
from typing import Annotated, Literal, Optional
from sqlalchemy.orm import Session

import database
import models
from database import get_db
from auth_routes import router as auth_router
from admin_func import router as admin_router  
from doctor_func import router as doctor_router
from patient_func import router as patient_router
from security import RoleChecker
from schemas import Patient, PatientUpdate

# Initialize SQLite tables automatically on start
database.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# Router Registrations
app.include_router(auth_router)
app.include_router(admin_router) 
app.include_router(doctor_router)
app.include_router(patient_router)

require_any_user = Depends(RoleChecker(allowed_roles=["admin", "doctor", "patient"]))

# Global Routes
@app.get('/view')
def view(db: Session = Depends(get_db), current_user: dict = require_any_user):
    return db.query(models.DBPatient).all()

if __name__ == "__main__":
    import uvicorn
    # Make sure to launch via "python main.py" or use the target port parameters manually
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)