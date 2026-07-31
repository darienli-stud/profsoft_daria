import logging

import httpx

from app.core.config import settings
from app.models.database_models import Task

logger = logging.getLogger(__name__)


def send_result(task: Task) -> bool:
    payload = {"external_id": task.external_id, "result": task.result}

    if settings.TEST_MODE or not settings.RESULT_URL:
        logger.info("Export skipped (TEST_MODE or empty RESULT_URL): %s", payload)
        return True

    response = httpx.post(settings.RESULT_URL, json=payload, timeout=10)
    return 200 <= response.status_code < 300
