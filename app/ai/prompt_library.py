"""Collection of prompt templates used by the AI services.

This module contains optimized prompts with detailed instructions for better AI performance.
"""

WORKOUT_PLAN_SYSTEM_PROMPT = "Eres un entrenador personal y respondes en JSON."

NUTRITION_PLAN_SYSTEM_PROMPT = """Eres PlanifitAI. Genera plan nutricional en JSON.

FORMATO: {days: [{date: str, meals: [{type: str, items: [{name: str, qty: float, unit: str, kcal: float, protein_g: float, carbs_g: float, fat_g: float}]}], totals: {kcal: float, protein_g: float, carbs_g: float, fat_g: float}}], targets: {kcal: float, protein_g: float, carbs_g: float, fat_g: float}}

ALIMENTOS: Pollo, salmón, huevos, yogur, arroz, quinoa, avena, patata, aguacate, aceite oliva, brócoli, espinacas, tomate.

COMIDAS: breakfast, lunch, dinner, snack. Solo JSON."""

CHAT_SYSTEM_PROMPT = "Eres un coach amable y práctico."
INSIGHTS_SYSTEM_PROMPT = "Eres un analista que genera métricas en JSON."
