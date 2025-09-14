#!/usr/bin/env python3
"""
Script de prueba para verificar que el endpoint getFoodDetails funciona.
"""

import requests
import json

def test_food_details_endpoint():
    """Prueba el endpoint de detalles de alimentos."""
    
    print("🍎 Probando endpoint de detalles de alimentos...")
    
    # Primero buscar algunos alimentos para obtener IDs
    print("\n1. Buscando alimentos...")
    try:
        search_response = requests.get('http://localhost:8000/api/v1/nutrition/foods/search?q=manzana&page=1&page_size=3')
        
        if search_response.status_code == 200:
            foods = search_response.json().get('data', [])
            print(f"   ✅ Encontrados {len(foods)} alimentos")
            
            if foods:
                # Probar con el primer alimento encontrado
                first_food = foods[0]
                food_id = first_food.get('id')
                food_name = first_food.get('name', 'Unknown')
                
                print(f"\n2. Probando detalles del alimento: {food_name} (ID: {food_id})")
                
                try:
                    details_response = requests.get(f'http://localhost:8000/api/v1/nutrition/foods/{food_id}')
                    
                    print(f"   - Status Code: {details_response.status_code}")
                    
                    if details_response.status_code == 200:
                        details = details_response.json().get('data', {})
                        print(f"   ✅ ¡Éxito! Detalles obtenidos:")
                        print(f"   - Nombre: {details.get('name', 'N/A')}")
                        print(f"   - Calorías: {details.get('calories_kcal', 'N/A')} kcal")
                        print(f"   - Proteína: {details.get('protein_g', 'N/A')} g")
                        print(f"   - Carbohidratos: {details.get('carbs_g', 'N/A')} g")
                        print(f"   - Grasa: {details.get('fat_g', 'N/A')} g")
                        print(f"   - Fuente: {details.get('source', 'N/A')}")
                    else:
                        print(f"   ❌ Error: {details_response.status_code}")
                        print(f"   - Response: {details_response.text}")
                        
                except Exception as e:
                    print(f"   ❌ Error obteniendo detalles: {e}")
            else:
                print("   ⚠️ No se encontraron alimentos para probar")
        else:
            print(f"   ❌ Error en búsqueda: {search_response.status_code}")
            print(f"   - Response: {search_response.text}")
            
    except Exception as e:
        print(f"   ❌ Error en búsqueda: {e}")
    
    # Probar con un ID que no existe
    print(f"\n3. Probando con ID inexistente...")
    try:
        fake_response = requests.get('http://localhost:8000/api/v1/nutrition/foods/fake-id-123')
        print(f"   - Status Code: {fake_response.status_code}")
        
        if fake_response.status_code == 404:
            print(f"   ✅ Correcto: Devuelve 404 para ID inexistente")
        else:
            print(f"   ⚠️ Esperado 404, pero recibido: {fake_response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error probando ID inexistente: {e}")


if __name__ == "__main__":
    test_food_details_endpoint()
