from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from piccolo.columns import Bytea, Text, Timestamp, UUID as PiccoloUUID, Varchar
from piccolo.table import Table

from app.database import DB


# Dataclassモデル (API入出力用)
@dataclass
class Department:
    id: UUID = field(default_factory=uuid4)
    name: str = ""


@dataclass
class Employee:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    email: str = ""
    department_id: UUID | None = None
    profile_image: bytes | None = None


@dataclass
class PC:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    model: str = ""
    serial_number: str = ""
    assigned_to: UUID | None = None


@dataclass
class PCAssignmentHistory:
    id: UUID = field(default_factory=uuid4)
    pc_id: UUID = field(default_factory=uuid4)
    employee_id: UUID | None = None
    assigned_at: datetime = field(default_factory=datetime.now)
    notes: str = ""


# Piccoloテーブル (ORM)
class DepartmentTable(Table, tablename="departments"):
    id = PiccoloUUID(primary_key=True)
    name = Varchar(length=255, null=False)


class EmployeeTable(Table, tablename="employees"):
    id = PiccoloUUID(primary_key=True)
    name = Varchar(length=255, null=False)
    email = Varchar(length=255, null=False, unique=True)
    department_id = PiccoloUUID(null=True)
    profile_image = Bytea(null=True)


class PCTable(Table, tablename="pcs"):
    id = PiccoloUUID(primary_key=True)
    name = Varchar(length=255, null=False)
    model = Varchar(length=255, null=False)
    serial_number = Varchar(length=255, null=False, unique=True)
    assigned_to = PiccoloUUID(null=True)


class PCAssignmentHistoryTable(Table, tablename="pc_assignment_histories"):
    id = PiccoloUUID(primary_key=True)
    pc_id = PiccoloUUID(null=False)
    employee_id = PiccoloUUID(null=True)
    assigned_at = Timestamp(null=False)
    notes = Text(default="")


# データベースエンジン設定
for table in [DepartmentTable, EmployeeTable, PCTable, PCAssignmentHistoryTable]:
    table._meta._db = DB
