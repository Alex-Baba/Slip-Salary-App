"""Compatibility shim - re-export schemas from the package submodules.

Existing imports like `from app.api import schemas` or
`from app.api.schemas import EmployeeSchema` will keep working.
"""

from .schemas import *  # re-export everything from the package

__all__ = getattr(__import__('app.api.schemas', fromlist=['__all__']), '__all__')


