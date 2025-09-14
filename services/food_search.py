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
        logger.info("Fetching %s details for source_id=%s", source.value, source_id)
        details: SourceFoodDetails = adapter.get_details(source_id)
    except requests.exceptions.HTTPError as he:
        if getattr(he.response, "status_code", None) == 429:
            logger.info("%s 429 rate-limited. Skipping external fetch for %s", source.value, source_id)
            return None
        logger.warning("%s details HTTP error for %s: %s", source.value, source_id, he)
        return None
    except requests.exceptions.RequestException as re:
        logger.warning("%s details request failed for %s: %s", source.value, source_id, re)
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


def get_food(db: Session, food_id: str) -> Optional[nutrition_schemas.FoodDetails]:
    """
    Obtiene los detalles de un alimento específico por su ID.
    
    Args:
        db: Sesión de base de datos
        food_id: ID del alimento
    
    Returns:
        Detalles del alimento o None si no se encuentra
    """
    try:
        # Buscar en la base de datos local primero
        food = db.query(Food).filter(Food.id == food_id).first()
        if food:
            return nutrition_schemas.FoodDetails.from_orm(food)
        
        # Si no se encuentra localmente, intentar obtenerlo de la fuente externa
        # Esto es útil si el alimento existe en la fuente pero no se ha cacheado localmente
        logger.info("Food %s not found locally, attempting external fetch", food_id)
        
        # Intentar obtener de la fuente externa
        try:
            adapter = get_food_source_adapter()
            details = adapter.get_details(food_id)
            
            # Guardar en la base de datos local para futuras consultas
            entity = _map_details_to_food_entity(details)
            db.add(entity)
            db.commit()
            
            return nutrition_schemas.FoodDetails.from_orm(entity)
            
        except UnsupportedFoodSourceError as e:
            logger.warning("Food source unsupported for %s: %s", food_id, e)
            return None
        except requests.exceptions.HTTPError as he:
            if getattr(he.response, "status_code", None) == 404:
                logger.info("Food %s not found in external source", food_id)
                return None
            elif getattr(he.response, "status_code", None) == 429:
                logger.info("External source rate-limited for %s", food_id)
                return None
            else:
                logger.warning("External source HTTP error for %s: %s", food_id, he)
                return None
        except requests.exceptions.RequestException as re:
            logger.warning("External source request failed for %s: %s", food_id, re)
            return None
        except Exception as ex:
            logger.exception("Unexpected error fetching food %s: %s", food_id, ex)
            return None
            
    except Exception as ex:
        logger.exception("Unexpected error in get_food for %s: %s", food_id, ex)
        return None


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
    # But only if we have very few results (less than 5) to avoid excessive API calls
    if local_count < (offset + size) and local_count < 5:
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
                logger.info("Calling %s search for '%s' size=%d", adapter.__class__.__name__, q, fetch_size)
                hits = adapter.search(q, page=1, page_size=fetch_size)
                for h in hits:
                    # Map source string to FoodSource enum
                    source_enum = FoodSource(h.source)
                    _ensure_food_from_source(db, source_enum, h.source_id)
            except requests.exceptions.HTTPError as he:
                if getattr(he.response, "status_code", None) == 429:
                    logger.info("%s 429 rate-limited. Serving cache-only for '%s'", adapter.__class__.__name__, q)
                else:
                    logger.warning("%s search HTTP error for '%s': %s", adapter.__class__.__name__, q, he)
            except requests.exceptions.RequestException as re:
                logger.warning("%s search request failed for '%s': %s", adapter.__class__.__name__, q, re)
            except Exception as ex:
                logger.exception("Unexpected error on %s search for '%s': %s", adapter.__class__.__name__, q, ex)

    # Re-query for the requested page after potential fill
    rows: List[Food] = local_q.offset(offset).limit(size).all()
    return [nutrition_schemas.FoodDetails.from_orm(r) for r in rows]


def search_foods_smart(
    db: Session, 
    query: str, 
    page: int = 1, 
    page_size: int = 10,
    user_id: int = 0,
    context: Optional[str] = None,
    simulate_ai: bool = False
) -> List[nutrition_schemas.FoodHit]:
    """
    Búsqueda inteligente de alimentos que usa IA para mejorar los resultados.
    
    Args:
        db: Sesión de base de datos
        query: Consulta de búsqueda original
        page: Número de página
        page_size: Tamaño de página
        user_id: ID del usuario (para personalización con IA)
        context: Contexto adicional (ej: "desayuno", "alto en proteína")
        simulate_ai: Si simular la IA (para testing)
    
    Returns:
        Lista de resultados de alimentos
    """
    q = (query or "").strip()
    if not q:
        return []
    
    # Si tenemos IA disponible y un usuario, intentar mejorar la búsqueda
    enhanced_terms = [q]  # Fallback a la consulta original
    
    if user_id > 0 and not simulate_ai:
        try:
            from app.ai.smart_food_search import get_enhanced_search_terms
            from app.auth.deps import UserContext
            
            # Crear contexto de usuario mínimo para la IA
            user_context = UserContext(id=user_id, email="", username="")
            enhanced_terms = get_enhanced_search_terms(
                user_context, q, context, simulate=False
            )
            logger.info(f"Términos de búsqueda mejorados para '{q}': {enhanced_terms}")
        except Exception as e:
            logger.warning(f"No se pudo mejorar la búsqueda con IA: {e}")
            enhanced_terms = [q]
    
    # Buscar con todos los términos mejorados
    all_results = []
    seen_ids = set()
    
    for term in enhanced_terms:
        if not term.strip():
            continue
            
        # Usar la función de búsqueda existente para cada término
        term_results = search_foods(db, term, page=1, page_size=page_size)
        
        # Agregar resultados únicos
        for result in term_results:
            if result.id not in seen_ids:
                all_results.append(result)
                seen_ids.add(result.id)
    
    # Ordenar por relevancia (coincidencias exactas primero)
    def relevance_score(hit: nutrition_schemas.FoodHit) -> int:
        name_lower = hit.name.lower()
        query_lower = q.lower()
        
        if name_lower.startswith(query_lower):
            return 0  # Máxima relevancia
        elif query_lower in name_lower:
            return 1  # Alta relevancia
        else:
            return 2  # Baja relevancia
    
    all_results.sort(key=relevance_score)
    
    # Paginar los resultados
    size = min(max(page_size or 10, 1), MAX_PAGE_SIZE)
    page = max(page or 1, 1)
    offset = (page - 1) * size
    
    return all_results[offset:offset + size]


