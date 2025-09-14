#!/usr/bin/env python3
"""Test directo de generación nutricional con GPT-5-nano"""

import os
import sys
import json
from openai import OpenAI

def test_nutrition_generation():
    # Obtener API key del entorno
    api_key = os.getenv('API_OPEN_AI')
    if not api_key:
        print("❌ API_OPEN_AI no encontrada en variables de entorno")
        return False
    
    print(f"✅ API Key encontrada: {api_key[:20]}...")
    
    try:
        client = OpenAI(api_key=api_key)
        
        # Prompt optimizado para GPT-5-nano
        system_prompt = """Eres PlanifitAI. Genera plan nutricional en JSON.

FORMATO: {days: [{date: str, meals: [{type: str, items: [{name: str, qty: float, unit: str, kcal: float, protein_g: float, carbs_g: float, fat_g: float}]}], totals: {kcal: float, protein_g: float, carbs_g: float, fat_g: float}}], targets: {kcal: float, protein_g: float, carbs_g: float, fat_g: float}}

ALIMENTOS: Pollo, salmón, huevos, yogur, arroz, quinoa, avena, patata, aguacate, aceite oliva, brócoli, espinacas, tomate.

COMIDAS: breakfast, lunch, dinner, snack. Solo JSON."""

        user_prompt = """Genera un plan nutricional simple para 1 día en formato JSON. Incluye desayuno, almuerzo y cena con alimentos básicos."""

        print("🔄 Generando plan nutricional con GPT-5-nano...")
        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            reasoning_effort="low",  # Parámetro específico de GPT-5-nano
            verbosity="low"       # Parámetro específico de GPT-5-nano
        )
        
        reply = response.choices[0].message.content
        print(f"✅ Respuesta recibida:")
        print(f"Longitud: {len(reply)} caracteres")
        print(f"Primeros 200 caracteres: {reply[:200]}...")
        
        # Limpiar respuesta (remover markdown si existe)
        clean_reply = reply.strip()
        if clean_reply.startswith('```json'):
            clean_reply = clean_reply[7:]  # Remover ```json
        if clean_reply.endswith('```'):
            clean_reply = clean_reply[:-3]  # Remover ```
        clean_reply = clean_reply.strip()
        
        # Intentar parsear como JSON
        try:
            plan = json.loads(clean_reply)
            print(f"✅ JSON válido!")
            print(f"Días: {len(plan.get('days', []))}")
            if plan.get('days'):
                first_day = plan['days'][0]
                print(f"Comidas del primer día: {len(first_day.get('meals', []))}")
                for meal in first_day.get('meals', []):
                    print(f"  - {meal.get('type', 'unknown')}: {len(meal.get('items', []))} items")
            return True
        except json.JSONDecodeError as e:
            print(f"❌ Error parseando JSON: {e}")
            print(f"Contenido limpio: {clean_reply[:500]}...")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Tipo de error: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = test_nutrition_generation()
    sys.exit(0 if success else 1)
