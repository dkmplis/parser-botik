import time
import logging

from functools import wraps

logger = logging.getLogger(__name__)


def async_timed(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        query = args[0] if args else kwargs.get('query', 'unknown')

        start = time.perf_counter()
        try:
            return await func(*args, **kwargs)
        finally:
            elapsed = (time.perf_counter() - start) * 1000
            logger.info(
                f" [ТАЙМЕР] Запрос '{query}' обработан за {elapsed} мс")
    return wrapper
