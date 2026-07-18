from sqlalchemy import String, BigInteger, ForeignKey, Integer, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession
)

engine = create_async_engine("sqlite+aiosqlite:///bot_database.db", echo=True)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __table__ = 'users'

    tg_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    is_active: Mapped[bool] = mapped_column(Boolean)
    kufar_subs: Mapped[list['KufarSubscription']] = relationship(
        back_populates='user', cascade="all, delete-orphan"
    )


class KufarSubscription(Base):
    __tablename__ = 'kufar_subscriptions'

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.tg_id', ondelete='CASCADE'))

    name: Mapped[str] = mapped_column(String(255))
    region_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    area_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    user: Mapped["User"] = relationship(back_populates="kufar_subs")


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
