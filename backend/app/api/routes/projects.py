import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_writer
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.schemas.target import TargetCreate, TargetResponse, TargetUpdate
from app.services import recon_service

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    body: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_writer),
):
    return recon_service.create_project(db, body.name, body.description, current_user)


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return recon_service.list_projects(db, current_user)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return recon_service.get_project_or_404(db, project_id, current_user)


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: uuid.UUID,
    body: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_writer),
):
    project = recon_service.get_project_or_404(db, project_id, current_user)
    return recon_service.update_project(db, project, body.name, body.description)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_writer),
):
    project = recon_service.get_project_or_404(db, project_id, current_user)
    recon_service.delete_project(db, project)


# --- Targets (sub-rotas) ---

@router.post("/{project_id}/targets", response_model=TargetResponse, status_code=status.HTTP_201_CREATED)
def create_target(
    project_id: uuid.UUID,
    body: TargetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_writer),
):
    project = recon_service.get_project_or_404(db, project_id, current_user)
    return recon_service.create_target(db, project, body.value, body.kind)


@router.get("/{project_id}/targets", response_model=list[TargetResponse])
def list_targets(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = recon_service.get_project_or_404(db, project_id, current_user)
    return project.targets


@router.patch("/{project_id}/targets/{target_id}", response_model=TargetResponse)
def update_target(
    project_id: uuid.UUID,
    target_id: uuid.UUID,
    body: TargetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_writer),
):
    recon_service.get_project_or_404(db, project_id, current_user)
    target = recon_service.get_target_or_404(db, target_id, current_user)
    return recon_service.update_target(db, target, body.value)


@router.delete("/{project_id}/targets/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_target(
    project_id: uuid.UUID,
    target_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_writer),
):
    recon_service.get_project_or_404(db, project_id, current_user)
    target = recon_service.get_target_or_404(db, target_id, current_user)
    recon_service.delete_target(db, target)
