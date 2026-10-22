import re
from typing import Annotated, Generic, TypeVar

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

T = TypeVar("T")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _email(value: str) -> str:
    value = value.strip().lower()
    if not EMAIL_RE.match(value):
        raise ValueError("Enter an email address like name@example.com")
    return value


# Plain-string email: pydantic's EmailStr rejects the reserved .local demo domains.
Email = Annotated[str, AfterValidator(_email)]
Cents = Annotated[int, Field(ge=0, le=100_000_000, description="Amount in cents (1250 = $12.50)")]


class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(Schema, Generic[T]):
    items: list[T]
    total: int
    page: int = 1
    page_size: int = 50


class Message(Schema):
    detail: str


class ReasonIn(Schema):
    reason: str = Field(min_length=3, max_length=255)


class OptionalNoteIn(Schema):
    note: str | None = Field(default=None, max_length=255)
