from .common import BaseModel, constr, Optional


class DepartmentSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class DepartmentCreateSchema(BaseModel):
    name: constr(min_length=1, max_length=100)


class DepartmentUpdateSchema(BaseModel):
    name: Optional[constr(min_length=1, max_length=100)] = None
