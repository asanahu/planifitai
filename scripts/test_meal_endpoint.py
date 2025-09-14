#!/usr/bin/env python3
"""
Script de prueba para verificar el endpoint de creación de comidas.
"""

import requests
import json
from datetime import datetime
import pytz

def test_meal_creation_endpoint():
    """Prueba el endpoint de creación de comidas."""
    
    print("🍽️ Probando endpoint de creación de comidas...")
    
    # Obtener fecha actual en Madrid
    madrid_tz = pytz.timezone('Europe/Madrid')
    today_madrid = datetime.now(madrid_tz).date()
    
    print(f"📅 Fecha de Madrid: {today_madrid}")
    
    # Payload de prueba
    payload = {
        "date": str(today_madrid),
        "meal_type": "breakfast",
        "name": "Desayuno de prueba",
        "items": []
    }
    
    print(f"📤 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Probar el endpoint
        response = requests.post(
            'http://localhost:8000/api/v1/nutrition/meal',
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"\n📊 Respuesta:")
        print(f"   - Status Code: {response.status_code}")
        print(f"   - Headers: {dict(response.headers)}")
        
        if response.status_code == 200 or response.status_code == 201:
            print(f"   ✅ ¡Éxito! Comida creada correctamente")
            print(f"   - Response: {response.json()}")
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   - Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Error de conexión: No se puede conectar al servidor")
        print(f"   - Asegúrate de que el servidor esté corriendo en localhost:8000")
    except Exception as e:
        print(f"   ❌ Error inesperado: {e}")
    
    # Probar también el endpoint de salud
    print(f"\n🏥 Probando endpoint de salud...")
    try:
        health_response = requests.get('http://localhost:8000/health')
        print(f"   - Health Status: {health_response.status_code}")
        if health_response.status_code == 200:
            print(f"   ✅ Servidor funcionando correctamente")
        else:
            print(f"   ❌ Problema con el servidor")
    except Exception as e:
        print(f"   ❌ Error conectando al servidor: {e}")


if __name__ == "__main__":
    test_meal_creation_endpoint()
