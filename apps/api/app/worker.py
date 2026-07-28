import asyncio
from datetime import datetime, timezone

import dramatiq
from dramatiq.brokers.redis import RedisBroker

from .config import get_settings
from .db import SessionLocal
from .models import Document, JobStatus, ProcessingJob, ProviderConfiguration
from .pdf_processor import analyze_pdf, translate_document

dramatiq.set_broker(RedisBroker(url=get_settings().redis_url))


def _progress(session, job: ProcessingJob, stage: str, current: int, total: int, percent: float) -> None:
    session.refresh(job)
    if job.cancel_requested:
        raise asyncio.CancelledError()
    job.current_stage = stage
    job.current_page = current
    job.total_pages = total
    job.progress_percent = min(round(percent, 1), 100)
    session.commit()


def _finish(session, job: ProcessingJob, status: str = JobStatus.complete.value) -> None:
    job.status = status
    job.current_stage = "complete"
    job.progress_percent = 100
    job.completed_at = datetime.now(timezone.utc)
    session.commit()


def _fail(session, job: ProcessingJob, exc: BaseException) -> None:
    if isinstance(exc, asyncio.CancelledError):
        job.status = JobStatus.cancelled.value
        job.current_stage = "cancelled"
        job.cancelled_at = datetime.now(timezone.utc)
    else:
        job.status = JobStatus.failed.value
        job.current_stage = "failed"
        job.error_message = str(exc)
    session.commit()


@dramatiq.actor(max_retries=0)
def analyze_job(job_id: str) -> None:
    with SessionLocal() as session:
        job = session.get(ProcessingJob, job_id)
        if not job or job.status not in {JobStatus.queued.value, JobStatus.running.value}:
            return
        document = session.get(Document, job.document_id)
        try:
            job.status = JobStatus.running.value
            job.started_at = datetime.now(timezone.utc)
            session.commit()
            analyze_pdf(session, document, lambda *args: _progress(session, job, *args))
            warning_status = (
                JobStatus.complete_with_warnings.value
                if document.status == "analyzed_with_warnings"
                else JobStatus.complete.value
            )
            _finish(session, job, warning_status)
        except BaseException as exc:
            _fail(session, job, exc)


@dramatiq.actor(max_retries=0)
def translation_job(job_id: str, provider_id: str, source: str, target: str, tone: str) -> None:
    with SessionLocal() as session:
        job = session.get(ProcessingJob, job_id)
        if not job or job.status not in {JobStatus.queued.value, JobStatus.running.value}:
            return
        document = session.get(Document, job.document_id)
        provider = session.get(ProviderConfiguration, provider_id)
        try:
            job.status = JobStatus.running.value
            job.started_at = datetime.now(timezone.utc)
            session.commit()
            asyncio.run(translate_document(
                session,
                document,
                provider,
                target,
                source,
                tone,
                lambda *args: _progress(session, job, *args),
                lambda: bool(session.get(ProcessingJob, job.id).cancel_requested),
            ))
            failed = any(element.translation_status == "failed" for page in document.pages for element in page.elements)
            _finish(session, job, JobStatus.complete_with_warnings.value if failed else JobStatus.complete.value)
        except BaseException as exc:
            _fail(session, job, exc)
