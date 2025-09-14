"""Servicio de búsqueda inteligente de alimentos usando IA."""

from __future__ import annotations

import json
import logging
from typing import List, Optional

from fastapi import HTTPException

from app.ai_client import get_ai_client
from app.auth.deps import UserContext
from . import schemas

logger = logging.getLogger(__name__)


def enhance_food_search(
    user: UserContext,
    req: schemas.SmartFoodSearchRequest,
    *,
    simulate: bool = False,
) -> schemas.SmartFoodSearchResponse:
    """
    Mejora la búsqueda de alimentos usando IA para entender mejor la consulta del usuario.
    
    La IA analiza la consulta y:
    1. Genera términos de búsqueda más efectivos
    2. Sugiere alimentos relacionados
    3. Proporciona contexto nutricional cuando es relevante
    """
    
    if simulate:
        # Respuesta simulada mejorada con sugerencias más útiles
        query_lower = req.query.lower()
        
        # Generar sugerencias específicas basadas en la consulta
        suggestions = []
        
        if "dulce" in query_lower or "sweet" in query_lower:
            suggestions = ["apple", "banana", "grapes", "strawberries", "honey"]
        elif "salado" in query_lower or "salty" in query_lower:
            suggestions = ["cheese", "ham", "olives", "nuts", "bread"]
        elif "proteína" in query_lower or "protein" in query_lower:
            suggestions = ["chicken", "egg", "tuna", "yogurt", "beans"]
        elif "desayuno" in query_lower or "breakfast" in query_lower:
            suggestions = ["cereal", "milk", "bread", "butter", "coffee"]
        elif "almuerzo" in query_lower or "comida" in query_lower or "lunch" in query_lower:
            suggestions = ["salad", "pasta", "rice", "vegetables", "meat"]
        elif "cena" in query_lower or "dinner" in query_lower:
            suggestions = ["fish", "soup", "vegetables", "chicken", "salad"]
        elif "snack" in query_lower or "merienda" in query_lower:
            suggestions = ["nuts", "yogurt", "fruit", "cookies", "cheese"]
        else:
            # Sugerencias genéricas más útiles (en inglés para mejor compatibilidad)
            suggestions = ["apple", "banana", "yogurt", "cheese", "nuts"]
        
        return schemas.SmartFoodSearchResponse(
            enhanced_query=req.query,
            search_terms=[req.query] + suggestions[:3],  # Incluir algunas sugerencias como términos de búsqueda
            suggestions=suggestions[:5],
            context_notes=f"Sugerencias simuladas para: {req.query}"
        )
    
    client = get_ai_client()
    
    # Prompt del sistema para entender búsquedas de alimentos
    sys_prompt = (
        "Eres un asistente nutricional experto. Tu tarea es mejorar las búsquedas de alimentos "
        "entendiendo la intención del usuario y generando términos de búsqueda más efectivos. "
        "Responde ÚNICAMENTE con JSON válido sin explicaciones adicionales.\n\n"
        "Esquema de respuesta:\n"
        "{\n"
        '  "enhanced_query": "consulta mejorada y más específica",\n'
        '  "search_terms": ["término1", "término2", "término3"],\n'
        '  "suggestions": ["sugerencia1", "sugerencia2", "sugerencia3"],\n'
        '  "context_notes": "nota contextual opcional"\n'
        "}\n\n"
        "Reglas:\n"
        "- enhanced_query: Reescribe la consulta de forma más específica y clara\n"
        "- search_terms: Lista de términos de búsqueda efectivos (máximo 5)\n"
        "- suggestions: Sugerencias de alimentos relacionados (máximo 5)\n"
        "- context_notes: Solo si hay información nutricional relevante\n"
        "- Usa nombres comunes de alimentos en español\n"
        "- Considera sinónimos y variaciones comunes\n"
        "- Si menciona características nutricionales, inclúyelas en los términos"
    )
    
    # Construir el prompt del usuario
    context_info = ""
    if req.context:
        context_info = f" Contexto adicional: {req.context}."
    
    user_prompt = (
        f"Mejora esta búsqueda de alimentos: '{req.query}'.{context_info}\n\n"
        f"Genera hasta {req.max_suggestions} sugerencias relacionadas. "
        "Si la consulta es muy general, hazla más específica. "
        "Si menciona características nutricionales, inclúyelas en los términos de búsqueda."
    )
    
    try:
        resp = client.chat(
            user.id,
            [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        
        # Parsear la respuesta JSON
        reply = resp.get("reply", "")
        data = _parse_json_response(reply)
        
        # Validar y crear la respuesta
        return schemas.SmartFoodSearchResponse(
            enhanced_query=data.get("enhanced_query", req.query),
            search_terms=data.get("search_terms", [req.query])[:5],
            suggestions=data.get("suggestions", [])[:req.max_suggestions],
            context_notes=data.get("context_notes")
        )
        
    except Exception as e:
        logger.error(f"Error en búsqueda inteligente de alimentos: {e}")
        # Fallback a búsqueda simple
        return schemas.SmartFoodSearchResponse(
            enhanced_query=req.query,
            search_terms=[req.query],
            suggestions=[],
            context_notes="Búsqueda básica (IA no disponible)"
        )


def _parse_json_response(text: str) -> dict:
    """Extrae un objeto JSON de la respuesta del modelo."""
    import re
    
    try:
        return json.loads(text)
    except Exception:
        pass
    
    # Buscar bloques de código JSON
    fence = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
    if fence:
        try:
            return json.loads(fence.group(1))
        except Exception:
            pass
    
    # Heurística: primer { ... último }
    start = text.find("{")
    end = text.rfind("}")
    if 0 <= start < end:
        try:
            return json.loads(text[start : end + 1])
        except Exception:
            pass
    
    raise HTTPException(status_code=502, detail="Respuesta de IA inválida")


def get_food_search_suggestions(
    user: UserContext,
    query: str,
    context: Optional[str] = None,
    *,
    simulate: bool = False,
) -> List[str]:
    """
    Obtiene sugerencias inteligentes para búsqueda de alimentos.
    
    Args:
        user: Contexto del usuario
        query: Consulta de búsqueda
        context: Contexto adicional (ej: "desayuno", "alto en proteína")
        simulate: Si usar modo simulación
    
    Returns:
        Lista de sugerencias de alimentos
    """
    req = schemas.SmartFoodSearchRequest(
        query=query,
        context=context,
        max_suggestions=5
    )
    
    response = enhance_food_search(user, req, simulate=simulate)
    return response.suggestions


def get_enhanced_search_terms(
    user: UserContext,
    query: str,
    context: Optional[str] = None,
    *,
    simulate: bool = False,
) -> List[str]:
    """
    Obtiene términos de búsqueda mejorados para una consulta.
    
    Args:
        user: Contexto del usuario
        query: Consulta original
        context: Contexto adicional
        simulate: Si usar modo simulación
    
    Returns:
        Lista de términos de búsqueda mejorados
    """
    req = schemas.SmartFoodSearchRequest(
        query=query,
        context=context,
        max_suggestions=3
    )
    
    response = enhance_food_search(user, req, simulate=simulate)
    return response.search_terms
