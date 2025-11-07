from .common import BaseModel, EmailStr, constr, Optional


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
    # Inline manager summary for UI convenience
    manager: Optional[ManagerListSchema] = None
    department_id: Optional[int] = None
    base_salary: float
    expected_working_days: Optional[int] = None

    class Config:
        from_attributes = True


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
    # Optional initial attendance values; if omitted the service will
    # populate sensible defaults (working_days -> expected_working_days, leave_days -> 0)
    working_days: Optional[int] = None
    leave_days: Optional[int] = None


class EmployeeListSchema(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    role: EmployeeRoleSchema
    manager_id: Optional[int] = None
    # Include lightweight manager summary in listings
    manager: Optional[ManagerListSchema] = None
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


class EmployeeUpdateSchema(BaseModel):
    first_name: Optional[constr(min_length=1, max_length=30)] = None
    last_name: Optional[constr(min_length=1, max_length=30)] = None
    role_id: Optional[int] = None
    manager_id: Optional[int] = None
    department_id: Optional[int] = None
    base_salary: Optional[float] = None
    expected_working_days: Optional[int] = None
    password: Optional[constr(min_length=8)] = None
