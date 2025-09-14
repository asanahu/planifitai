"""Celery tasks for asynchronous nutrition plan generation."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Dict, Any

from celery import current_task
from sqlalchemy.orm import Session

from app.background.celery_app import celery_app
from app.ai.services import generate_nutrition_plan_optimized, generate_nutrition_plan
from app.ai import plan_persistence
from app.ai.cache import generate_nutrition_plan_with_cache
from app.ai import schemas
from app.dependencies import get_db
from app.auth.deps import UserContext


@celery_app.task(
    bind=True, 
    name="generate_nutrition_plan_async",
    time_limit=300,  # 5 minutos
    soft_time_limit=240  # 4 minutos
)
def generate_nutrition_plan_task(
    self, 
    user_id: int, 
    request_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Genera plan nutricional de 2 semanas en background.
    
    Args:
        user_id: ID del usuario
        request_data: Datos de la petición (days, preferences, etc.)
    
    Returns:
        Dict con el plan generado y metadatos
    """
    try:
        # Actualizar progreso inicial
        self.update_state(
            state='PROGRESS', 
            meta={
                'step': 'analyzing_profile', 
                'progress': 10,
                'message': 'Analizando perfil del usuario...'
            }
        )
        
        # Crear contexto de usuario simulado para la tarea
        user_context = UserContext(id=user_id, email="", is_active=True)
        
        # Crear esquema de petición
        nutrition_request = schemas.NutritionPlanRequest(**request_data)
        
        # Obtener sesión de base de datos
        db = next(get_db())
        
        try:
            # Actualizar progreso - generando plan
            self.update_state(
                state='PROGRESS', 
                meta={
                    'step': 'generating_plan', 
                    'progress': 30,
                    'message': 'Generando plan nutricional personalizado...'
                }
            )
            
            # Generar el plan nutricional
            plan = generate_nutrition_plan(user_context, nutrition_request, db)
            
            # Actualizar progreso - finalizando
            self.update_state(
                state='PROGRESS', 
                meta={
                    'step': 'finalizing', 
                    'progress': 90,
                    'message': 'Finalizando plan nutricional...'
                }
            )
            
            # Convertir a dict para serialización
            plan_dict = plan.model_dump()

            # Persistir automáticamente (limpiar previas y guardar nuevas)
            try:
                plan_persistence.clean_existing_ai_meals(db, user_id, days_ahead=14)
                persist_result = plan_persistence.persist_nutrition_plan(
                    db=db,
                    user_id=user_id,
                    plan_data=plan_dict,
                    targets=plan_dict.get('targets', {})
                )
            except Exception as _:
                persist_result = {"success": False}
            
            # Actualizar progreso - completado
            self.update_state(
                state='PROGRESS', 
                meta={
                    'step': 'completed', 
                    'progress': 100,
                    'message': 'Plan generado exitosamente'
                }
            )
            
            return {
                'status': 'SUCCESS',
                'plan': plan_dict,
                'generated_at': datetime.utcnow().isoformat(),
                'days_generated': len(plan_dict.get('days', [])),
                'targets': plan_dict.get('targets', {}),
                'persist': persist_result,
            }
            
        finally:
            db.close()
            
    except Exception as exc:
        # Log del error
        error_msg = str(exc)
        self.update_state(
            state='FAILURE', 
            meta={
                'error': error_msg,
                'error_type': type(exc).__name__,
                'failed_at': datetime.utcnow().isoformat()
            }
        )
        raise


@celery_app.task(
    bind=True, 
    name="generate_nutrition_plan_14_days",
    time_limit=300,  # 5 minutos
    soft_time_limit=240  # 4 minutos
)
def generate_nutrition_plan_14_days_task(
    self,
    user_id: int,
    request_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Genera plan nutricional optimizado de 14 días completos.
    
    Esta tarea genera un plan completo de 2 semanas usando una estrategia
    optimizada: genera 7 días base + variaciones inteligentes.
    """
    try:
        # Actualizar progreso inicial
        self.update_state(
            state='PROGRESS', 
            meta={
                'step': 'analyzing_profile', 
                'progress': 5,
                'message': 'Analizando perfil del usuario...'
            }
        )
        
        # Crear contexto de usuario
        user_context = UserContext(id=user_id, email="", is_active=True)
        
        # Obtener sesión de base de datos
        db = next(get_db())
        
        try:
            # Paso 1: Generar plan base de 7 días
            self.update_state(
                state='PROGRESS', 
                meta={
                    'step': 'generating_base_week', 
                    'progress': 25,
                    'message': 'Generando plan base de 7 días...'
                }
            )
            
            base_request = schemas.NutritionPlanRequest(
                days=7,
                preferences=request_data.get('preferences', {})
            )
            
            base_plan = generate_nutrition_plan(user_context, base_request, db)
            
            # Paso 2: Crear variaciones inteligentes para la segunda semana
            self.update_state(
                state='PROGRESS', 
                meta={
                    'step': 'creating_variations', 
                    'progress': 60,
                    'message': 'Creando variaciones para la segunda semana...'
                }
            )
            
            week2_plan = create_intelligent_variations(base_plan, user_context, db)
            
            # Paso 3: Combinar ambos planes
            self.update_state(
                state='PROGRESS', 
                meta={
                    'step': 'combining_plans', 
                    'progress': 85,
                    'message': 'Combinando planes de ambas semanas...'
                }
            )
            
            # Combinar días de ambos planes
            combined_days = base_plan.days + week2_plan.days
            
            # Actualizar fechas para la segunda semana
            from datetime import timedelta
            base_date = datetime.fromisoformat(base_plan.days[0].date)
            
            for i, day in enumerate(week2_plan.days):
                new_date = base_date + timedelta(days=7 + i)
                day.date = new_date.isoformat()
            
            # Crear plan final
            final_plan = schemas.NutritionPlan(
                days=combined_days,
                targets=base_plan.targets
            )

            # Persistir automáticamente el plan combinado
            try:
                final_dict = final_plan.model_dump()
                plan_persistence.clean_existing_ai_meals(db, user_id, days_ahead=14)
                persist_result = plan_persistence.persist_nutrition_plan(
                    db=db,
                    user_id=user_id,
                    plan_data=final_dict,
                    targets=final_dict.get('targets', {})
                )
            except Exception as _:
                persist_result = {"success": False}
            
            # Actualizar progreso - completado
            self.update_state(
                state='PROGRESS', 
                meta={
                    'step': 'completed', 
                    'progress': 100,
                    'message': 'Plan de 14 días generado exitosamente'
                }
            )
            
            return {
                'status': 'SUCCESS',
                'plan': final_plan.model_dump(),
                'generated_at': datetime.utcnow().isoformat(),
                'days_generated': len(combined_days),
                'strategy': 'base_week_plus_variations',
                'targets': base_plan.targets,
                'persist': persist_result,
            }
            
        finally:
            db.close()
            
    except Exception as exc:
        error_msg = str(exc)
        self.update_state(
            state='FAILURE', 
            meta={
                'error': error_msg,
                'error_type': type(exc).__name__,
                'failed_at': datetime.utcnow().isoformat()
            }
        )
        raise


@celery_app.task(
    bind=True, 
    name="generate_nutrition_plan_test",
    time_limit=60,  # 1 minuto para pruebas
    soft_time_limit=45  # 45 segundos
)
def generate_nutrition_plan_test_task(
    self, 
    user_id: int, 
    request_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Tarea de prueba rápida para generar un plan de 1 día.
    """
    try:
        # Actualizar progreso inicial
        self.update_state(
            state='PROGRESS', 
            meta={
                'step': 'generating_test_plan', 
                'progress': 50,
                'message': 'Generando plan de prueba...'
            }
        )
        
        # Crear contexto de usuario simulado
        user_context = UserContext(id=user_id, email="", is_active=True)
        
        # Crear esquema de petición para 1 día
        nutrition_request = schemas.NutritionPlanRequest(days=1, preferences={})
        
        # Obtener sesión de base de datos
        db = next(get_db())
        
        try:
            # Generar el plan nutricional usando modo simulado para evitar rate limits
            plan = generate_nutrition_plan_optimized(user_context, nutrition_request, db)
            
            # Actualizar progreso - completado
            self.update_state(
                state='PROGRESS', 
                meta={
                    'step': 'completed', 
                    'progress': 100,
                    'message': 'Plan de prueba generado exitosamente'
                }
            )
            
            # Convertir a dict para serialización
            plan_dict = plan.model_dump()
            
            return {
                'status': 'SUCCESS',
                'plan': plan_dict,
                'generated_at': datetime.utcnow().isoformat(),
                'days_generated': len(plan_dict.get('days', [])),
                'targets': plan_dict.get('targets', {}),
                'test_mode': True
            }
            
        finally:
            db.close()
            
    except Exception as exc:
        # Log del error
        error_msg = str(exc)
        self.update_state(
            state='FAILURE', 
            meta={
                'error': error_msg,
                'error_type': type(exc).__name__,
                'failed_at': datetime.utcnow().isoformat()
            }
        )
        raise


def create_intelligent_variations(
    base_plan: schemas.NutritionPlan, 
    user_context: UserContext, 
    db: Session
) -> schemas.NutritionPlan:
    """
    Crea variaciones inteligentes del plan base para la segunda semana.
    
    Esta función toma el plan de 7 días y crea variaciones manteniendo
    el balance nutricional pero cambiando ingredientes y preparaciones.
    """
    from app.ai_client import get_ai_client
    from app.ai import prompt_library
    
    # Crear variaciones usando IA
    client = get_ai_client()
    
    variation_prompt = f"""
    Basándote en este plan nutricional de 7 días, crea variaciones inteligentes para los días 8-14:

    Plan base: {base_plan.model_dump_json()}

    INSTRUCCIONES ESPECÍFICAS:
    1. Mantén EXACTAMENTE los mismos objetivos nutricionales (targets)
    2. Varía ingredientes pero mantén el balance nutricional
    3. Introduce nuevos alimentos saludables españoles
    4. Considera la variedad para evitar monotonía
    5. Mantén horarios de comidas consistentes
    6. Usa alimentos de temporada cuando sea posible
    7. Incluye preparaciones diferentes (ej: pollo a la plancha vs pollo al horno)

    EJEMPLOS DE VARIACIONES:
    - Pollo → Pavo, Salmón, Atún
    - Arroz integral → Quinoa, Bulgur, Pasta integral
    - Brócoli → Espinacas, Coliflor, Pimientos
    - Aceite de oliva → Aguacate, Frutos secos

    Responde SOLO con JSON válido siguiendo el mismo esquema del plan base.
    Genera exactamente 7 días adicionales (días 8-14).
    """
    
    try:
        resp = client.chat(
            user_context.id,
            [
                {"role": "system", "content": prompt_library.NUTRITION_PLAN_SYSTEM_PROMPT},
                {"role": "user", "content": variation_prompt},
            ],
        )
        
        # Parsear respuesta JSON
        from app.ai.services import _parse_json_payload
        data = _parse_json_payload(resp.get("reply", ""))
        
        # Validar y crear esquema
        return schemas.NutritionPlan.model_validate(data)
        
    except Exception as exc:
        # Fallback: crear variaciones simples programáticamente
        return create_simple_variations(base_plan)


def create_simple_variations(base_plan: schemas.NutritionPlan) -> schemas.NutritionPlan:
    """
    Crea variaciones simples programáticamente como fallback.
    """
    # Mapeo de variaciones simples
    variations_map = {
        "pollo": "pavo",
        "arroz integral": "quinoa",
        "brócoli": "espinacas",
        "aceite de oliva": "aguacate",
        "yogur griego": "queso fresco",
        "huevos": "claras de huevo",
        "pasta integral": "arroz salvaje",
        "salmón": "atún",
        "avena": "mijo",
        "almendras": "nueces"
    }
    
    # Crear variaciones de los días base
    varied_days = []
    for day in base_plan.days:
        varied_meals = []
        
        for meal in day.meals:
            varied_items = []
            
            for item in meal.items:
                # Crear variación del nombre del alimento
                varied_name = item.name
                for original, variation in variations_map.items():
                    if original.lower() in item.name.lower():
                        varied_name = item.name.lower().replace(original.lower(), variation)
                        break
                
                # Crear nuevo item con nombre variado
                from app.ai.schemas import MealItem
                varied_item = MealItem(
                    name=varied_name,
                    qty=item.qty,
                    unit=item.unit,
                    kcal=item.kcal,
                    protein_g=item.protein_g,
                    carbs_g=item.carbs_g,
                    fat_g=item.fat_g
                )
                varied_items.append(varied_item)
            
            # Crear nueva comida
            from app.ai.schemas import Meal
            varied_meal = Meal(
                type=meal.type,
                items=varied_items,
                meal_kcal=meal.meal_kcal
            )
            varied_meals.append(varied_meal)
        
        # Crear nuevo día
        from app.ai.schemas import NutritionDayPlan
        varied_day = NutritionDayPlan(
            date=day.date,
            meals=varied_meals,
            totals=day.totals
        )
        varied_days.append(varied_day)
    
    return schemas.NutritionPlan(
        days=varied_days,
        targets=base_plan.targets
    )
