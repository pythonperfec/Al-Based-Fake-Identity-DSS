import asyncio
import logging
from app.domain.interfaces import IJobQueue
from app.core.database import AsyncSessionLocal
from app.services.orchestrator import ScreeningOrchestrator

logger = logging.getLogger(__name__)


class InProcessJobQueue(IJobQueue):
    """In-process background job queue executing tasks via asyncio."""

    def __init__(self, orchestrator: ScreeningOrchestrator = None):
        self.orchestrator = orchestrator or ScreeningOrchestrator()

    async def enqueue(self, screening_id: str) -> None:
        """Enqueue screening for background execution."""
        asyncio.create_task(self._run_job(screening_id))

    async def _run_job(self, screening_id: str) -> None:
        try:
            async with AsyncSessionLocal() as session:
                await self.orchestrator.process_screening(screening_id, session)
        except Exception as e:
            logger.error(f"Error executing job for screening_id {screening_id}: {e}", exc_info=True)

