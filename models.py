from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class DepartmentModel(Base):
    __tablename__: str = "departments"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)


class EmployeeModel(Base):
    __tablename__: str = "employees"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    department_id: Mapped[UUID | None] = mapped_column(ForeignKey("departments.id", ondelete="SET NULL"))


class PCModel(Base):
    __tablename__: str = "pcs"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
    serial_number: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    assigned_to: Mapped[UUID | None] = mapped_column(ForeignKey("employees.id", ondelete="SET NULL"))


class PCAssignmentHistoryModel(Base):
    __tablename__: str = "pc_assignment_histories"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    pc_id: Mapped[UUID] = mapped_column(ForeignKey("pcs.id", ondelete="CASCADE"), nullable=False)
    employee_id: Mapped[UUID | None] = mapped_column(ForeignKey("employees.id", ondelete="SET NULL"))
    assigned_at: Mapped[datetime] = mapped_column(server_default=func.current_timestamp(), nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="")


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
