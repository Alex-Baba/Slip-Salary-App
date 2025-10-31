from .common import BaseModel, Optional


class AttendanceSchema(BaseModel):
    id: int
    employee_id: int
    working_days: int
    leave_days: int
    year: int
    month: int

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
