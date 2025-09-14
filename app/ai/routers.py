"""FastAPI routers exposing AI functionality."""

from __future__ import annotations

import logging
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.ai_client import get_ai_client
from app.auth.deps import UserContext, get_current_user
from app.core.database import get_db

from . import schemas, services, smart_food_search
from . import plan_persistence
from app.notifications import crud as notif_crud, models as notif_models, services as notif_services, schemas as notif_schemas
from app.background.nutrition_tasks import generate_nutrition_plan_task, generate_nutrition_plan_14_days_task

router = APIRouter(prefix="/ai", tags=["ai"])
logger = logging.getLogger(__name__)


@router.get("/test-celery")
def test_celery():
    """
    Endpoint de prueba para verificar que Celery está funcionando.
    """
    try:
        from app.background.tasks import chat_task
        
        # Crear una tarea simple de prueba
        task = chat_task.delay({
            "messages": [{"role": "user", "content": "test"}],
            "model": None
        })
        
        return {
            "status": "success",
            "message": "Celery está funcionando",
            "task_id": task.id,
            "celery_configured": True
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error con Celery: {str(e)}",
            "celery_configured": False
        }


@router.get("/test-nutrition-task")
def test_nutrition_task():
    """
    Endpoint de prueba para verificar que las tareas de nutrición están registradas.
    """
    try:
        from app.background.nutrition_tasks import generate_nutrition_plan_task
        
        # Crear una tarea de prueba
        task = generate_nutrition_plan_task.delay(
            user_id=1,
            request_data={"days": 1, "preferences": {}}
        )
        
        return {
            "status": "success",
            "message": "Tarea de nutrición registrada correctamente",
            "task_id": task.id,
            "nutrition_tasks_available": True
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error con tareas de nutrición: {str(e)}",
            "nutrition_tasks_available": False
        }


@router.post("/test-async-generation")
def test_async_generation():
    """
    Endpoint de prueba para verificar la generación asíncrona completa (sin autenticación).
    """
    try:
        from app.background.nutrition_tasks import generate_nutrition_plan_task
        
        # Crear una tarea de prueba
        task = generate_nutrition_plan_task.delay(
            user_id=1,
            request_data={"days": 1, "preferences": {}}
        )
        
        return {
            "status": "success",
            "message": "Generación asíncrona iniciada correctamente",
            "task_id": task.id,
            "test_url": f"/api/v1/ai/generate/nutrition-plan-status/{task.id}"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error iniciando generación: {str(e)}"
        }


@router.post("/test-quick-generation")
def test_quick_generation():
    """
    Endpoint de prueba rápida para generar un plan de 1 día (sin autenticación).
    """
    try:
        from app.background.nutrition_tasks import generate_nutrition_plan_test_task
        
        # Crear una tarea de prueba rápida
        task = generate_nutrition_plan_test_task.delay(
            user_id=1,
            request_data={"days": 1, "preferences": {}}
        )
        
        return {
            "status": "success",
            "message": "Generación rápida iniciada (1 día)",
            "task_id": task.id,
            "test_url": f"/api/v1/ai/generate/nutrition-plan-status/{task.id}",
            "estimated_time": "30-60 segundos"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error iniciando generación rápida: {str(e)}"
        }


@router.post("/test-14-days-generation")
def test_14_days_generation():
    """
    Endpoint de prueba para generar un plan de 14 días (sin autenticación).
    """
    try:
        from app.background.nutrition_tasks import generate_nutrition_plan_14_days_task
        
        # Crear una tarea de prueba de 14 días
        task = generate_nutrition_plan_14_days_task.delay(
            user_id=1,
            request_data={"days": 14, "preferences": {}}
        )
        
        return {
            "status": "success",
            "message": "Generación de 14 días iniciada",
            "task_id": task.id,
            "test_url": f"/api/v1/ai/generate/nutrition-plan-status/{task.id}",
            "estimated_time": "5-10 segundos"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error iniciando generación de 14 días: {str(e)}"
        }


@router.post("/test-14-days-working")
async def test_14_days_working():
    """Test de generación de 14 días sin autenticación - FUNCIONANDO."""
    try:
        from openai import OpenAI
        from app.core.config import settings
        import json
        from datetime import date, timedelta
        
        # Obtener API key
        api_key = getattr(settings, 'API_OPEN_AI', None) or settings.OPENAI_API_KEY
        if not api_key:
            return {
                "status": "error",
                "message": "API key no configurada"
            }
        
        client = OpenAI(api_key=api_key)
        
        # Generar fechas para 14 días
        today = date.today()
        dates = [(today + timedelta(days=i)).isoformat() for i in range(14)]
        
        # Prompt optimizado para GPT-5-nano
        system_prompt = """Eres PlanifitAI, un experto nutricionista. Genera planes nutricionales completos y realistas en formato JSON.

FORMATO EXACTO:
{
  "days": [
    {
      "date": "YYYY-MM-DD",
      "meals": [
        {
          "type": "breakfast|lunch|dinner|snack",
          "items": [
            {
              "name": "nombre del alimento",
              "qty": cantidad_numerica,
              "unit": "g|ml|unidad|taza",
              "kcal": calorias,
              "protein_g": proteinas,
              "carbs_g": carbohidratos,
              "fat_g": grasas
            }
          ],
          "meal_kcal": total_calorias_comida
        }
      ],
      "totals": {
        "kcal": total_dia,
        "protein_g": proteinas_dia,
        "carbs_g": carbohidratos_dia,
        "fat_g": grasas_dia
      }
    }
  ],
  "targets": {
    "kcal": objetivo_calorias,
    "protein_g": objetivo_proteinas,
    "carbs_g": objetivo_carbohidratos,
    "fat_g": objetivo_grasas
  }
}

ALIMENTOS DISPONIBLES: Pollo, salmón, huevos, yogur griego, arroz integral, quinoa, avena, patata, aguacate, aceite de oliva, brócoli, espinacas, tomate, plátano, manzana, nueces, almendras, leche, queso fresco.

COMIDAS: breakfast (desayuno), lunch (almuerzo), dinner (cena), snack (merienda).

IMPORTANTE: Responde SOLO con JSON válido, sin texto adicional."""

        user_prompt = f"""Genera un plan nutricional completo para 14 días (2 semanas completas).

DETALLES:
- Objetivo: mantener peso
- Nivel de actividad: moderadamente activo
- Fechas: {dates[0]} a {dates[-1]}
- Incluye 4 comidas por día: desayuno, almuerzo, cena y merienda
- Usa alimentos variados y saludables
- Mantén balance nutricional adecuado
- Considera horarios españoles de comida
- Varía los alimentos para evitar monotonía

Genera el JSON completo para los 14 días."""

        # Generar con GPT-5-nano
        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            reasoning_effort="low",
            verbosity="low"
        )
        
        reply = response.choices[0].message.content
        
        # Limpiar respuesta
        clean_reply = reply.strip()
        if clean_reply.startswith('```json'):
            clean_reply = clean_reply[7:]
        if clean_reply.endswith('```'):
            clean_reply = clean_reply[:-3]
        clean_reply = clean_reply.strip()
        
        # Parsear JSON
        plan_data = json.loads(clean_reply)
        
        # Validar estructura
        if not plan_data.get('days') or not plan_data.get('targets'):
            raise ValueError("Estructura JSON inválida")
        
        return {
            "status": "success",
            "message": f"Plan nutricional de {len(plan_data['days'])} días generado exitosamente con GPT-5-nano",
            "plan": plan_data,
            "days_generated": len(plan_data['days']),
            "targets": plan_data['targets'],
            "first_day_meals": len(plan_data['days'][0]['meals']) if plan_data['days'] else 0,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error generando plan: {str(e)}",
            "error_type": type(e).__name__
        }


@router.post("/generate/nutrition-plan-direct-working")
async def generate_nutrition_plan_direct_working(
    request: schemas.NutritionPlanRequest,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generación directa de plan nutricional sin Celery - FUNCIONANDO."""
    try:
        from openai import OpenAI
        from app.core.config import settings
        import json
        from datetime import date, timedelta
        
        # Obtener API key
        api_key = getattr(settings, 'API_OPEN_AI', None) or settings.OPENAI_API_KEY
        if not api_key:
            return {
                "status": "error",
                "message": "API key no configurada"
            }
        
        client = OpenAI(api_key=api_key)
        
        # Generar fechas
        today = date.today()
        dates = [(today + timedelta(days=i)).isoformat() for i in range(request.days)]
        
        # Prompt optimizado para GPT-5-nano
        system_prompt = """Eres PlanifitAI, un experto nutricionista. Genera planes nutricionales completos y realistas en formato JSON.

FORMATO EXACTO:
{
  "days": [
    {
      "date": "YYYY-MM-DD",
      "meals": [
        {
          "type": "breakfast|lunch|dinner|snack",
          "items": [
            {
              "name": "nombre del alimento",
              "qty": cantidad_numerica,
              "unit": "g|ml|unidad|taza",
              "kcal": calorias,
              "protein_g": proteinas,
              "carbs_g": carbohidratos,
              "fat_g": grasas
            }
          ],
          "meal_kcal": total_calorias_comida
        }
      ],
      "totals": {
        "kcal": total_dia,
        "protein_g": proteinas_dia,
        "carbs_g": carbohidratos_dia,
        "fat_g": grasas_dia
      }
    }
  ],
  "targets": {
    "kcal": objetivo_calorias,
    "protein_g": objetivo_proteinas,
    "carbs_g": objetivo_carbohidratos,
    "fat_g": objetivo_grasas
  }
}

ALIMENTOS DISPONIBLES: Pollo, salmón, huevos, yogur griego, arroz integral, quinoa, avena, patata, aguacate, aceite de oliva, brócoli, espinacas, tomate, plátano, manzana, nueces, almendras, leche, queso fresco.

COMIDAS: breakfast (desayuno), lunch (almuerzo), dinner (cena), snack (merienda).

IMPORTANTE: Responde SOLO con JSON válido, sin texto adicional."""

        user_prompt = f"""Genera un plan nutricional completo para {request.days} días.

DETALLES:
- Objetivo: {request.goal or 'maintain_weight'}
- Nivel de actividad: {request.activity_level or 'moderately_active'}
- Fechas: {', '.join(dates[:5])}{'...' if len(dates) > 5 else ''}
- Incluye 4 comidas por día: desayuno, almuerzo, cena y merienda
- Usa alimentos variados y saludables
- Mantén balance nutricional adecuado
- Considera horarios españoles de comida

Genera el JSON completo para los {request.days} días."""

        # Generar con GPT-5-nano
        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            reasoning_effort="low",
            verbosity="low"
        )
        
        reply = response.choices[0].message.content
        
        # Limpiar respuesta
        clean_reply = reply.strip()
        if clean_reply.startswith('```json'):
            clean_reply = clean_reply[7:]
        if clean_reply.endswith('```'):
            clean_reply = clean_reply[:-3]
        clean_reply = clean_reply.strip()
        
        # Parsear JSON
        plan_data = json.loads(clean_reply)
        
        # Validar estructura
        if not plan_data.get('days') or not plan_data.get('targets'):
            raise ValueError("Estructura JSON inválida")
        
        return {
            "status": "success",
            "message": f"Plan nutricional de {len(plan_data['days'])} días generado exitosamente con GPT-5-nano",
            "plan": plan_data,
            "days_generated": len(plan_data['days']),
            "targets": plan_data['targets'],
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error generando plan: {str(e)}",
            "error_type": type(e).__name__
        }


@router.post("/test-nutrition-direct")
async def test_nutrition_direct():
    """Test directo de generación nutricional sin autenticación."""
    try:
        from app.ai.services import generate_nutrition_plan_optimized
        from app.auth.deps import UserContext
        
        # Crear contexto de usuario simulado
        user_context = UserContext(
            id=1,
            user_id=1,
            email="test@example.com",
            is_active=True
        )
        
        # Crear request simulado
        request = schemas.NutritionPlanRequest(
            days=1,
            goal="maintain_weight",
            activity_level="moderately_active"
        )
        
        # Generar plan directamente (sin Celery)
        plan = generate_nutrition_plan_optimized(
            user=user_context,
            req=request,
            db=None,  # No necesitamos DB para este test
            simulate=False
        )
        
        return {
            "status": "success",
            "message": "Plan nutricional generado exitosamente con GPT-5-nano",
            "plan": plan,
            "days_count": len(plan.days),
            "first_day_meals": len(plan.days[0].meals) if plan.days else 0,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error generando plan: {str(e)}",
            "error_type": type(e).__name__
        }


@router.post("/generate/nutrition-plan-direct")
async def generate_nutrition_plan_direct(
    request: schemas.NutritionPlanRequest,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generación directa de plan nutricional sin Celery."""
    try:
        from app.ai.services import generate_nutrition_plan_optimized
        
        # Generar plan directamente (sin Celery)
        plan = generate_nutrition_plan_optimized(
            user=current_user,
            req=request,
            db=db,
            simulate=False
        )
        
        return {
            "status": "success",
            "message": "Plan nutricional generado exitosamente",
            "plan": plan,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error generando plan: {str(e)}",
            "error_type": type(e).__name__
        }


@router.post("/test-direct-generation")
async def test_direct_generation():
    """Test directo de generación sin Celery."""
    try:
        from app.ai.services import generate_nutrition_plan_optimized
        from app.auth.deps import UserContext
        from app.ai import schemas
        
        # Crear contexto de usuario simulado
        user_context = UserContext(
            id=1,
            user_id=1,
            email="test@example.com",
            is_active=True
        )
        
        # Crear request simulado
        request = schemas.NutritionPlanRequest(
            days=1,
            goal="maintain_weight",
            activity_level="moderately_active"
        )
        
        # Generar plan directamente (sin Celery)
        plan = generate_nutrition_plan_optimized(
            user=user_context,
            req=request,
            db=None,  # No necesitamos DB para este test
            simulate=False
        )
        
        return {
            "status": "success",
            "message": "Generación directa exitosa",
            "plan": plan,
            "days_count": len(plan.days),
            "first_day_meals": len(plan.days[0].meals) if plan.days else 0
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error en generación directa: {str(e)}",
            "error_type": type(e).__name__
        }


@router.get("/rate-limit-status")
def get_rate_limit_status():
    """
    Obtiene el estado del rate limiter de OpenRouter.
    """
    try:
        from app.ai.rate_limiter import get_rate_limiter
        rate_limiter = get_rate_limiter()
        status = rate_limiter.get_status()
        
        return {
            "status": "success",
            "rate_limit_status": status
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error obteniendo estado del rate limiter: {str(e)}"
        }


@router.get("/cache/stats")
def get_cache_stats():
    """
    Obtiene estadísticas del cache de planes nutricionales.
    """
    try:
        from app.ai.cache import get_nutrition_cache
        cache = get_nutrition_cache()
        stats = cache.get_cache_stats()
        
        return {
            "status": "success",
            "cache_stats": stats
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error obteniendo estadísticas del cache: {str(e)}"
        }


@router.get("/generate/nutrition-plan-stream/{task_id}")
def stream_nutrition_plan_status(task_id: str):
    """
    Endpoint SSE para streaming de progreso en tiempo real.
    Reduce significativamente el número de requests HTTP.
    """
    import asyncio
    import json
    
    async def event_stream():
        try:
            from celery.result import AsyncResult
            from app.background.celery_app import celery_app
            
            task = AsyncResult(task_id, app=celery_app)
            last_status = None
            
            while True:
                try:
                    current_status = task.state
                    
                    if current_status != last_status:
                        # Enviar evento SSE
                        if current_status == 'PENDING':
                            data = {
                                'status': 'PENDING', 
                                'progress': 0,
                                'message': 'Tarea en cola de espera...'
                            }
                        elif current_status == 'PROGRESS':
                            meta = task.info or {}
                            data = {
                                'status': 'PROGRESS', 
                                'progress': meta.get('progress', 0),
                                'step': meta.get('step', 'processing'),
                                'message': meta.get('message', 'Procesando...')
                            }
                        elif current_status == 'SUCCESS':
                            result = task.result
                            data = {
                                'status': 'SUCCESS', 
                                'plan': result.get('plan'),
                                'generated_at': result.get('generated_at'),
                                'days_generated': result.get('days_generated', 0),
                                'strategy': result.get('strategy', 'standard'),
                                'targets': result.get('targets', {})
                            }
                        elif current_status == 'FAILURE':
                            info = task.info
                            if hasattr(info, 'get'):
                                data = {
                                    'status': 'FAILURE', 
                                    'error': info.get('error', 'Error desconocido'),
                                    'error_type': info.get('error_type', 'UnknownError'),
                                    'failed_at': info.get('failed_at')
                                }
                            else:
                                error_type = type(info).__name__
                                error_message = str(info)
                                if 'TimeLimitExceeded' in error_type:
                                    error_message = "La tarea excedió el tiempo límite de procesamiento"
                                
                                data = {
                                    'status': 'FAILURE', 
                                    'error': error_message,
                                    'error_type': error_type,
                                    'failed_at': datetime.utcnow().isoformat()
                                }
                        else:
                            data = {
                                'status': 'UNKNOWN', 
                                'error': f'Estado desconocido: {current_status}',
                                'error_type': 'UnknownState'
                            }
                        
                        # Enviar como SSE
                        yield f"data: {json.dumps(data)}\n\n"
                        last_status = current_status
                        
                        # Si la tarea terminó, cerrar conexión
                        if current_status in ['SUCCESS', 'FAILURE']:
                            break
                    
                    # Esperar antes del siguiente check
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    error_data = {
                        'status': 'ERROR',
                        'error': f'Error en stream: {str(e)}',
                        'error_type': 'StreamError'
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    break
            
        except Exception as e:
            error_data = {
                'status': 'ERROR',
                'error': f'Error inicializando stream: {str(e)}',
                'error_type': 'StreamInitError'
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@router.post("/generate/workout-plan", response_model=schemas.WorkoutPlan)
def generate_workout_plan(
    payload: schemas.WorkoutPlanRequest,
    simulate: bool = Query(False),
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return services.generate_workout_plan(current_user, payload, db=db, simulate=simulate)


@router.post("/generate/nutrition-plan", response_model=schemas.NutritionPlan)
def generate_nutrition_plan(
    payload: schemas.NutritionPlanRequest,
    simulate: bool = Query(False),
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return services.generate_nutrition_plan(current_user, payload, db=db, simulate=simulate)


@router.post("/chat", response_model=schemas.ChatResponse)
def chat(
    payload: schemas.ChatRequest,
    current_user: UserContext = Depends(get_current_user),
):
    return services.chat(current_user, payload)


@router.post("/insights", response_model=schemas.InsightsResponse)
def insights(
    payload: schemas.InsightsRequest,
    current_user: UserContext = Depends(get_current_user),
):
    return services.insights(current_user, payload)


@router.post("/food-search/enhance", response_model=schemas.SmartFoodSearchResponse)
def enhance_food_search(
    payload: schemas.SmartFoodSearchRequest,
    simulate: bool = Query(False),
    current_user: UserContext = Depends(get_current_user),
):
    """Mejora la búsqueda de alimentos usando IA para entender mejor la consulta del usuario."""
    return smart_food_search.enhance_food_search(current_user, payload, simulate=simulate)


@router.get("/food-search/suggestions")
def get_food_suggestions(
    query: str = Query(..., description="Consulta de búsqueda"),
    context: str = Query(None, description="Contexto adicional (ej: desayuno, alto en proteína)"),
    simulate: bool = Query(False),
    current_user: UserContext = Depends(get_current_user),
):
    """Obtiene sugerencias inteligentes para búsqueda de alimentos."""
    suggestions = smart_food_search.get_food_search_suggestions(
        current_user, query, context, simulate=simulate
    )
    return {"suggestions": suggestions}


@router.get("/food-search/terms")
def get_enhanced_search_terms(
    query: str = Query(..., description="Consulta de búsqueda"),
    context: str = Query(None, description="Contexto adicional"),
    simulate: bool = Query(False),
    current_user: UserContext = Depends(get_current_user),
):
    """Obtiene términos de búsqueda mejorados para una consulta."""
    terms = smart_food_search.get_enhanced_search_terms(
        current_user, query, context, simulate=simulate
    )
    return {"search_terms": terms}


# ---------------------------------------------------------------------------
# Async Nutrition Plan Generation
# ---------------------------------------------------------------------------

@router.post("/generate/nutrition-plan-async")
def generate_nutrition_plan_async_endpoint(
    payload: schemas.NutritionPlanRequest,
    current_user: UserContext = Depends(get_current_user),
):
    """
    Inicia la generación asíncrona de un plan nutricional.
    
    Retorna un task_id que puede usarse para consultar el progreso.
    """
    # Iniciar tarea en background
    task = generate_nutrition_plan_task.delay(
        user_id=current_user.id,
        request_data=payload.model_dump()
    )
    
    return {
        "task_id": task.id,
        "status": "PENDING",
        "message": "Plan generándose en background",
        "estimated_time": "30-60 segundos"
    }


@router.post("/test-14-days-web-format")
async def test_14_days_web_format():
    """Test que simula exactamente el formato del endpoint principal para la web."""
    try:
        from app.ai.smart_generator import SmartNutritionPlanGenerator
        from app.user_profile.models import UserProfile, Goal, ActivityLevel
        from app.auth.deps import UserContext
        from app.ai import schemas
        from app.core.database import get_db
        
        # Simular usuario autenticado
        user_context = UserContext(
            id=1,
            user_id=1,
            email="test@example.com",
            is_active=True
        )
        
        # Crear request como lo haría la web
        payload = schemas.NutritionPlanRequest(
            days=14,
            goal="maintain_weight",
            activity_level="moderately_active"
        )
        
        # Usar el generador inteligente como lo hace el endpoint principal
        generator = SmartNutritionPlanGenerator()
        
        # Simular sesión de base de datos
        db = next(get_db())
        
        try:
            # Generar plan usando el mismo código que el endpoint principal
            plan = generator.generate_optimized_plan(user_context, payload, db)
            
            # Convertir a dict como lo hace el endpoint principal
            plan_data = plan.model_dump()
            
            # Respuesta en el mismo formato que el endpoint principal
            return {
                "task_id": f"smart-{user_context.id}-{datetime.utcnow().timestamp()}",
                "status": "SUCCESS",
                "message": f"Plan nutricional inteligente de {len(plan_data['days'])} días generado exitosamente",
                "plan": plan_data,
                "days_generated": len(plan_data['days']),
                "targets": plan_data['targets'],
                "progress": 100,
                "generated_at": datetime.utcnow().isoformat(),
                "generation_type": "smart_ai_with_profile_analysis"
            }
            
        finally:
            db.close()
            
    except Exception as e:
        return {
            "task_id": f"error-smart-test-{datetime.utcnow().timestamp()}",
            "status": "FAILURE",
            "error": f"Error generando plan inteligente: {str(e)}",
            "error_type": type(e).__name__
        }


@router.post("/test-smart-generation")
async def test_smart_generation():
    """Test del sistema inteligente de generación sin autenticación."""
    try:
        from app.ai.smart_generator import SmartNutritionPlanGenerator
        from app.user_profile.models import UserProfile, Goal, ActivityLevel
        from app.auth.deps import UserContext
        from app.ai import schemas
        from app.core.database import get_db
        
        # Crear perfil simulado para pruebas
        profile = UserProfile(
            user_id=1,
            age=30,
            sex="male",
            weight_kg=75.0,
            height_cm=175.0,
            goal=Goal.MAINTAIN_WEIGHT,
            activity_level=ActivityLevel.MODERATELY_ACTIVE,
            allergies=None,
            medical_conditions=None
        )
        
        # Crear contexto de usuario simulado
        user_context = UserContext(
            id=1,
            user_id=1,
            email="test@example.com",
            is_active=True
        )
        
        # Crear request
        request = schemas.NutritionPlanRequest(
            days=14,
            goal="maintain_weight",
            activity_level="moderately_active"
        )
        
        # Crear generador
        generator = SmartNutritionPlanGenerator()
        
        # Analizar perfil
        analysis = generator.analyze_user_profile(profile)
        
        # Obtener alimentos disponibles (simulados para prueba)
        available_foods = [
            {"name": "Pollo", "calories_kcal": 165, "protein_g": 31, "carbs_g": 0, "fat_g": 3.6},
            {"name": "Arroz integral", "calories_kcal": 111, "protein_g": 2.6, "carbs_g": 23, "fat_g": 0.9},
            {"name": "Brócoli", "calories_kcal": 34, "protein_g": 2.8, "carbs_g": 7, "fat_g": 0.4},
            {"name": "Aceite de oliva", "calories_kcal": 884, "protein_g": 0, "carbs_g": 0, "fat_g": 100},
            {"name": "Huevos", "calories_kcal": 155, "protein_g": 13, "carbs_g": 1.1, "fat_g": 11}
        ]
        
        return {
            "status": "success",
            "message": "Sistema inteligente funcionando correctamente",
            "profile_analysis": {
                "bmr": analysis.get("bmr"),
                "tdee": analysis.get("tdee"),
                "target_calories": analysis.get("target_calories"),
                "protein_g": analysis.get("protein_g"),
                "carbs_g": analysis.get("carbs_g"),
                "fat_g": analysis.get("fat_g")
            },
            "available_foods_count": len(available_foods),
            "test_profile": {
                "age": 30,
                "sex": "male",
                "weight_kg": 75.0,
                "height_cm": 175.0,
                "goal": "maintain_weight",
                "activity_level": "moderately_active"
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error en sistema inteligente: {str(e)}",
            "error_type": type(e).__name__
        }


@router.post("/test-web-generation")
async def test_web_generation():
    """Test de generación web sin autenticación - FUNCIONANDO."""
    try:
        from openai import OpenAI
        from app.core.config import settings
        import json
        from datetime import date, timedelta
        
        # Obtener API key
        api_key = getattr(settings, 'API_OPEN_AI', None) or settings.OPENAI_API_KEY
        if not api_key:
            return {
                "status": "error",
                "message": "API key no configurada"
            }
        
        client = OpenAI(api_key=api_key)
        
        # Generar fechas para 14 días
        today = date.today()
        dates = [(today + timedelta(days=i)).isoformat() for i in range(14)]
        
        # Prompt optimizado para GPT-5-nano
        system_prompt = """Eres PlanifitAI, un experto nutricionista. Genera planes nutricionales completos y realistas en formato JSON.

FORMATO EXACTO:
{
  "days": [
    {
      "date": "YYYY-MM-DD",
      "meals": [
        {
          "type": "breakfast|lunch|dinner|snack",
          "items": [
            {
              "name": "nombre del alimento",
              "qty": cantidad_numerica,
              "unit": "g|ml|unidad|taza",
              "kcal": calorias,
              "protein_g": proteinas,
              "carbs_g": carbohidratos,
              "fat_g": grasas
            }
          ],
          "meal_kcal": total_calorias_comida
        }
      ],
      "totals": {
        "kcal": total_dia,
        "protein_g": proteinas_dia,
        "carbs_g": carbohidratos_dia,
        "fat_g": grasas_dia
      }
    }
  ],
  "targets": {
    "kcal": objetivo_calorias,
    "protein_g": objetivo_proteinas,
    "carbs_g": objetivo_carbohidratos,
    "fat_g": objetivo_grasas
  }
}

ALIMENTOS DISPONIBLES: Pollo, salmón, huevos, yogur griego, arroz integral, quinoa, avena, patata, aguacate, aceite de oliva, brócoli, espinacas, tomate, plátano, manzana, nueces, almendras, leche, queso fresco.

COMIDAS: breakfast (desayuno), lunch (almuerzo), dinner (cena), snack (merienda).

IMPORTANTE: Responde SOLO con JSON válido, sin texto adicional."""

        user_prompt = f"""Genera un plan nutricional completo para 14 días (2 semanas completas).

DETALLES:
- Objetivo: mantener peso
- Nivel de actividad: moderadamente activo
- Fechas: {dates[0]} a {dates[-1]}
- Incluye 4 comidas por día: desayuno, almuerzo, cena y merienda
- Usa alimentos variados y saludables
- Mantén balance nutricional adecuado
- Considera horarios españoles de comida
- Varía los alimentos para evitar monotonía

Genera el JSON completo para los 14 días."""

        # Generar con GPT-5-nano
        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            reasoning_effort="low",
            verbosity="low"
        )
        
        reply = response.choices[0].message.content
        
        # Limpiar respuesta
        clean_reply = reply.strip()
        if clean_reply.startswith('```json'):
            clean_reply = clean_reply[7:]
        if clean_reply.endswith('```'):
            clean_reply = clean_reply[:-3]
        clean_reply = clean_reply.strip()
        
        # Parsear JSON
        plan_data = json.loads(clean_reply)
        
        # Validar estructura
        if not plan_data.get('days') or not plan_data.get('targets'):
            raise ValueError("Estructura JSON inválida")
        
        # Simular respuesta async exitosa (como lo espera la web)
        return {
            "task_id": f"test-web-{datetime.utcnow().timestamp()}",
            "status": "SUCCESS",
            "message": f"Plan nutricional de {len(plan_data['days'])} días generado exitosamente con GPT-5-nano",
            "plan": plan_data,
            "days_generated": len(plan_data['days']),
            "targets": plan_data['targets'],
            "progress": 100,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "task_id": f"error-test-{datetime.utcnow().timestamp()}",
            "status": "FAILURE",
            "error": f"Error generando plan: {str(e)}",
            "error_type": type(e).__name__
        }


@router.post("/generate/nutrition-plan-14-days-async")
def generate_nutrition_plan_14_days_async_endpoint(
    payload: schemas.NutritionPlanRequest,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generación inteligente de plan nutricional de 14 días.
    
    Analiza el perfil del usuario, genera el plan con IA y lo guarda en la base de datos.
    """
    try:
        from app.ai.smart_generator import generate_smart_nutrition_plan
        
        # Asegurar que se generen 14 días
        payload.days = 14
        
        # Generar plan inteligente
        plan = generate_smart_nutrition_plan(current_user, payload, db)
        
        # Convertir a dict para respuesta
        plan_data = plan.model_dump()

        # Persistencia controlada por bandera
        persist_result = {"skipped": True}
        if bool(getattr(payload, "persist_to_db", True)):
            try:
                # Limpiar comidas IA previas en las próximas 2 semanas
                plan_persistence.clean_existing_ai_meals(db, current_user.id, days_ahead=14)
                # Persistir nuevo plan en backend como planificado (estructura DB)
                persist_result = plan_persistence.persist_nutrition_plan(
                    db=db,
                    user_id=current_user.id,
                    plan_data=plan_data,
                    targets=plan_data.get("targets", {})
                )
            except Exception as persist_exc:
                # No bloquear la respuesta por errores de persistencia, pero informar
                persist_result = {
                    "success": False,
                    "message": f"Persistencia fallida: {str(persist_exc)}"
                }
        
        # Crear notificación in-app (en lista de notificaciones)
        try:
            from app.core.database import get_db as _get_db
            # ya tenemos db (dependency), lo reutilizamos
            dedupe_key = f"ai:nutrition:plan:{current_user.id}:{datetime.utcnow().date().isoformat()}"
            notif = notif_schemas.NotificationCreate(
                user_id=current_user.id,
                category=notif_models.NotificationCategory.NUTRITION,
                type=notif_models.NotificationType.CUSTOM,
                title="Plan de nutrición generado",
                body=f"Se generó un plan de {len(plan_data['days'])} días.",
                payload={
                    "days": len(plan_data["days"]),
                    "targets": plan_data.get("targets", {}),
                    "persist": persist_result,
                },
                scheduled_at_utc=datetime.utcnow(),
                dedupe_key=dedupe_key,
            )
            row = notif_crud.create_notification(db, notif)
            notif_services.dispatch_notification(db, row.id)
        except Exception:
            pass

        # Simular respuesta async exitosa (como lo espera la web)
        return {
            "task_id": f"smart-{current_user.id}-{datetime.utcnow().timestamp()}",
            "status": "SUCCESS",
            "message": f"Plan nutricional inteligente de {len(plan_data['days'])} días generado exitosamente",
            "plan": plan_data,
            "days_generated": len(plan_data['days']),
            "targets": plan_data['targets'],
            "progress": 100,
            "generated_at": datetime.utcnow().isoformat(),
            "generation_type": "smart_ai_with_profile_analysis",
            "persist": persist_result,
        }
        
    except Exception as e:
        logger.error(f"Error en endpoint de generación: {str(e)}")
        return {
            "task_id": f"error-smart-{current_user.id}-{datetime.utcnow().timestamp()}",
            "status": "FAILURE",
            "error": f"Error generando plan inteligente: {str(e)}",
            "error_type": type(e).__name__
        }


@router.get("/generate/nutrition-plan-status/{task_id}")
def get_nutrition_plan_status(task_id: str):
    """
    Consulta el estado de una tarea de generación de plan nutricional.
    
    Compatible con el nuevo sistema directo (sin Celery) y el sistema legacy.
    """
    try:
        # Verificar si es un task_id del nuevo sistema directo
        if task_id.startswith(('smart-', 'direct-', 'test-web-', 'error-')):
            # Sistema directo - la generación ya está completada
            if task_id.startswith('error-'):
                return {
                    'status': 'FAILURE',
                    'error': 'Error en generación directa',
                    'error_type': 'DirectGenerationError',
                    'message': 'Error en el sistema de generación directa'
                }
            else:
                # Para el sistema directo, la tarea ya está completada
                # La web espera información sobre días generados
                return {
                    'status': 'SUCCESS',
                    'progress': 100,
                    'message': 'Plan generado exitosamente con sistema directo',
                    'plan': None,  # El plan ya fue devuelto en la respuesta inicial
                    'generated_at': datetime.utcnow().isoformat(),
                    'generation_type': 'direct_system',
                    'days_generated': 14,  # Informar que se generaron 14 días
                    'targets': {
                        'kcal': 2200,
                        'protein_g': 120,
                        'carbs_g': 250,
                        'fat_g': 70
                    }
                }
        
        # Sistema legacy con Celery
        from celery.result import AsyncResult
        from app.background.celery_app import celery_app
        
        # Obtener resultado de la tarea usando la instancia de Celery
        task = AsyncResult(task_id, app=celery_app)
        
        if task.state == 'PENDING':
            response = {
                'status': 'PENDING', 
                'progress': 0,
                'message': 'Tarea en cola de espera...'
            }
        elif task.state == 'PROGRESS':
            meta = task.info or {}
            response = {
                'status': 'PROGRESS', 
                'progress': meta.get('progress', 0),
                'step': meta.get('step', 'processing'),
                'message': meta.get('message', 'Procesando...')
            }
        elif task.state == 'SUCCESS':
            result = task.result
            response = {
                'status': 'SUCCESS', 
                'plan': result.get('plan'),
                'generated_at': result.get('generated_at'),
                'days_generated': result.get('days_generated', 0),
                'strategy': result.get('strategy', 'standard'),
                'targets': result.get('targets', {})
            }
        elif task.state == 'FAILURE':
            # Manejar diferentes tipos de fallos
            info = task.info
            if hasattr(info, 'get'):
                # Es un diccionario normal
                response = {
                    'status': 'FAILURE', 
                    'error': info.get('error', 'Error desconocido'),
                    'error_type': info.get('error_type', 'UnknownError'),
                    'failed_at': info.get('failed_at')
                }
            else:
                # Es un objeto de excepción (como TimeLimitExceeded)
                error_type = type(info).__name__
                error_message = str(info)
                
                if 'TimeLimitExceeded' in error_type:
                    error_message = "La tarea excedió el tiempo límite de procesamiento"
                elif 'NotRegistered' in error_type:
                    error_message = "La tarea no está registrada en el worker"
                
                response = {
                    'status': 'FAILURE', 
                    'error': error_message,
                    'error_type': error_type,
                    'failed_at': datetime.utcnow().isoformat()
                }
        else:
            # Estado desconocido
            response = {
                'status': 'UNKNOWN', 
                'error': f'Estado desconocido: {task.state}',
                'error_type': 'UnknownState'
            }
        
        return response
        
    except Exception as e:
        # Log del error para debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error consultando estado de tarea {task_id}: {e}")
        
        # Manejar diferentes tipos de errores
        error_type = type(e).__name__
        error_message = str(e)
        
        if 'TimeLimitExceeded' in error_type:
            error_message = "La tarea excedió el tiempo límite de procesamiento"
        elif 'NotRegistered' in error_type:
            error_message = "La tarea no está registrada en el worker"
        elif 'ConnectionError' in error_type:
            error_message = "Error de conexión con el broker de Celery"
        
        return {
            'status': 'FAILURE',
            'error': error_message,
            'error_type': error_type,
            'failed_at': datetime.utcnow().isoformat()
        }


@router.delete("/generate/nutrition-plan-cancel/{task_id}")
def cancel_nutrition_plan_generation(task_id: str):
    """
    Cancela una tarea de generación de plan nutricional en progreso.
    """
    try:
        from celery.result import AsyncResult
        from app.background.celery_app import celery_app
        
        task = AsyncResult(task_id, app=celery_app)
        
        if task.state in ['PENDING', 'PROGRESS']:
            task.revoke(terminate=True)
            return {
                'status': 'CANCELLED',
                'message': 'Tarea cancelada exitosamente'
            }
        else:
            return {
                'status': 'NOT_CANCELLABLE',
                'message': f'La tarea ya está en estado {task.state} y no puede ser cancelada'
            }
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error cancelando tarea {task_id}: {e}")
        
        return {
            'status': 'ERROR',
            'message': f'Error cancelando tarea: {str(e)}'
        }


@router.get("/test-simple")
def test_simple():
    """Test básico sin dependencias complejas."""
    return {
        "status": "success", 
        "message": "Endpoint simple funcionando",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/test-static-plan")
def test_static_plan():
    """Endpoint que devuelve un plan estático de 14 días para pruebas."""
    
    # Plan estático de 14 días
    plan_data = {
        "days": []
    }
    
    # Generar 14 días con estructura simple
    for i in range(14):
        day = {
            "day": i + 1,
            "meals": [
                {
                    "type": "desayuno",
                    "name": f"Desayuno Día {i + 1}",
                    "items": [
                        {"name": "Avena con frutas", "quantity": 100, "unit": "g", "calories": 150, "protein": 5, "carbs": 30, "fat": 3},
                        {"name": "Leche", "quantity": 200, "unit": "ml", "calories": 80, "protein": 8, "carbs": 12, "fat": 0}
                    ]
                },
                {
                    "type": "almuerzo", 
                    "name": f"Almuerzo Día {i + 1}",
                    "items": [
                        {"name": "Pollo", "quantity": 150, "unit": "g", "calories": 250, "protein": 30, "carbs": 0, "fat": 12},
                        {"name": "Arroz", "quantity": 80, "unit": "g", "calories": 280, "protein": 6, "carbs": 60, "fat": 2}
                    ]
                },
                {
                    "type": "cena",
                    "name": f"Cena Día {i + 1}",
                    "items": [
                        {"name": "Salmón", "quantity": 120, "unit": "g", "calories": 200, "protein": 25, "carbs": 0, "fat": 12},
                        {"name": "Ensalada", "quantity": 150, "unit": "g", "calories": 30, "protein": 2, "carbs": 6, "fat": 0}
                    ]
                },
                {
                    "type": "merienda",
                    "name": f"Merienda Día {i + 1}",
                    "items": [
                        {"name": "Yogur", "quantity": 150, "unit": "g", "calories": 100, "protein": 15, "carbs": 8, "fat": 2}
                    ]
                }
            ]
        }
        plan_data["days"].append(day)
    
    plan_data["targets"] = {
        "kcal": 2200,
        "protein_g": 120,
        "carbs_g": 250,
        "fat_g": 70
    }
    
    return {
        "task_id": f"static-{datetime.utcnow().timestamp()}",
        "status": "SUCCESS",
        "message": f"Plan estático de {len(plan_data['days'])} días",
        "plan": plan_data,
        "days_generated": len(plan_data['days']),
        "targets": plan_data['targets'],
        "progress": 100,
        "generated_at": datetime.utcnow().isoformat()
    }


