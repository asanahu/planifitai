from __future__ import annotations

import logging
from typing import List, Optional
from uuid import uuid4

import requests
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.nutrition.models import Food, FoodSource
from app.nutrition import schemas as nutrition_schemas
from services.food_sources import (
    FoodDetails as SourceFoodDetails,
    UnsupportedFoodSourceError,
    get_food_source_adapter,
)


logger = logging.getLogger(__name__)


MAX_PAGE_SIZE = 25


def _map_details_to_food_entity(details: SourceFoodDetails, existing: Optional[Food] = None) -> Food:
    brand = None
    # Try to infer brand from raw_payload (FDC commonly has brandName/brandOwner)
    raw = details.raw_payload or {}
    brand = raw.get("brandOwner") or raw.get("brandName")
    entity = existing or Food(id=str(uuid4()))
    entity.name = details.name
    entity.brand = brand
    entity.source = FoodSource(details.source)
    entity.source_id = details.source_id
    entity.calories_kcal = details.calories_kcal
    entity.protein_g = details.protein_g
    entity.carbs_g = details.carbs_g
    entity.fat_g = details.fat_g
    entity.raw_payload = raw
    # keep defaults
    return entity


def _ensure_food_from_source(db: Session, source: FoodSource, source_id: str) -> Optional[Food]:
    existing: Food | None = (
        db.query(Food).filter(Food.source == source, Food.source_id == source_id).first()
    )
    if existing:
        return existing
    try:
        adapter = get_food_source_adapter()
    except UnsupportedFoodSourceError as e:
        logger.warning("Food source unsupported: %s", e)
        return None
    try:
        logger.info("Fetching FDC details for source_id=%s", source_id)
        details: SourceFoodDetails = adapter.get_details(source_id)
    except requests.exceptions.HTTPError as he:
        if getattr(he.response, "status_code", None) == 429:
            logger.info("FDC 429 rate-limited. Skipping external fetch for %s", source_id)
            return None
        logger.warning("FDC details HTTP error for %s: %s", source_id, he)
        return None
    except requests.exceptions.RequestException as re:
        logger.warning("FDC details request failed for %s: %s", source_id, re)
        return None
    except Exception as ex:
        logger.exception("Unexpected error fetching details for %s: %s", source_id, ex)
        return None

    entity = _map_details_to_food_entity(details)
    db.add(entity)
    try:
        db.commit()
    except Exception:
        db.rollback()
        # race or conflict → try read again
        entity = (
            db.query(Food)
            .filter(Food.source == source, Food.source_id == source_id)
            .first()
        )
    return entity


def search_foods(db: Session, query: str, page: int = 1, page_size: int = 10) -> List[nutrition_schemas.FoodHit]:
    q = (query or "").strip()
    if not q:
        return []

    size = min(max(page_size or 10, 1), MAX_PAGE_SIZE)
    page = max(page or 1, 1)
    offset = (page - 1) * size

    # Local search with simple autocomplete ordering
    prefix = f"{q.lower()}%"
    local_q = (
        db.query(Food)
        .filter(Food.name.ilike(f"%{q}%"))
        .order_by(
            case((func.lower(Food.name).like(prefix), 0), else_=1),
            func.length(Food.name),
            Food.name,
        )
    )
    local_count = local_q.count()

    # If local cache insufficient to cover requested page, try external fill
    if local_count < (offset + size):
        try:
            adapter = get_food_source_adapter()
        except UnsupportedFoodSourceError as e:
            logger.info("No adapter available: %s", e)
            adapter = None

        if adapter is not None:
            need = (offset + size) - local_count
            # fetch a bit more than needed, within 25 max
            fetch_size = min(MAX_PAGE_SIZE, max(need, size))
            try:
                logger.info("Calling FDC search for '%s' size=%d", q, fetch_size)
                hits = adapter.search(q, page=1, page_size=fetch_size)
                for h in hits:
                    # Only FDC supported for now
                    if h.source != "fdc":
                        continue
                    _ensure_food_from_source(db, FoodSource.fdc, h.source_id)
            except requests.exceptions.HTTPError as he:
                if getattr(he.response, "status_code", None) == 429:
                    logger.info("FDC 429 rate-limited. Serving cache-only for '%s'", q)
                else:
                    logger.warning("FDC search HTTP error for '%s': %s", q, he)
            except requests.exceptions.RequestException as re:
                logger.warning("FDC search request failed for '%s': %s", q, re)
            except Exception as ex:
                logger.exception("Unexpected error on FDC search for '%s': %s", q, ex)

    # Re-query for the requested page after potential fill
    rows: List[Food] = local_q.offset(offset).limit(size).all()
    return [nutrition_schemas.FoodHit.from_orm(r) for r in rows]


def get_food(db: Session, food_id: str) -> Optional[nutrition_schemas.FoodDetails]:
    row: Food | None = db.query(Food).filter(Food.id == food_id).first()
    if not row:
        return None
    return nutrition_schemas.FoodDetails.from_orm(row)
