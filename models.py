from dataclasses import dataclass, field
from datetime import datetime
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


@dataclass
class PCAssignmentHistory:
    id: UUID = field(default_factory=uuid4)
    pc_id: UUID = field(default_factory=uuid4)
    employee_id: UUID | None = None
    assigned_at: datetime = field(default_factory=datetime.now)
    notes: str = ""
