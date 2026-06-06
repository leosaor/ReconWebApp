import uuid

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.project import Project
from app.models.scan import Scan, ScanStatus, ScanType
from app.models.target import Target
from app.models.user import User, UserRole
from app.services.auth_service import login_user


def make_user(db: Session, email: str, role: UserRole = UserRole.PENTESTER) -> User:
    user = User(
        email=email,
        hashed_password=hash_password("Password123!"),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth_headers(db: Session, user: User) -> dict:
    token_resp, _ = login_user(db, user.email, "Password123!")
    return {"Authorization": f"Bearer {token_resp.access_token}"}


def make_project(db: Session, owner: User, name: str = "Test Project") -> Project:
    project = Project(owner_id=owner.id, name=name)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def make_target(db: Session, project: Project, value: str = "example.com") -> Target:
    target = Target(project_id=project.id, value=value, kind="domain")
    db.add(target)
    db.commit()
    db.refresh(target)
    return target


def make_scan(
    db: Session,
    target: Target,
    scan_type: ScanType = ScanType.SUBDOMAIN_ENUM,
    status: ScanStatus = ScanStatus.COMPLETED,
) -> Scan:
    scan = Scan(target_id=target.id, scan_type=scan_type, status=status)
    db.add(scan)
    db.commit()
    db.refresh(scan)
    return scan
