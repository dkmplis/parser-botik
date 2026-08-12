import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select

from src.db.models import AsyncSessionLocal, KufarRealtySubscription
from src.deal_type import DealType

logger = logging.getLogger(__name__)


async def add_realty_subscription(
    tg_id: int,
    deal_type_str: DealType,
    rooms: str | None,
    price_min: float | None,
    price_max: float | None,
    gtsy: str,
) -> bool:
    async with AsyncSessionLocal() as session:
        try:
            new_sub = KufarRealtySubscription(
                user_id=tg_id,
                deal_type=DealType(deal_type_str),
                rooms=rooms,
                price_min=price_min,
                price_max=price_max,
                gtsy=gtsy,
            )
            session.add(new_sub)
            await session.commit()
            p_min = new_sub.price_min // 100 if new_sub.price_min else 'Любая'
            p_max = new_sub.price_max // 100 if new_sub.price_max else 'Любая'

            logger.info(
                f"✅ Пользователь {tg_id} успешно добавил подписку на недвижимость:\n"
                f"   • Сделка: {new_sub.deal_type}\n"
                f"   • Комнат: {new_sub.rooms or 'Любое'}\n"
                f"   • Цена: от {p_min} до {p_max} BYN\n"
                f"   • Локация (gtsy): {new_sub.gtsy}"
            )
            return True
        except SQLAlchemyError as ex:
            await session.rollback()
            logger.error(
                f"Ошибка при сохранении подписки на недвижимость для {tg_id}: {ex}"
            )
            return False


async def get_all_realty_kufar_subs() -> list[KufarRealtySubscription]:
    async with AsyncSessionLocal() as session:
        try:
            stmt = select(KufarRealtySubscription)
            result = await session.scalars(stmt)
            return list(result)
        except SQLAlchemyError as e:
            logger.error(f"Ошибка чтения БД: {e}")
            return []


async def get_subs_by_user_id(user_id: int) -> list[KufarRealtySubscription]:
    async with AsyncSessionLocal() as session:
        try:
            stmt = select(KufarRealtySubscription).where(
                KufarRealtySubscription.user_id == user_id
            )
            result = await session.scalars(stmt)
            return list(result.all())
        except SQLAlchemyError as e:
            logger.error(f"Ошибка чтения БД: {e}")
            return []


async def delete_sub_by_id(sub_id: int) -> bool:
    async with AsyncSessionLocal() as session:
        sub = await session.get(KufarRealtySubscription, sub_id)
        if sub:
            await session.delete(sub)
            await session.commit()
            return True
        return False
