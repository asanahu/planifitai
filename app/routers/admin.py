import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.core.config import settings
from app.core.errors import ok

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)


def require_admin_secret(x_admin_secret: Optional[str] = Header(None)):
    if not settings.AI_INTERNAL_SECRET:
        raise HTTPException(status_code=403, detail="admin not configured")
    if not x_admin_secret or x_admin_secret != settings.AI_INTERNAL_SECRET:
        raise HTTPException(status_code=403, detail="forbidden")


@router.post("/exercises/import/wger")
def import_wger(language: str = "es", dry_run: bool = False, _=Depends(require_admin_secret)):
    from scripts.import_wger import import_wger as _import

    count = _import(language=language, token=None, dry_run=dry_run)
    logger.info("admin.import_wger language=%s imported=%d dry_run=%s", language, count, dry_run)
    return ok({"imported": count})


@router.post("/exercises/import/free-db")
def import_free_db(
    url: str | None = None,
    path: str | None = None,
    dry_run: bool = False,
    translate_es: bool = True,
    update_existing: bool = False,
    _=Depends(require_admin_secret),
):
    from scripts.import_free_exercise_db import import_free_exercise_db as _import

    count = _import(
        url=url,
        path=path,
        dry_run=dry_run,
        translate_es=translate_es,
        update_existing=update_existing,
    )
    logger.info(
        "admin.import_free_db url=%s path=%s imported=%d dry_run=%s translate_es=%s update_existing=%s",
        url,
        path,
        count,
        dry_run,
        translate_es,
        update_existing,
    )
    return ok({"imported": count})
