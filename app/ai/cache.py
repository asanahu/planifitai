"""Sistema de cache inteligente para planes nutricionales."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.ai import schemas
from app.auth.deps import UserContext


class NutritionPlanCache:
    """Cache inteligente para planes nutricionales."""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = timedelta(hours=24)  # Cache válido por 24 horas
    
    def _generate_cache_key(self, user_context: UserContext, request: schemas.NutritionPlanRequest) -> str:
        """Genera una clave única para el cache basada en el usuario y la petición."""
        # Crear hash del perfil del usuario y la petición
        cache_data = {
            "user_id": user_context.id,
            "days": request.days,
            "preferences": request.preferences or {},
        }
        
        # Convertir a string JSON y crear hash
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def get(self, user_context: UserContext, request: schemas.NutritionPlanRequest) -> Optional[schemas.NutritionPlan]:
        """Obtiene un plan del cache si existe y es válido."""
        cache_key = self._generate_cache_key(user_context, request)
        
        if cache_key not in self._cache:
            return None
        
        cache_entry = self._cache[cache_key]
        
        # Verificar si el cache ha expirado
        cached_at = datetime.fromisoformat(cache_entry["cached_at"])
        if datetime.now() - cached_at > self._cache_ttl:
            del self._cache[cache_key]
            return None
        
        # Retornar el plan desde el cache
        return schemas.NutritionPlan.model_validate(cache_entry["plan"])
    
    def set(self, user_context: UserContext, request: schemas.NutritionPlanRequest, plan: schemas.NutritionPlan):
        """Almacena un plan en el cache."""
        cache_key = self._generate_cache_key(user_context, request)
        
        self._cache[cache_key] = {
            "plan": plan.model_dump(),
            "cached_at": datetime.now().isoformat(),
            "user_id": user_context.id,
            "days": request.days
        }
    
    def clear_user_cache(self, user_id: int):
        """Limpia el cache de un usuario específico."""
        keys_to_remove = []
        for key, entry in self._cache.items():
            if entry.get("user_id") == user_id:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._cache[key]
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del cache."""
        return {
            "total_entries": len(self._cache),
            "cache_ttl_hours": self._cache_ttl.total_seconds() / 3600,
            "entries": [
                {
                    "user_id": entry["user_id"],
                    "days": entry["days"],
                    "cached_at": entry["cached_at"]
                }
                for entry in self._cache.values()
            ]
        }


# Instancia global del cache
_nutrition_cache = NutritionPlanCache()


def get_nutrition_cache() -> NutritionPlanCache:
    """Obtiene la instancia global del cache."""
    return _nutrition_cache


def generate_nutrition_plan_with_cache(
    user: UserContext,
    req: schemas.NutritionPlanRequest,
    db: Session,
    *,
    simulate: bool = False,
) -> schemas.NutritionPlan:
    """Genera un plan nutricional con cache inteligente."""
    from app.ai.services import generate_nutrition_plan_optimized
    
    # Si es modo simulado, no usar cache
    if simulate:
        return generate_nutrition_plan_optimized(user, req, db, simulate=True)
    
    # Intentar obtener del cache primero
    cache = get_nutrition_cache()
    cached_plan = cache.get(user, req)
    
    if cached_plan:
        return cached_plan
    
    # Si no está en cache, generar nuevo plan
    plan = generate_nutrition_plan_optimized(user, req, db, simulate=False)
    
    # Almacenar en cache
    cache.set(user, req, plan)
    
    return plan
