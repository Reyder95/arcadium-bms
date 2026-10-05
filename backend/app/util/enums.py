from enum import StrEnum
from sqlalchemy import Enum as SAEnum, CheckConstraint

class MatchResult(StrEnum):
    WIN = "win"
    LOSS = "loss"

class MatchStatus(StrEnum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class CancelReason(StrEnum):
    NO_CHART = "No Chart"

class MatchType(StrEnum):
    CASUAL = "casual"
    COMPETITIVE = "competitive"

# Creates a column type for the database that can take in an enum, store it as plaintext, and then retrieve it as an enum for use in code

def str_enum(enum_cls):
    return SAEnum(
        enum_cls,
        native_enum=False,
        create_constraint=False,
        length=max(len(member.value) for member in enum_cls),
        values_callable=lambda e: [member.value for member in e]
    )

# Creates a constraint on a column in the database such that the values that the column can hold are ONLY those from a specific enum

def enum_check(column: str, enum_cls, name: str) -> CheckConstraint:
    allowed = ", ".join(f"'{member.value}'" for member in enum_cls)
    return CheckConstraint(f"{column} IN ({allowed})", name=name)