import asyncio
import logging

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from app.common.ensure_time import now_utc
from app.task.models import TaskStatus


logger = logging.getLogger(__name__)


async def process_overdue_tasks(
    session: AsyncSession,
) -> int:
    """
    Find overdue active tasks and cancel them.

    Returns:
        Number of tasks that were cancelled.
    """

    from app.task.dao import TaskDAO

    tasks = await TaskDAO.get_overdue(
        session
    )

    for task in tasks:
        task.status = TaskStatus.CANCELLED

    if tasks:
        await session.commit()

    return len(tasks)


async def overdue_tasks_worker(
    session_factory: async_sessionmaker[AsyncSession],
    interval: int = 60,
) -> None:
    """
    Periodically process overdue tasks.
    """

    while True:
        try:
            async with session_factory() as session:
                cancelled_count = (
                    await process_overdue_tasks(
                        session
                    )
                )

                if cancelled_count:
                    logger.info(
                        "Automatically cancelled "
                        "%s overdue task(s)",
                        cancelled_count,
                    )

        except asyncio.CancelledError:
            logger.info(
                "Overdue tasks worker stopped"
            )
            raise

        except Exception:
            logger.exception(
                "Error while processing overdue tasks"
            )

        await asyncio.sleep(interval)