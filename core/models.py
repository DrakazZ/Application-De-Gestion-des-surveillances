"""
Dataclasses for solver data models with optional dict conversion helpers.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class Teacher:
    index: Optional[int] = None
    id: Optional[str] = None
    name: str = ""
    grade: str = ""
    max_sessions: int = 0
    assigned_sessions: Any = field(default_factory=set)
    total_sessions: int = 0
    wishes: Any = field(default_factory=dict)
    wish_submission_index: Optional[int] = None


@dataclass
class Session:
    id: Optional[int] = None
    key: str = ""
    date: str = ""
    time: str = ""
    base_required_staff: int = 0
    padding: int = 0
    total_required_staff: int = 0
    responsible_teachers: Any = field(default_factory=list)


def teacher_from_dict(data: Dict[str, Any]) -> Teacher:
    """Create a Teacher from a dict without coercing field types."""
    return Teacher(
        index=data.get("index"),
        id=data.get("id"),
        name=data.get("name", ""),
        grade=data.get("grade", ""),
        max_sessions=data.get("max_sessions", 0),
        assigned_sessions=data.get("assigned_sessions", set()),
        total_sessions=data.get("total_sessions", 0),
        wishes=data.get("wishes", {}),
        wish_submission_index=data.get("wish_submission_index"),
    )


def teacher_to_dict(teacher: Teacher) -> Dict[str, Any]:
    """Convert a Teacher to a dict matching the solver schema."""
    return {
        "index": teacher.index,
        "id": teacher.id,
        "name": teacher.name,
        "grade": teacher.grade,
        "max_sessions": teacher.max_sessions,
        "assigned_sessions": teacher.assigned_sessions,
        "total_sessions": teacher.total_sessions,
        "wishes": teacher.wishes,
        "wish_submission_index": teacher.wish_submission_index,
    }


def session_from_dict(data: Dict[str, Any]) -> Session:
    """Create a Session from a dict without coercing field types."""
    return Session(
        id=data.get("id"),
        key=data.get("key", ""),
        date=data.get("date", ""),
        time=data.get("time", ""),
        base_required_staff=data.get("base_required_staff", 0),
        padding=data.get("padding", 0),
        total_required_staff=data.get("total_required_staff", 0),
        responsible_teachers=data.get("responsible_teachers", []),
    )


def session_to_dict(session: Session) -> Dict[str, Any]:
    """Convert a Session to a dict matching the solver schema."""
    return {
        "id": session.id,
        "key": session.key,
        "date": session.date,
        "time": session.time,
        "base_required_staff": session.base_required_staff,
        "padding": session.padding,
        "total_required_staff": session.total_required_staff,
        "responsible_teachers": session.responsible_teachers,
    }


__all__ = [
    "Teacher",
    "Session",
    "teacher_from_dict",
    "teacher_to_dict",
    "session_from_dict",
    "session_to_dict",
]
