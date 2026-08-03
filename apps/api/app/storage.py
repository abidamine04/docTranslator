from pathlib import Path

from fastapi import HTTPException, UploadFile

PDF_SIGNATURE = b"%PDF-"


def document_dir(document_id: str, storage_root: Path) -> Path:
    root = storage_root.resolve()
    destination = (root / document_id).resolve()
    if root not in destination.parents:
        raise ValueError("Unsafe storage path")
    destination.mkdir(parents=True, exist_ok=True)
    return destination


async def save_pdf(
    upload: UploadFile,
    document_id: str,
    max_upload_mb: int,
    storage_root: Path,
) -> tuple[Path, int]:
    if not upload.filename or not upload.filename.lower().endswith(".pdf"):
        raise HTTPException(415, "This milestone accepts native PDF files")
    maximum = max_upload_mb * 1024 * 1024
    path = document_dir(document_id, storage_root) / "original.pdf"
    size = 0
    with path.open("wb") as target:
        while chunk := await upload.read(1024 * 1024):
            size += len(chunk)
            if size > maximum:
                target.close()
                path.unlink(missing_ok=True)
                raise HTTPException(413, f"File exceeds the {max_upload_mb} MB limit")
            target.write(chunk)
    with path.open("rb") as source:
        if source.read(5) != PDF_SIGNATURE:
            path.unlink(missing_ok=True)
            raise HTTPException(415, "The file content is not a valid PDF")
    return path, size
