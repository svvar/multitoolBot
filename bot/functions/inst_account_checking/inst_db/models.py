from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Float, Boolean, Enum, DateTime, VARCHAR, JSON
from .engine import Base
import enum


class AccountStatus(enum.Enum):
    ACTIVE = "active"
    BLOCK = "block"
    CHECK = "check"


class Account(Base):
    __tablename__ = "accounts"

    row_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=True)
    last_name: Mapped[str] = mapped_column(String(50), nullable=True)
    email: Mapped[str] = mapped_column(
        String(100), unique=True)
    email_password: Mapped[str] = mapped_column(String(100))
    birth_date: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    username: Mapped[str] = mapped_column(
        String(50), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    black_key: Mapped[str] = mapped_column(String, nullable=True)
    cookies: Mapped[str | None] = mapped_column(JSON, nullable=True)
    registration_date: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True))
    spent_on_number: Mapped[float] = mapped_column(Float, default=0.0)
    spent_on_email: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus), default=AccountStatus.BLOCK)
    combination: Mapped[str | None] = mapped_column(String, nullable=True)
    avatar_path: Mapped[str | None] = mapped_column(String, nullable=True)
    downloaded: Mapped[bool] = mapped_column(Boolean, default=False)
    geo: Mapped[str] = mapped_column(VARCHAR, default='ua')
    server: Mapped[str] = mapped_column(VARCHAR, nullable=True)
