"""Collection of prompt templates used by the AI services.

This module purposely keeps the prompts very small; in a real
implementation they would include extensive instructions and few-shots.
"""

WORKOUT_PLAN_SYSTEM_PROMPT = "Eres un entrenador personal y respondes en JSON."
NUTRITION_PLAN_SYSTEM_PROMPT = "Eres un dietista deportivo y respondes en JSON."
CHAT_SYSTEM_PROMPT = "Eres un coach amable y práctico."
INSIGHTS_SYSTEM_PROMPT = "Eres un analista que genera métricas en JSON."
