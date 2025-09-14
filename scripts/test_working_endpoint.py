#!/usr/bin/env python3
"""Test del endpoint funcional de generación nutricional"""

import requests
import json

def test_working_endpoint():
    url = "http://localhost:8000/api/v1/ai/generate/nutrition-plan-direct-working"
    
    # Datos del request para 14 días
    data = {
        "days": 14,
        "goal": "maintain_weight",
        "activity_level": "moderately_active"
    }
    
    # Headers (simulando usuario autenticado)
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test-token"  # Token de prueba
    }
    
    print("🔄 Probando endpoint funcional de generación nutricional...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=120)
        
        print(f"✅ Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                plan = result.get("plan", {})
                days = plan.get("days", [])
                targets = result.get("targets", {})
                
                print(f"✅ Plan generado exitosamente!")
                print(f"📊 Días generados: {len(days)}")
                print(f"🎯 Objetivos: {targets}")
                
                if days:
                    first_day = days[0]
                    meals = first_day.get("meals", [])
                    print(f"🍽️ Comidas del primer día ({first_day.get('date', 'N/A')}): {len(meals)}")
                    
                    for meal in meals:
                        items = meal.get("items", [])
                        print(f"  - {meal.get('type', 'unknown')}: {len(items)} items")
                
                return True
            else:
                print(f"❌ Error en respuesta: {result.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"❌ Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error en request: {e}")
        return False

if __name__ == "__main__":
    success = test_working_endpoint()
    print(f"\n{'✅ ÉXITO' if success else '❌ FALLO'}")
