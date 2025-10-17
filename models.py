from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from piccolo.columns import (
    Bytea,
    Boolean,
    Date,
    Text,
    Timestamp,
    UUID as PiccoloUUID,
    Varchar,
)
from piccolo.table import Table

from app.database import DB


class Role(str, Enum):
    USER = "user"
    ADMIN = "admin"


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
    resignation_date: datetime | None = None
    transfer_date: datetime | None = None
    role: Role = Role.USER


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


@dataclass
class ChatMessage:
    id: UUID = field(default_factory=uuid4)
    sender_id: UUID = field(default_factory=uuid4)
    receiver_id: UUID = field(default_factory=uuid4)
    content: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    is_read: bool = False


@dataclass
class BlogPost:
    id: UUID = field(default_factory=uuid4)
    author_id: UUID = field(default_factory=uuid4)
    title: str = ""
    content: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Tag:
    id: UUID = field(default_factory=uuid4)
    name: str = ""


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
    resignation_date = Date(null=True)
    transfer_date = Date(null=True)
    role = Varchar(length=50, null=False, default=Role.USER.value)


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


class ChatMessageTable(Table, tablename="chat_messages"):
    id = PiccoloUUID(primary_key=True)
    sender_id = PiccoloUUID(null=False)
    receiver_id = PiccoloUUID(null=False)
    content = Text(null=False)
    created_at = Timestamp(null=False)
    is_read = Boolean(default=False)


class BlogPostTable(Table, tablename="blog_posts"):
    id = PiccoloUUID(primary_key=True)
    author_id = PiccoloUUID(null=False)
    title = Varchar(length=255, null=False)
    content = Text(null=False)
    created_at = Timestamp(null=False)
    updated_at = Timestamp(null=False)


class TagTable(Table, tablename="tags"):
    id = PiccoloUUID(primary_key=True)
    name = Varchar(length=255, null=False)


# データベースエンジン設定
for table in [
    DepartmentTable,
    EmployeeTable,
    PCTable,
    PCAssignmentHistoryTable,
    ChatMessageTable,
    BlogPostTable,
    TagTable,
]:
    table._meta._db = DB
