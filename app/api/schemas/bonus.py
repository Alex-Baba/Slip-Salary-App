from .common import BaseModel, Optional, constr


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


class BonusUpdateSchema(BaseModel):
    amount: Optional[float] = None
    description: Optional[constr(min_length=1, max_length=255)] = None
    date: Optional[str] = None

    def to_date(self):
        from datetime import date as _date
        if not self.date:
            return None
        try:
            parts = [int(p) for p in self.date.split('-')]
            if len(parts) != 3:
                raise ValueError
            return _date(parts[0], parts[1], parts[2])
        except Exception:
            raise ValueError("Invalid date format, expected YYYY-MM-DD")
