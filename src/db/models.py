from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from src.deal_type import DealType

engine = create_async_engine("sqlite+aiosqlite:///data/bot_database.db", echo=True)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    tg_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    is_active: Mapped[bool] = mapped_column(Boolean)
    kufar_subs: Mapped[list["KufarSubscription"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    realty_subs: Mapped[list["KufarRealtySubscription"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class KufarSubscription(Base):
    __tablename__ = "kufar_subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.tg_id", ondelete="CASCADE"))

    query: Mapped[str] = mapped_column(String(255))
    region_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    area_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    user: Mapped["User"] = relationship(back_populates="kufar_subs")


class KufarRealtySubscription(Base):
    __tablename__ = "kufar_realty_subscription"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.tg_id", ondelete="CASCADE"))

    deal_type: Mapped[DealType] = mapped_column(nullable=True)
    rooms: Mapped[str] = mapped_column(nullable=True)
    price_min: Mapped[int] = mapped_column(nullable=True)
    price_max: Mapped[int] = mapped_column(nullable=True)
    gtsy: Mapped[str] = mapped_column(nullable=False)

    user: Mapped["User"] = relationship(back_populates="realty_subs")


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
