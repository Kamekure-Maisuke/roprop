from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class Employee:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    email: str = ""
    department: str = ""


@dataclass
class PC:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    model: str = ""
    serial_number: str = ""
    assigned_to: UUID | None = None
