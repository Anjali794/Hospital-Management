from pydantic import BaseModel, Field, computed_field, EmailStr, ConfigDict
from typing import Annotated, Literal, Optional

class Patient(BaseModel):
    model_config = {"populate_by_name": True}
    id: Annotated[str, Field(..., description='ID of the patient', examples=['P-001'])]
    email: EmailStr

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "john.doe@gmail.com"
            }
        }
    )
    name: Annotated[str, Field(..., description='Name of the patient')]
    city: Annotated[str, Field(..., description='City where the patient is living')]
    age: Annotated[int, Field(..., gt=0, lt=120, description='Age of the patient')]
    gender: Annotated[Literal['male', 'female', 'others'], Field(..., description='Gender of the patient')]
    height: Annotated[float, Field(..., gt=0, description='Height of the patient in mtrs')]
    weight: Annotated[float, Field(..., gt=0, description='Weight of the patient in kgs')]
    disease_injury: Annotated[str, Field(..., description='disease/injury', alias='disease/injury')]

    @computed_field
    def bmi(self) -> float:
        return round(self.weight / (self.height ** 2), 2)

    @computed_field
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return 'Underweight'
        elif self.bmi < 25:
            return 'Normal'
        elif self.bmi < 30:
            return 'Overweight'
        return 'Obese'
        
class PatientUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    age: Optional[int] = Field(default=None, gt=0)
    gender: Optional[Literal['male', 'female', 'others']] = None
    height: Optional[float] = Field(default=None, gt=0)
    weight: Optional[float] = Field(default=None, gt=0)
    disease_injury: Optional[str] = None

