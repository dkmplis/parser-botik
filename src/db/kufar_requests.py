import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.db.models import AsyncSessionLocal, KufarSubscription

logger = logging.getLogger(__name__)


async def get_all_kufar_subs() -> list[KufarSubscription]:
    async with AsyncSessionLocal() as session:
        try:
            stmt = select(KufarSubscription)
            result = await session.scalars(stmt)
            return list(result.all())
        except SQLAlchemyError as e:
            logger.error(f"Ошибка чтения БД: {e}")
            return []


async def add_kufar_sub(
    tg_id: int, query: str, region_id: int | None, area_id: int | None
) -> bool:
    async with AsyncSessionLocal() as session:
        try:
            new_sub = KufarSubscription(
                user_id=tg_id, query=query, region_id=region_id, area_id=area_id
            )
            session.add(new_sub)
            await session.commit()
            logger.info(f"Пользователь {tg_id} добавил подписку: {query}")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при сохранении подписки на {query} для {tg_id}: {e}")
            return False


async def get_subs_by_user_id(user_id: int) -> list[KufarSubscription]:
    async with AsyncSessionLocal() as session:
        try:
            stmt = select(KufarSubscription).where(KufarSubscription.user_id == user_id)
            result = await session.scalars(stmt)
            return list(result.all())
        except SQLAlchemyError as e:
            logger.error(f"Ошибка чтения БД: {e}")
            return []


async def delete_kufar_sub_by_id(sub_id: int) -> bool:
    async with AsyncSessionLocal() as session:
        sub = await session.get(KufarSubscription, sub_id)
        if sub:
            await session.delete(sub)
            await session.commit()
            logger.info(f"Подписка {sub_id} удалена")
            return True
        return False
