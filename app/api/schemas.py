from pydantic import BaseModel, EmailStr
from typing import Optional

class EmployeeRoleSchema(BaseModel):
    id: int
    role: str

    class Config:
        orm_mode = True

class EmployeeSchema(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    cnp: str
    role: EmployeeRoleSchema
    manager_id: Optional[int] = None

    class Config:
        orm_mode = True

class SalarySchema(BaseModel):
    id: int
    employee_id: int
    amount: float
    date: str  

    class Config:
        orm_mode = True

class AttendanceSchema(BaseModel):
    id: int
    employee_id: int
    working_days: int
    leave_days: int

    class Config:
        orm_mode = True

class BonusSchema(BaseModel):
    id: int
    employee_id: int
    amount: float
    description: str
    date: str  

    class Config:
        orm_mode = True

class EmployeeCreateSchema(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    cnp: str
    role_id: int
    manager_id: Optional[int] = None