"""REST endpoints for creating and viewing HTTP monitors."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.monitor import MonitorCreate, MonitorRead
from app.services.monitor_service import (
    DuplicateMonitorURL,
    create_monitor,
    delete_monitor,
    get_monitor,
    list_monitors,
    pause_monitor,
)


router = APIRouter(prefix="/api/monitors", tags=["monitors"])


@router.post("", response_model=MonitorRead, status_code=status.HTTP_201_CREATED)
def create_monitor_endpoint(
    monitor_input: MonitorCreate,
    db: Session = Depends(get_db),
) -> MonitorRead:
    """Create a monitor and schedule its first check immediately."""

    try:
        monitor = create_monitor(db, monitor_input)
    except DuplicateMonitorURL as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    return MonitorRead.model_validate(monitor)


@router.get("", response_model=list[MonitorRead])
def list_monitors_endpoint(
    include_inactive: bool = True,
    db: Session = Depends(get_db),
) -> list[MonitorRead]:
    """List monitors for the dashboard."""

    monitors = list_monitors(db, include_inactive=include_inactive)
    return [MonitorRead.model_validate(monitor) for monitor in monitors]


@router.get("/{monitor_id}", response_model=MonitorRead)
def get_monitor_endpoint(monitor_id: UUID, db: Session = Depends(get_db)) -> MonitorRead:
    """Return one monitor or a standard 404 response."""

    monitor = get_monitor(db, monitor_id)
    if monitor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitor not found")
    return MonitorRead.model_validate(monitor)


@router.patch("/{monitor_id}/pause", response_model=MonitorRead)
def pause_monitor_endpoint(monitor_id: UUID, db: Session = Depends(get_db)) -> MonitorRead:
    """Pause a monitor without deleting its configuration or history."""

    monitor = pause_monitor(db, monitor_id)
    if monitor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitor not found")
    return MonitorRead.model_validate(monitor)


@router.delete("/{monitor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_monitor_endpoint(monitor_id: UUID, db: Session = Depends(get_db)) -> None:
    """Delete a monitor and its associated historical check results."""

    deleted = delete_monitor(db, monitor_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitor not found")
