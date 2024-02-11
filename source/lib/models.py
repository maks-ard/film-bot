from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import SMALLINT, VARCHAR, ARRAY, BIGINT


class Base(AsyncAttrs, DeclarativeBase):
    __table_args__ = {"schema": "film-bot"}

    date_add: Mapped[datetime] = mapped_column(server_default=func.current_timestamp())
    date_update: Mapped[datetime] = mapped_column(server_default=func.current_timestamp(), onupdate=func.now())


class Users(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BIGINT, unique=True, primary_key=True)
    is_bot: Mapped[bool] = mapped_column(default=False)
    first_name: Mapped[str] = mapped_column(VARCHAR(255), nullable=True)
    last_name: Mapped[str] = mapped_column(VARCHAR(255), nullable=True)
    username: Mapped[str] = mapped_column(VARCHAR(32), nullable=True)
    language_code: Mapped[str] = mapped_column(VARCHAR(5))
    is_premium: Mapped[bool] = mapped_column(nullable=True)
    is_admin: Mapped[bool] = mapped_column(default=False)


class Films(Base):
    __tablename__ = "films"

    code: Mapped[int] = mapped_column(SMALLINT(), unique=True, primary_key=True)
    title: Mapped[str] = mapped_column(VARCHAR(150))
    description: Mapped[str] = mapped_column(VARCHAR(), nullable=True)
    links_view: Mapped[list[str]] = mapped_column(ARRAY(VARCHAR()), nullable=True)
    source_url: Mapped[str] = mapped_column(nullable=True)

    def __str__(self):
        return f"{self.code} - {self.title}"
