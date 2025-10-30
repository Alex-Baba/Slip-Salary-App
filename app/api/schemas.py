from pydantic import BaseModel, EmailStr, constr
from typing import Optional

class EmployeeRoleSchema(BaseModel):
    id: int
    role: str

    class Config:
        from_attributes = True

class ManagerListSchema(BaseModel):
    id: int
    first_name: str
    last_name: str
    department_name: Optional[str] = None

    class Config:
        from_attributes = True

class EmployeeSchema(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    cnp: str
    role: EmployeeRoleSchema
    manager_id: Optional[int] = None
    department_id: Optional[int] = None
    base_salary: float
    expected_working_days: Optional[int] = None

    class Config:
        from_attributes = True

class SalarySchema(BaseModel):
    id: int
    employee_id: int
    amount: float
    date: str  

    class Config:
        from_attributes = True

class AttendanceSchema(BaseModel):
    id: int
    employee_id: int
    working_days: int
    leave_days: int
    year: int
    month: int

    class Config:
        from_attributes = True

class BonusSchema(BaseModel):
    id: int
    employee_id: int
    amount: float
    description: str
    date: str  

    class Config:
        from_attributes = True

class AttendanceCreateSchema(BaseModel):
    employee_id: int
    working_days: int
    leave_days: int
    year: int
    month: int

class AttendanceUpdateSchema(BaseModel):
    working_days: Optional[int] = None
    leave_days: Optional[int] = None

class EmployeeCreateSchema(BaseModel):
    email: EmailStr
    password: constr(min_length=8)
    first_name: constr(min_length=1, max_length=30)
    last_name: constr(min_length=1, max_length=30)
    cnp: constr(min_length=13, max_length=13)
    role_id: int
    manager_id: Optional[int] = None
    department_id: Optional[int] = None
    base_salary: Optional[float] = None
    expected_working_days: Optional[int] = None

class EmployeeDeleteSchema(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    cnp: str

    class Config:
        from_attributes = True

class DepartmentSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class DepartmentCreateSchema(BaseModel):
    name: constr(min_length=1, max_length=100)


