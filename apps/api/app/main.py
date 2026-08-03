import asyncio
import json
import shutil
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from sqlalchemy import select, text
from sqlalchemy.orm import Session, selectinload

from .application_settings import effective_storage_root, get_application_settings
from .config import get_settings
from .db import Base, SessionLocal, engine, get_db
from .models import (
    Document,
    DocumentElement,
    ElementStatus,
    Export,
    Page,
    ProcessingJob,
    ProviderConfiguration,
)
from .pdf_processor import export_pdf
from .providers import TranslationProvider
from .quality import completion_report
from .schemas import ApplicationSettingsWrite, ElementPatch, ProviderTest, ProviderWrite, TranslateRequest
from .security import admin_token_error, encrypt_secret, require_admin
from .storage import document_dir, save_pdf
from .worker import analyze_job, translation_job

settings = get_settings()
app = FastAPI(title="DocTranslator API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def authorize_api(request: Request, call_next):
    if request.url.path.startswith("/api/") and request.method != "OPTIONS":
        if error := admin_token_error(request.headers.get("X-Admin-Token", "")):
            return JSONResponse(status_code=error[0], content={"detail": error[1]})
    return await call_next(request)

@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        effective_storage_root(session).mkdir(parents=True, exist_ok=True)


def document_view(document: Document) -> dict:
    return {
        "id": document.id,
        "filename": document.filename,
        "mime_type": document.mime_type,
        "size_bytes": document.size_bytes,
        "page_count": document.page_count,
        "source_language": document.source_language,
        "target_language": document.target_language,
        "status": document.status,
        "created_at": document.created_at,
    }


def job_view(job: ProcessingJob) -> dict:
    return {
        "id": job.id,
        "document_id": job.document_id,
        "status": job.status,
        "current_stage": job.current_stage,
        "current_page": job.current_page,
        "total_pages": job.total_pages,
        "progress_percent": job.progress_percent,
        "error_message": job.error_message,
    }


@app.get("/health/live")
def live() -> dict:
    return {"status": "ok"}


@app.get("/health/ready")
def ready(db: Session = Depends(get_db)) -> dict:
    checks = {"database": False, "redis": False}
    try:
        db.execute(text("select 1"))
        checks["database"] = True
    except Exception:
        pass
    try:
        import redis
        checks["redis"] = bool(redis.from_url(settings.redis_url).ping())
    except Exception:
        pass
    if not all(checks.values()):
        raise HTTPException(503, detail=checks)
    return {"status": "ready", "checks": checks}


@app.post("/api/documents/upload", status_code=201)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)) -> dict:
    app_settings = get_application_settings(db)
    upload_root = effective_storage_root(db)
    document = Document(
        filename=Path(file.filename or "document.pdf").name,
        mime_type=file.content_type or "application/pdf",
        size_bytes=0,
        source_path="",
    )
    db.add(document)
    db.flush()
    try:
        path, size = await save_pdf(
            file, document.id, app_settings.max_upload_mb, upload_root
        )
        document.source_path = str(path)
        document.size_bytes = size
        job = ProcessingJob(document_id=document.id, current_stage="parsing_document")
        db.add(job)
        db.commit()
        analyze_job.send(job.id)
        return {"document": document_view(document), "job": job_view(job)}
    except Exception:
        db.rollback()
        failed_path = (
            Path(document.source_path).parent
            if document.source_path
            else document_dir(document.id, upload_root)
        )
        shutil.rmtree(failed_path, ignore_errors=True)
        raise


@app.get("/api/documents")
def list_documents(db: Session = Depends(get_db)) -> list[dict]:
    documents = db.scalars(select(Document).order_by(Document.created_at.desc())).all()
    return [document_view(document) for document in documents]


@app.get("/api/documents/{document_id}")
def get_document(document_id: str, db: Session = Depends(get_db)) -> dict:
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(404, "Document not found")
    result = document_view(document)
    result["quality"] = quality_report(db, document_id)
    return result


@app.delete("/api/documents/{document_id}", status_code=204)
def delete_document(document_id: str, db: Session = Depends(get_db)) -> None:
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(404, "Document not found")
    path = Path(document.source_path).parent
    db.delete(document)
    db.commit()
    shutil.rmtree(path, ignore_errors=True)


@app.get("/api/documents/{document_id}/file")
def original_file(document_id: str, db: Session = Depends(get_db)) -> FileResponse:
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(404, "Document not found")
    return FileResponse(document.source_path, media_type="application/pdf", filename=document.filename)


@app.get("/api/documents/{document_id}/pages")
def list_pages(document_id: str, db: Session = Depends(get_db)) -> list[dict]:
    pages = db.scalars(select(Page).where(Page.document_id == document_id).order_by(Page.page_index)).all()
    return [
        {
            "id": p.id,
            "page_index": p.page_index,
            "width": p.width,
            "height": p.height,
            "page_type": p.page_type,
        }
        for p in pages
    ]


@app.get("/api/documents/{document_id}/elements")
def list_elements(document_id: str, db: Session = Depends(get_db)) -> list[dict]:
    elements = db.execute(
        select(DocumentElement, Page.page_index)
        .join(Page)
        .where(Page.document_id == document_id)
        .order_by(Page.page_index, DocumentElement.id)
    ).all()
    return [{
        "id": e.id,
        "page_number": page_index + 1,
        "bounding_box": e.bounding_box,
        "original_text": e.original_text,
        "translated_text": e.translated_text,
        "source_language": e.source_language,
        "target_language": e.target_language,
        "confidence": e.confidence,
        "translation_status": e.translation_status,
        "style": e.style_json,
        "reviewed": e.reviewed,
    } for e, page_index in elements]


@app.patch("/api/elements/{element_id}")
def patch_element(element_id: str, body: ElementPatch, db: Session = Depends(get_db)) -> dict:
    element = db.get(DocumentElement, element_id)
    if not element:
        raise HTTPException(404, "Element not found")
    element.translated_text = body.translated_text
    element.translation_status = ElementStatus.manually_edited.value
    db.commit()
    return {"id": element.id, "translation_status": element.translation_status}


@app.post("/api/elements/{element_id}/review")
def review_element(element_id: str, db: Session = Depends(get_db)) -> dict:
    element = db.get(DocumentElement, element_id)
    if not element:
        raise HTTPException(404, "Element not found")
    element.reviewed = True
    db.commit()
    return {"id": element.id, "reviewed": True}


@app.post("/api/documents/{document_id}/translate", status_code=202)
def translate(document_id: str, body: TranslateRequest, db: Session = Depends(get_db)) -> dict:
    app_settings = get_application_settings(db)
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(404, "Document not found")
    provider = db.get(ProviderConfiguration, body.provider_id) if body.provider_id else db.scalar(
        select(ProviderConfiguration).where(ProviderConfiguration.is_active.is_(True))
    )
    if not provider:
        raise HTTPException(409, "Configure and activate a translation provider in Settings")
    source = body.source_language or document.source_language or "auto"
    job = ProcessingJob(document_id=document.id, current_stage="queued")
    db.add(job)
    db.commit()
    target = body.target_language or app_settings.default_target_language
    tone = body.tone or app_settings.default_translation_tone
    translation_job.send(job.id, provider.id, source, target, tone)
    return job_view(job)


@app.post("/api/documents/{document_id}/cancel")
def cancel(document_id: str, db: Session = Depends(get_db)) -> dict:
    job = db.scalar(
        select(ProcessingJob)
        .where(ProcessingJob.document_id == document_id, ProcessingJob.status.in_(["queued", "running"]))
        .order_by(ProcessingJob.created_at.desc())
    )
    if not job:
        raise HTTPException(404, "No active job found")
    job.cancel_requested = True
    db.commit()
    return job_view(job)


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db)) -> dict:
    job = db.get(ProcessingJob, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job_view(job)


@app.get("/api/jobs/{job_id}/events")
async def job_events(job_id: str) -> StreamingResponse:
    async def stream():
        last = ""
        while True:
            from .db import SessionLocal
            with SessionLocal() as session:
                job = session.get(ProcessingJob, job_id)
                if not job:
                    yield f"event: error\ndata: {json.dumps({'message': 'Job not found'})}\n\n"
                    break
                payload = json.dumps(job_view(job), default=str)
                if payload != last:
                    yield f"data: {payload}\n\n"
                    last = payload
                if job.status in {"complete", "complete_with_warnings", "failed", "cancelled"}:
                    break
            await asyncio.sleep(0.75)
    return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


def quality_report(db: Session, document_id: str) -> dict:
    return completion_report(db, document_id)


@app.post("/api/documents/{document_id}/export", status_code=201)
def create_export(document_id: str, db: Session = Depends(get_db)) -> dict:
    document = db.scalar(
        select(Document)
        .options(selectinload(Document.pages).selectinload(Page.elements))
        .where(Document.id == document_id)
    )
    if not document:
        raise HTTPException(404, "Document not found")
    export = Export(document_id=document.id, export_type="translated_pdf", status="processing")
    db.add(export)
    db.flush()
    destination = Path(document.source_path).parent / f"translated-{export.id}.pdf"
    try:
        rendered, overflow = export_pdf(db, document, destination)
        export.path = str(destination)
        report = completion_report(db, document.id)
        export.status = (
            "complete"
            if report["completion_status"] == "complete" and overflow == 0
            else "complete_with_warnings"
        )
        db.commit()
        return {"id": export.id, "status": export.status, "rendered_blocks": rendered, "overflow_warnings": overflow}
    except Exception as exc:
        export.status = "failed"
        export.error_message = str(exc)
        db.commit()
        raise HTTPException(422, f"Export failed: {exc}") from exc


@app.get("/api/exports/{export_id}/download")
def download_export(export_id: str, db: Session = Depends(get_db)) -> FileResponse:
    export = db.get(Export, export_id)
    if not export or not export.path or export.status not in {"complete", "complete_with_warnings"}:
        raise HTTPException(404, "Completed export not found")
    return FileResponse(export.path, media_type="application/pdf", filename="translated.pdf")


def provider_view(provider: ProviderConfiguration) -> dict:
    return {
        "id": provider.id,
        "name": provider.name,
        "provider_type": provider.provider_type,
        "base_url": provider.base_url,
        "has_api_key": bool(provider.encrypted_api_key),
        "model": provider.model,
        "timeout_seconds": provider.timeout_seconds,
        "max_retries": provider.max_retries,
        "batch_size": provider.batch_size,
        "context_size": provider.context_size,
        "temperature": provider.temperature,
        "custom_system_prompt": provider.custom_system_prompt,
        "rate_limit_per_minute": provider.rate_limit_per_minute,
        "max_output_tokens": provider.max_output_tokens,
        "chat_completions_path": provider.chat_completions_path,
        "models_path": provider.models_path,
        "translate_path": provider.translate_path,
        "custom_headers": provider.custom_headers,
        "verify_tls": provider.verify_tls,
        "is_active": provider.is_active,
    }


@app.get("/api/providers")
def list_providers(db: Session = Depends(get_db)) -> list[dict]:
    providers = db.scalars(select(ProviderConfiguration).order_by(ProviderConfiguration.name))
    return [provider_view(value) for value in providers]


@app.post("/api/providers", dependencies=[Depends(require_admin)], status_code=201)
def create_provider(body: ProviderWrite, db: Session = Depends(get_db)) -> dict:
    values = body.model_dump(mode="json", exclude={"api_key"})
    if body.is_active:
        db.query(ProviderConfiguration).update({"is_active": False})
    provider = ProviderConfiguration(**values, encrypted_api_key=encrypt_secret(body.api_key))
    db.add(provider)
    db.commit()
    return provider_view(provider)


@app.put("/api/providers/{provider_id}", dependencies=[Depends(require_admin)])
def update_provider(provider_id: str, body: ProviderWrite, db: Session = Depends(get_db)) -> dict:
    provider = db.get(ProviderConfiguration, provider_id)
    if not provider:
        raise HTTPException(404, "Provider not found")
    if body.is_active:
        db.query(ProviderConfiguration).update({"is_active": False})
    for key, value in body.model_dump(mode="json", exclude={"api_key"}).items():
        setattr(provider, key, value)
    if body.api_key is not None:
        provider.encrypted_api_key = encrypt_secret(body.api_key)
    db.commit()
    return provider_view(provider)


@app.post("/api/providers/test", dependencies=[Depends(require_admin)])
async def test_provider(body: ProviderTest, db: Session = Depends(get_db)) -> dict:
    provider = db.get(ProviderConfiguration, body.provider_id)
    if not provider:
        raise HTTPException(404, "Provider not found")
    try:
        prompt = get_application_settings(db).translation_system_prompt
        output = await TranslationProvider(provider, prompt).translate(["Hello"], "en", "fr", "neutral")
        return {"ok": True, "sample": output[0]}
    except Exception as exc:
        raise HTTPException(502, f"Connection test failed: {exc}") from exc


def application_settings_view(value) -> dict:
    return {
        "default_target_language": value.default_target_language,
        "ocr_confidence_threshold": value.ocr_confidence_threshold,
        "max_upload_mb": value.max_upload_mb,
        "max_page_count": value.max_page_count,
        "file_retention_days": value.file_retention_days,
        "default_translation_tone": value.default_translation_tone,
        "translation_system_prompt": value.translation_system_prompt,
        "storage_root": value.storage_root,
        "language_detection_sample_chars": value.language_detection_sample_chars,
    }


@app.get("/api/settings")
def read_application_settings(db: Session = Depends(get_db)) -> dict:
    return application_settings_view(get_application_settings(db))


@app.put("/api/settings", dependencies=[Depends(require_admin)])
def update_application_settings(
    body: ApplicationSettingsWrite, db: Session = Depends(get_db)
) -> dict:
    value = get_application_settings(db)
    for key, setting in body.model_dump().items():
        setattr(value, key, setting)
    root = Path(value.storage_root).expanduser().resolve()
    try:
        root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise HTTPException(422, f"Storage root is not writable: {exc}") from exc
    db.commit()
    return application_settings_view(value)


@app.get("/api/languages")
def languages() -> list[dict]:
    return [
        {"code": "ar", "name": "Arabic"}, {"code": "zh", "name": "Chinese"},
        {"code": "en", "name": "English"}, {"code": "fr", "name": "French"},
        {"code": "de", "name": "German"}, {"code": "he", "name": "Hebrew"},
        {"code": "hi", "name": "Hindi"}, {"code": "it", "name": "Italian"},
        {"code": "ja", "name": "Japanese"}, {"code": "ko", "name": "Korean"},
        {"code": "pt", "name": "Portuguese"}, {"code": "ru", "name": "Russian"},
        {"code": "es", "name": "Spanish"}, {"code": "tr", "name": "Turkish"},
    ]
