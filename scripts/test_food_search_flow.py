#!/usr/bin/env python3
"""
Script de prueba para verificar el flujo completo del buscador de alimentos.
"""

import requests
import json

def test_food_search_flow():
    """Prueba el flujo completo de búsqueda de alimentos."""
    
    print("🔍 Probando flujo completo de búsqueda de alimentos...")
    
    # 1. Probar búsqueda de alimentos
    print("\n1. Probando búsqueda de alimentos...")
    try:
        search_response = requests.get('http://localhost:8000/api/v1/nutrition/foods/search?q=manzana&page=1&page_size=5')
        
        if search_response.status_code == 200:
            foods = search_response.json().get('data', [])
            print(f"   ✅ Encontrados {len(foods)} alimentos")
            
            if foods:
                first_food = foods[0]
                food_id = first_food.get('id')
                food_name = first_food.get('name', 'Unknown')
                
                print(f"   - Primer alimento: {food_name} (ID: {food_id})")
                
                # 2. Probar obtener detalles del alimento
                print(f"\n2. Probando detalles del alimento...")
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
                        print(f"   - Sugerencias de porción: {details.get('portion_suggestions', 'N/A')}")
                        
                        # Verificar campos requeridos para el frontend
                        required_fields = ['name', 'calories_kcal', 'protein_g', 'carbs_g', 'fat_g']
                        missing_fields = [field for field in required_fields if field not in details or details[field] is None]
                        
                        if missing_fields:
                            print(f"   ⚠️ Campos faltantes: {missing_fields}")
                        else:
                            print(f"   ✅ Todos los campos requeridos están presentes")
                            
                    else:
                        print(f"   ❌ Error obteniendo detalles: {details_response.status_code}")
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
    
    # 3. Probar búsqueda inteligente
    print(f"\n3. Probando búsqueda inteligente...")
    try:
        smart_response = requests.get('http://localhost:8000/api/v1/nutrition/foods/search-smart?q=manzana&page=1&page_size=5&simulate_ai=true')
        
        print(f"   - Status Code: {smart_response.status_code}")
        
        if smart_response.status_code == 200:
            smart_foods = smart_response.json().get('data', [])
            print(f"   ✅ Búsqueda inteligente funcionando: {len(smart_foods)} resultados")
        else:
            print(f"   ❌ Error en búsqueda inteligente: {smart_response.status_code}")
            print(f"   - Response: {smart_response.text}")
            
    except Exception as e:
        print(f"   ❌ Error en búsqueda inteligente: {e}")
    
    # 4. Probar sugerencias de IA
    print(f"\n4. Probando sugerencias de IA...")
    try:
        suggestions_response = requests.get('http://localhost:8000/api/v1/ai/food-search/suggestions?query=manzana&simulate=true')
        
        print(f"   - Status Code: {suggestions_response.status_code}")
        
        if suggestions_response.status_code == 200:
            suggestions_data = suggestions_response.json().get('data', {})
            suggestions = suggestions_data.get('suggestions', [])
            print(f"   ✅ Sugerencias de IA funcionando: {len(suggestions)} sugerencias")
            if suggestions:
                print(f"   - Ejemplos: {suggestions[:3]}")
        else:
            print(f"   ❌ Error en sugerencias de IA: {suggestions_response.status_code}")
            print(f"   - Response: {suggestions_response.text}")
            
    except Exception as e:
        print(f"   ❌ Error en sugerencias de IA: {e}")


if __name__ == "__main__":
    test_food_search_flow()
