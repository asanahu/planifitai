"""
Funciones para persistir planes nutricionales generados por IA en la base de datos.
"""

from datetime import datetime, date, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.nutrition import models, schemas, crud
from app.nutrition.models import TargetSource
import logging

logger = logging.getLogger(__name__)


def persist_nutrition_plan(
    db: Session,
    user_id: int,
    plan_data: Dict[str, Any],
    targets: Dict[str, float]
) -> Dict[str, Any]:
    """
    Persiste un plan nutricional generado por IA en la base de datos.
    
    Args:
        db: Sesión de base de datos
        user_id: ID del usuario
        plan_data: Datos del plan generado por IA
        targets: Objetivos nutricionales
        
    Returns:
        Diccionario con información sobre la persistencia
    """
    
    meals_created = 0
    targets_created = 0
    errors = []
    
    try:
        # Fecha base (hoy) por defecto
        base_date = date.today()

        logger.info(f"Persistiendo plan para usuario {user_id} desde fecha {base_date}")

        # 1) Construir objetivos diarios a partir de targets globales
        daily_targets = {
            "calories_target": int(targets.get("kcal") or targets.get("calories") or 2000),
            "protein_g_target": float(targets.get("protein_g") or targets.get("protein") or 100),
            "carbs_g_target": float(targets.get("carbs_g") or targets.get("carbs") or 250),
            "fat_g_target": float(targets.get("fat_g") or targets.get("fat") or 70),
        }

        # Helpers de mapeo
        def _map_meal_type(raw: str) -> str:
            v = (raw or "").strip().lower()
            if v in {"breakfast", "desayuno"}:
                return "breakfast"
            if v in {"lunch", "almuerzo", "comida"}:
                return "lunch"
            if v in {"dinner", "cena"}:
                return "dinner"
            if v in {"snack", "merienda"}:
                return "snack"
            return "other"

        def _map_unit(raw: str | None) -> str:
            if not raw:
                return "g"
            v = raw.strip().lower()
            if v in {"g", "gramo", "gramos"}:
                return "g"
            if v in {"ml", "mililitro", "mililitros"}:
                return "ml"
            if v in {"unidad", "unit", "piece", "pieza", "cup", "taza"}:
                return "unit"
            return v

        def _get_number(d: dict, *keys: str, default: float = 0.0) -> float:
            for k in keys:
                if k in d and d[k] is not None:
                    try:
                        return float(d[k])
                    except Exception:
                        continue
            return float(default)

        # 2) Procesar cada día del plan
        for day_index, day_data in enumerate(plan_data.get("days", [])):
            # Usar fecha provista en el plan si existe
            current_date = None
            try:
                if isinstance(day_data.get("date"), str):
                    current_date = date.fromisoformat(day_data["date"])  # YYYY-MM-DD
            except Exception:
                current_date = None
            if current_date is None:
                current_date = base_date + timedelta(days=day_index)

            try:
                # upsert de targets diarios
                crud.upsert_target(
                    db=db,
                    user_id=user_id,
                    day=current_date,
                    data=daily_targets,
                    source=TargetSource.auto,
                )
                targets_created += 1

                # Procesar comidas
                for meal_data in day_data.get("meals", []):
                    try:
                        meal_type = _map_meal_type(meal_data.get("type", ""))

                        meal_items: List[schemas.MealItemCreate] = []
                        for item in meal_data.get("items", []) or []:
                            serving_qty = _get_number(item, "qty", "quantity", "amount", default=100)
                            calories = _get_number(item, "kcal", "calories", "calorias", default=0)
                            protein = _get_number(item, "protein_g", "protein", "proteina", default=0)
                            carbs = _get_number(item, "carbs_g", "carbs", "carbohydrates", "carbohidratos", default=0)
                            fat = _get_number(item, "fat_g", "fat", "grasas", default=0)
                            fiber = _get_number(item, "fiber_g", "fiber", default=0) if (item.get("fiber_g") or item.get("fiber")) else None
                            sugar = _get_number(item, "sugar_g", "sugar", default=0) if (item.get("sugar_g") or item.get("sugar")) else None
                            sodium = _get_number(item, "sodium_mg", "sodium", default=0) if (item.get("sodium_mg") or item.get("sodium")) else None

                            meal_item = schemas.MealItemCreate(
                                food_id=None,
                                food_name=item.get("name", "Alimento generado por IA"),
                                serving_qty=serving_qty,
                                serving_unit=_map_unit(item.get("unit")),
                                calories_kcal=calories,
                                protein_g=protein,
                                carbs_g=carbs,
                                fat_g=fat,
                                fiber_g=fiber,
                                sugar_g=sugar,
                                sodium_mg=sodium,
                            )
                            meal_items.append(meal_item)

                        if meal_items:
                            meal_create = schemas.MealCreate(
                                date=current_date,
                                meal_type=meal_type,
                                name=meal_data.get("name", f"Comida IA - {meal_type.title()}"),
                                notes="Generado por IA - Plan 14 días",
                                items=meal_items,
                            )
                            crud.create_meal(db=db, user_id=user_id, payload=meal_create)
                            meals_created += 1

                    except Exception as meal_error:
                        error_msg = f"Error creando comida día {day_index + 1}: {str(meal_error)}"
                        logger.error(error_msg)
                        errors.append(error_msg)

            except Exception as day_error:
                error_msg = f"Error procesando día {day_index + 1}: {str(day_error)}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Commit final
        db.commit()

        result = {
            "success": True,
            "meals_created": meals_created,
            "targets_created": targets_created,
            "errors": errors,
            "message": f"Plan persistido: {meals_created} comidas, {targets_created} objetivos",
        }

        logger.info(f"Plan persistido exitosamente: {result}")
        return result

    except Exception as e:
        db.rollback()
        error_msg = f"Error crítico persistiendo plan: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "meals_created": 0,
            "targets_created": 0,
            "errors": [error_msg],
            "message": "Error persistiendo plan en base de datos",
        }


def clean_existing_ai_meals(db: Session, user_id: int, days_ahead: int = 14):
    """
    Limpia comidas generadas por IA anteriormente para evitar duplicados.
    
    Args:
        db: Sesión de base de datos
        user_id: ID del usuario
        days_ahead: Días hacia adelante a limpiar
    """
    
    try:
        base_date = date.today()
        end_date = base_date + timedelta(days=days_ahead)
        
        # Buscar comidas con notas que indiquen que fueron generadas por IA
        ai_meals = db.query(models.NutritionMeal).filter(
            models.NutritionMeal.user_id == user_id,
            models.NutritionMeal.date >= base_date,
            models.NutritionMeal.date <= end_date,
            models.NutritionMeal.notes.ilike("%Generado por IA%")
        ).all()
        
        deleted_count = len(ai_meals)
        
        for meal in ai_meals:
            db.delete(meal)
        
        db.commit()
        
        logger.info(f"Limpiadas {deleted_count} comidas IA anteriores para usuario {user_id}")
        return {"deleted": deleted_count}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error limpiando comidas IA: {str(e)}")
        return {"deleted": 0, "error": str(e)}
