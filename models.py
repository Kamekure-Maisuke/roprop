from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class Employee:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    email: str = ""
    department_id: UUID | None = None


@dataclass
class PC:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    model: str = ""
    serial_number: str = ""
    assigned_to: UUID | None = None


@dataclass
class Department:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
