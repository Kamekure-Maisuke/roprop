from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from piccolo.columns import (
    UUID as PiccoloUUID,
)
from piccolo.columns import (
    Boolean,
    Bytea,
    Date,
    ForeignKey,
    Integer,
    Text,
    Timestamp,
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
class Tag:
    id: UUID = field(default_factory=uuid4)
    name: str = ""


@dataclass
class BlogPost:
    id: UUID = field(default_factory=uuid4)
    author_id: UUID = field(default_factory=uuid4)
    title: str = ""
    content: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: list[Tag] = field(default_factory=list)
    like_count: int = 0
    is_liked: bool = False


@dataclass
class BlogLike:
    id: UUID = field(default_factory=uuid4)
    blog_post_id: UUID = field(default_factory=uuid4)
    employee_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class MeetingRoom:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    capacity: int = 0
    location: str = ""
    equipment: str = ""


@dataclass
class MeetingRoomReservation:
    id: UUID = field(default_factory=uuid4)
    meeting_room_id: UUID = field(default_factory=uuid4)
    title: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime = field(default_factory=datetime.now)
    created_by: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ReservationParticipant:
    id: UUID = field(default_factory=uuid4)
    reservation_id: UUID = field(default_factory=uuid4)
    employee_id: UUID = field(default_factory=uuid4)


# Piccoloテーブル (ORM)
class DepartmentTable(Table, tablename="departments"):
    id = PiccoloUUID(primary_key=True)
    name = Varchar(length=255, null=False)


class EmployeeTable(Table, tablename="employees"):
    id = PiccoloUUID(primary_key=True)
    name = Varchar(length=255, null=False)
    email = Varchar(length=255, null=False, unique=True)
    department_id = ForeignKey(references=DepartmentTable, null=True)
    profile_image = Bytea(null=True)
    resignation_date = Date(null=True)
    transfer_date = Date(null=True)
    role = Varchar(length=50, null=False, default=Role.USER.value)


class PCTable(Table, tablename="pcs"):
    id = PiccoloUUID(primary_key=True)
    name = Varchar(length=255, null=False)
    model = Varchar(length=255, null=False)
    serial_number = Varchar(length=255, null=False, unique=True)
    assigned_to = ForeignKey(references=EmployeeTable, null=True)


class PCAssignmentHistoryTable(Table, tablename="pc_assignment_histories"):
    id = PiccoloUUID(primary_key=True)
    pc_id = ForeignKey(references=PCTable, null=False)
    employee_id = ForeignKey(references=EmployeeTable, null=True)
    assigned_at = Timestamp(null=False)
    notes = Text(default="")


class ChatMessageTable(Table, tablename="chat_messages"):
    id = PiccoloUUID(primary_key=True)
    sender_id = ForeignKey(references=EmployeeTable, null=False)
    receiver_id = ForeignKey(references=EmployeeTable, null=False)
    content = Text(null=False)
    created_at = Timestamp(null=False)
    is_read = Boolean(default=False)


class BlogPostTable(Table, tablename="blog_posts"):
    id = PiccoloUUID(primary_key=True)
    author_id = ForeignKey(references=EmployeeTable, null=False)
    title = Varchar(length=255, null=False)
    content = Text(null=False)
    created_at = Timestamp(null=False)
    updated_at = Timestamp(null=False)


class TagTable(Table, tablename="tags"):
    id = PiccoloUUID(primary_key=True)
    name = Varchar(length=255, null=False)


class BlogPostTagTable(Table, tablename="blog_post_tags"):
    id = PiccoloUUID(primary_key=True)
    blog_post_id = ForeignKey(references=BlogPostTable, null=False)
    tag_id = ForeignKey(references=TagTable, null=False)


class BlogLikeTable(Table, tablename="blog_likes"):
    id = PiccoloUUID(primary_key=True)
    blog_post_id = ForeignKey(references=BlogPostTable, null=False)
    employee_id = ForeignKey(references=EmployeeTable, null=False)
    created_at = Timestamp(null=False)


class MeetingRoomTable(Table, tablename="meeting_rooms"):
    id = PiccoloUUID(primary_key=True)
    name = Varchar(length=255, null=False)
    capacity = Integer(null=False, default=0)
    location = Varchar(length=255, null=False)
    equipment = Text(default="")


class MeetingRoomReservationTable(Table, tablename="meeting_room_reservations"):
    id = PiccoloUUID(primary_key=True)
    meeting_room_id = ForeignKey(references=MeetingRoomTable, null=False)
    title = Varchar(length=255, null=False)
    start_time = Timestamp(null=False)
    end_time = Timestamp(null=False)
    created_by = ForeignKey(references=EmployeeTable, null=False)
    created_at = Timestamp(null=False)


class ReservationParticipantTable(Table, tablename="reservation_participants"):
    id = PiccoloUUID(primary_key=True)
    reservation_id = ForeignKey(references=MeetingRoomReservationTable, null=False)
    employee_id = ForeignKey(references=EmployeeTable, null=False)


# データベースエンジン設定
# テスト環境以外で本番DBエンジンを設定
if DB is not None:
    for table in [
        DepartmentTable,
        EmployeeTable,
        PCTable,
        PCAssignmentHistoryTable,
        ChatMessageTable,
        BlogPostTable,
        TagTable,
        BlogPostTagTable,
        BlogLikeTable,
        MeetingRoomTable,
        MeetingRoomReservationTable,
        ReservationParticipantTable,
    ]:
        table._meta._db = DB
