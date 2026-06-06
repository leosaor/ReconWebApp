import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.scan import Scan, ScanStatus, ScanType
from app.models.scan_result import ScanResult
from app.models.target import Target
from app.models.user import User, UserRole


def get_project_or_404(db: Session, project_id: uuid.UUID, current_user: User) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if current_user.role != UserRole.ADMIN and project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def get_target_or_404(db: Session, target_id: uuid.UUID, current_user: User) -> Target:
    target = db.get(Target, target_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")
    get_project_or_404(db, target.project_id, current_user)
    return target


def get_scan_or_404(db: Session, scan_id: uuid.UUID, current_user: User) -> Scan:
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    get_target_or_404(db, scan.target_id, current_user)
    return scan


def create_project(db: Session, name: str, description: str | None, owner: User) -> Project:
    project = Project(owner_id=owner.id, name=name, description=description)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def list_projects(db: Session, current_user: User) -> list[Project]:
    if current_user.role == UserRole.ADMIN:
        return db.query(Project).order_by(Project.created_at.desc()).all()
    return (
        db.query(Project)
        .filter(Project.owner_id == current_user.id)
        .order_by(Project.created_at.desc())
        .all()
    )


def update_project(
    db: Session, project: Project, name: str | None, description: str | None
) -> Project:
    if name is not None:
        project.name = name
    if description is not None:
        project.description = description
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project: Project) -> None:
    db.delete(project)
    db.commit()


def create_target(
    db: Session, project: Project, value: str, kind: str
) -> Target:
    existing = (
        db.query(Target)
        .filter(Target.project_id == project.id, Target.value == value)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Target already exists")
    target = Target(project_id=project.id, value=value, kind=kind)
    db.add(target)
    db.commit()
    db.refresh(target)
    return target


def update_target(
    db: Session, target: Target, value: str | None, in_scope: bool | None
) -> Target:
    if value is not None:
        target.value = value
    if in_scope is not None:
        target.in_scope = in_scope
    db.commit()
    db.refresh(target)
    return target


def delete_target(db: Session, target: Target) -> None:
    db.delete(target)
    db.commit()


def create_scan_and_enqueue(
    db: Session, target: Target, scan_type: ScanType
) -> Scan:
    if not target.in_scope:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Target is out of scope",
        )
    scan = Scan(target_id=target.id, scan_type=scan_type, status=ScanStatus.PENDING)
    db.add(scan)
    db.commit()
    db.refresh(scan)

    from app.tasks.recon import (
        run_http_probe,
        run_port_scan,
        run_subdomain_enum,
    )  # lazy import to avoid circular

    if scan_type == ScanType.SUBDOMAIN_ENUM:
        run_subdomain_enum.delay(str(scan.id))
    elif scan_type == ScanType.HTTP_PROBE:
        run_http_probe.delay(str(scan.id))
    elif scan_type == ScanType.PORT_SCAN:
        run_port_scan.delay(str(scan.id))

    return scan
