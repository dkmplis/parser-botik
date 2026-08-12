import logging

from sqlalchemy import exists, select

from src.db.models import AsyncSessionLocal, User

logger = logging.getLogger(__name__)


async def check_user_exists(tg_id: int) -> bool:
    async with AsyncSessionLocal() as session:
        stmt = select(exists().where(User.tg_id == tg_id))
        result = await session.scalar(stmt)
        return result


async def create_user(tg_id: int):
    async with AsyncSessionLocal() as session:
        new_user = User(tg_id=tg_id, is_active=True)
        session.add(new_user)
        await session.commit()
        logger.info(f"Зарегистрирован новый пользователь: {tg_id}")
