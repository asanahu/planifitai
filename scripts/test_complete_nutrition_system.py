#!/usr/bin/env python3
"""Sistema completo de generación de planes nutricionales con GPT-5-nano"""

import os
import sys
import json
from datetime import date, timedelta
from openai import OpenAI

def generate_nutrition_plan_complete(days=14, goal="maintain_weight", activity_level="moderately_active"):
    """Genera un plan nutricional completo usando GPT-5-nano."""
    
    # Obtener API key
    api_key = os.getenv('API_OPEN_AI')
    if not api_key:
        print("❌ API_OPEN_AI no encontrada")
        return None
    
    print(f"✅ API Key encontrada: {api_key[:20]}...")
    
    try:
        client = OpenAI(api_key=api_key)
        
        # Generar fechas
        today = date.today()
        dates = [(today + timedelta(days=i)).isoformat() for i in range(days)]
        
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

        user_prompt = f"""Genera un plan nutricional completo para {days} días.

DETALLES:
- Objetivo: {goal}
- Nivel de actividad: {activity_level}
- Fechas: {', '.join(dates[:5])}{'...' if len(dates) > 5 else ''}
- Incluye 4 comidas por día: desayuno, almuerzo, cena y merienda
- Usa alimentos variados y saludables
- Mantén balance nutricional adecuado
- Considera horarios españoles de comida

Genera el JSON completo para los {days} días."""

        print(f"🔄 Generando plan nutricional de {days} días con GPT-5-nano...")
        print(f"📅 Fechas: {dates[0]} a {dates[-1]}")
        
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
        print(f"✅ Respuesta recibida: {len(reply)} caracteres")
        
        # Limpiar respuesta
        clean_reply = reply.strip()
        if clean_reply.startswith('```json'):
            clean_reply = clean_reply[7:]
        if clean_reply.endswith('```'):
            clean_reply = clean_reply[:-3]
        clean_reply = clean_reply.strip()
        
        # Parsear JSON
        try:
            plan = json.loads(clean_reply)
            
            # Validar estructura
            if not plan.get('days') or not plan.get('targets'):
                raise ValueError("Estructura JSON inválida")
            
            days_generated = len(plan['days'])
            print(f"✅ Plan generado exitosamente!")
            print(f"📊 Días generados: {days_generated}")
            print(f"🎯 Objetivos: {plan['targets']}")
            
            # Mostrar resumen del primer día
            if plan['days']:
                first_day = plan['days'][0]
                meals_count = len(first_day.get('meals', []))
                print(f"🍽️ Comidas del primer día ({first_day.get('date', 'N/A')}): {meals_count}")
                
                for meal in first_day.get('meals', []):
                    items_count = len(meal.get('items', []))
                    print(f"  - {meal.get('type', 'unknown')}: {items_count} items")
            
            return plan
            
        except json.JSONDecodeError as e:
            print(f"❌ Error parseando JSON: {e}")
            print(f"📝 Contenido: {clean_reply[:500]}...")
            return None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"🔍 Tipo: {type(e).__name__}")
        return None

def test_generation():
    """Prueba la generación con diferentes configuraciones."""
    
    print("🧪 PRUEBAS DE GENERACIÓN CON GPT-5-NANO")
    print("=" * 50)
    
    # Prueba 1: 1 día
    print("\n📋 PRUEBA 1: Generación de 1 día")
    plan_1 = generate_nutrition_plan_complete(days=1)
    if plan_1:
        print("✅ Prueba 1 exitosa")
    else:
        print("❌ Prueba 1 falló")
    
    # Prueba 2: 7 días
    print("\n📋 PRUEBA 2: Generación de 7 días")
    plan_7 = generate_nutrition_plan_complete(days=7)
    if plan_7:
        print("✅ Prueba 2 exitosa")
    else:
        print("❌ Prueba 2 falló")
    
    # Prueba 3: 14 días (completo)
    print("\n📋 PRUEBA 3: Generación de 14 días (COMPLETO)")
    plan_14 = generate_nutrition_plan_complete(days=14)
    if plan_14:
        print("✅ Prueba 3 exitosa - PLAN DE 2 SEMANAS GENERADO")
        return plan_14
    else:
        print("❌ Prueba 3 falló")
        return None

if __name__ == "__main__":
    success = test_generation()
    if success:
        print(f"\n🎉 SISTEMA FUNCIONANDO CORRECTAMENTE")
        print(f"📊 Plan de {len(success['days'])} días generado exitosamente")
    else:
        print(f"\n❌ SISTEMA CON PROBLEMAS")
        sys.exit(1)
