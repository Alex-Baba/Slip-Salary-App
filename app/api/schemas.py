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
    date: str  # Always output ISO string

    class Config:
        from_attributes = True

    @classmethod
    def from_model(cls, bonus):
        return cls(
            id=bonus.id,
            employee_id=bonus.employee_id,
            amount=float(bonus.amount),
            description=bonus.description,
            date=bonus.date.isoformat() if bonus.date else None
        )

class BonusCreateSchema(BaseModel):
    employee_id: int
    amount: float
    description: constr(min_length=1, max_length=255)
    date: Optional[str] = None  # ISO format date string optional
    class Config:
        from_attributes = True

    def to_date(self):
        from datetime import date as _date
        if not self.date:
            return _date.today()
        try:
            parts = [int(p) for p in self.date.split('-')]
            if len(parts) != 3:
                raise ValueError
            return _date(parts[0], parts[1], parts[2])
        except Exception:
            raise ValueError("Invalid date format, expected YYYY-MM-DD")

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

class EmployeeListSchema(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    role: EmployeeRoleSchema
    manager_id: Optional[int] = None
    department_id: Optional[int] = None

    class Config:
        from_attributes = True

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


