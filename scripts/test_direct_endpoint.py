#!/usr/bin/env python3
"""Test del endpoint directo de generación nutricional"""

import requests
import json

def test_direct_endpoint():
    url = "http://localhost:8000/api/v1/ai/generate/nutrition-plan-direct"
    
    # Datos del request
    data = {
        "days": 1,
        "goal": "maintain_weight",
        "activity_level": "moderately_active"
    }
    
    # Headers (simulando usuario autenticado)
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test-token"  # Token de prueba
    }
    
    print("🔄 Probando endpoint directo...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=60)
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"✅ Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                plan = result.get("plan", {})
                days = plan.get("days", [])
                print(f"✅ Plan generado exitosamente!")
                print(f"✅ Días: {len(days)}")
                if days:
                    first_day = days[0]
                    meals = first_day.get("meals", [])
                    print(f"✅ Comidas del primer día: {len(meals)}")
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
    success = test_direct_endpoint()
    print(f"\n{'✅ ÉXITO' if success else '❌ FALLO'}")
