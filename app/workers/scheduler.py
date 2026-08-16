import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.db.database import SessionLocal
from app.services import ai_service, export_service, index_service, task_service

logger = logging.getLogger(__name__)


def process_pending() -> None:
    db = SessionLocal()
    try:
        task = task_service.claim_one_pending(db)
        if task is None:
            return

        logger.info(
            "Task %s (external_id=%s) claimed: pending -> processing",
            task.id,
            task.external_id,
        )
        try:
            result = ai_service.classify(task.input_text or "")
            task_service.mark_done(db, task, result)
            logger.info(
                "Task %s (external_id=%s) done: processing -> done, result=%s",
                task.id,
                task.external_id,
                result,
            )
        except Exception as e:
            task_service.mark_failed_or_retry(db, task, str(e))
            db.refresh(task)
            logger.warning(
                "Task %s (external_id=%s) failed: processing -> %s, error=%s",
                task.id,
                task.external_id,
                task.status,
                e,
            )
    finally:
        db.close()


def export_done() -> None:
    db = SessionLocal()
    try:
        tasks = task_service.list_done_for_export(db)
        for task in tasks:
            try:
                if export_service.send_result(task):
                    task_service.mark_sent(db, task)
                    logger.info(
                        "Task %s (external_id=%s) exported: done -> sent",
                        task.id,
                        task.external_id,
                    )
                else:
                    logger.warning(
                        "Task %s (external_id=%s) export failed, status remains done",
                        task.id,
                        task.external_id,
                    )
            except Exception as e:
                logger.exception(
                    "Task %s (external_id=%s) export error: %s",
                    task.id,
                    task.external_id,
                    e,
                )
    finally:
        db.close()


def reset_stuck_job() -> None:
    db = SessionLocal()
    try:
        n = task_service.reset_stuck(db)
        if n > 0:
            logger.info("Reset %s stuck task(s): processing -> pending", n)
    finally:
        db.close()


def process_idle_documents() -> None:
    db = SessionLocal()
    try:
        document = index_service.claim_one_idle(db)
        if document is None:
            return

        logger.info(
            "Document %s claimed: idle -> syncing, source=%s",
            document.id,
            document.source,
        )
        try:
            index_service.index_document(db, document)
            db.refresh(document)
            logger.info(
                "Document %s status=%s",
                document.id,
                document.status,
            )
        except Exception as e:
            logger.warning(
                "Document %s indexing job error: %s",
                document.id,
                e,
            )
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        process_pending,
        "interval",
        seconds=settings.POLL_INTERVAL,
        id="process_pending",
    )
    scheduler.add_job(
        export_done,
        "interval",
        seconds=settings.POLL_INTERVAL,
        id="export_done",
    )
    scheduler.add_job(
        reset_stuck_job,
        "interval",
        seconds=60,
        id="reset_stuck",
    )
    scheduler.add_job(
        process_idle_documents,
        "interval",
        seconds=settings.POLL_INTERVAL,
        id="process_idle_documents",
    )
    scheduler.start()
    logger.info(
        "Scheduler started: process_pending/export_done/process_idle_documents "
        "every %ss, reset_stuck every 60s",
        settings.POLL_INTERVAL,
    )
    return scheduler
