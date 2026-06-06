import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_writer
from app.models.user import User
from app.schemas.scan import ScanCreate, ScanResponse, ScanResultResponse
from app.services import recon_service

router = APIRouter(prefix="/api/v1", tags=["scans"])


@router.post("/targets/{target_id}/scans", response_model=ScanResponse, status_code=status.HTTP_202_ACCEPTED)
def create_scan(
    target_id: uuid.UUID,
    body: ScanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_writer),
):
    target = recon_service.get_target_or_404(db, target_id, current_user)
    return recon_service.create_scan_and_enqueue(db, target, body.scan_type)


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
