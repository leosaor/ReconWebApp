import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_writer
from app.core.config import settings
from app.core.rate_limit import get_client_ip, limiter
from app.models.scan import ScanType
from app.models.user import User
from app.schemas.scan import ScanCreate, ScanResponse, ScanResultResponse
from app.services.artifacts import content_fuzz_path, nuclei_scan_path
from app.services import recon_service

router = APIRouter(prefix="/api/v1", tags=["scans"])


@router.post("/targets/{target_id}/scans", response_model=ScanResponse, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit(settings.scan_create_rate_limit)
def create_scan(
    request: Request,
    target_id: uuid.UUID,
    body: ScanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_writer),
):
    target = recon_service.get_target_or_404(db, target_id, current_user)
    return recon_service.create_scan_and_enqueue(
        db,
        target,
        body.scan_type,
        current_user,
        request_ip=get_client_ip(request),
    )


@router.get("/targets/{target_id}/scans", response_model=list[ScanResponse])
def list_scans(
    target_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target = recon_service.get_target_or_404(db, target_id, current_user)
    return target.scans


@router.get("/scans/{scan_id}", response_model=ScanResponse)
def get_scan(
    scan_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return recon_service.get_scan_or_404(db, scan_id, current_user)


@router.get("/scans/{scan_id}/results", response_model=list[ScanResultResponse])
def list_scan_results(
    scan_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scan = recon_service.get_scan_or_404(db, scan_id, current_user)
    return scan.results


@router.get("/scans/{scan_id}/artifact")
def download_scan_artifact(
    scan_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scan = recon_service.get_scan_or_404(db, scan_id, current_user)
    artifacts = {
        ScanType.CONTENT_FUZZ: (
            content_fuzz_path(scan.target),
            "text/plain; charset=utf-8",
            f"feroxbuster-{scan.id}.txt",
        ),
        ScanType.NUCLEI_SCAN: (
            nuclei_scan_path(scan.target),
            "text/plain; charset=utf-8",
            f"nuclei-{scan.id}.txt",
        ),
    }
    artifact = artifacts.get(scan.scan_type)
    if artifact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")

    path, media_type, filename = artifact
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")

    return FileResponse(
        path,
        media_type=media_type,
        filename=filename,
    )
