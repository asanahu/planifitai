from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.deps import get_current_user
from app.auth.models import User
from app.dependencies import get_owned_progress_entry

from . import schemas, services, models

router = APIRouter(prefix="/progress", tags=["progress"])


@router.post("/", response_model=list[schemas.ProgressEntryRead], status_code=status.HTTP_201_CREATED)
def create_progress(payload: schemas.ProgressEntryCreate | schemas.ProgressEntryCreateBulk,
                    db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    entries = payload.items if isinstance(payload, schemas.ProgressEntryCreateBulk) else [payload]
    return services.create_entries(db, current_user.id, entries)


@router.get("/", response_model=list[schemas.ProgressEntryRead])
def list_progress(metric: models.MetricEnum | None = None,
                  start: date | None = None,
                  end: date | None = None,
                  db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    return services.list_entries(db, current_user.id, metric, start, end)


@router.get("/summary", response_model=schemas.ProgressSummary)
def get_summary(metric: models.MetricEnum,
                window: int | None = None,
                start: date | None = None,
                end: date | None = None,
                db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    if window and window not in (7, 30, 90):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid window")
    return services.summary(db, current_user.id, metric, start=start, end=end, window_days=window)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_progress(entry: models.ProgressEntry = Depends(get_owned_progress_entry), db: Session = Depends(get_db)):
    services.delete_entry(db, entry.user_id, entry.id)
    return
