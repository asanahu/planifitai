#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad de búsqueda inteligente de alimentos.
"""

import asyncio
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path para importar módulos
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Configurar variables de entorno para testing
os.environ.setdefault('OPENROUTER_KEY', 'test-key')
os.environ.setdefault('DATABASE_URL', 'sqlite:///test.db')

def test_smart_food_search():
    """Prueba la funcionalidad de búsqueda inteligente de alimentos."""
    
    print("🧪 Probando búsqueda inteligente de alimentos...")
    
    try:
        from app.ai.smart_food_search import enhance_food_search, get_food_search_suggestions
        from app.auth.deps import UserContext
        from app.ai.schemas import SmartFoodSearchRequest
        
        # Crear un contexto de usuario de prueba
        user_context = UserContext(id=1, email="test@example.com", username="testuser")
        
        # Casos de prueba
        test_cases = [
            {
                "query": "algo dulce para desayunar",
                "context": "desayuno",
                "description": "Búsqueda contextual para desayuno"
            },
            {
                "query": "alto en proteína",
                "context": "post-entrenamiento",
                "description": "Búsqueda por características nutricionales"
            },
            {
                "query": "manzana",
                "context": None,
                "description": "Búsqueda simple de alimento específico"
            },
            {
                "query": "algo saludable",
                "context": "snack",
                "description": "Búsqueda general con contexto"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📝 Prueba {i}: {test_case['description']}")
            print(f"   Consulta: '{test_case['query']}'")
            if test_case['context']:
                print(f"   Contexto: '{test_case['context']}'")
            
            try:
                # Probar la función de mejora de búsqueda
                req = SmartFoodSearchRequest(
                    query=test_case['query'],
                    context=test_case['context'],
                    max_suggestions=3
                )
                
                # Usar modo simulación para evitar llamadas reales a IA
                response = enhance_food_search(user_context, req, simulate=True)
                
                print(f"   ✅ Consulta mejorada: '{response.enhanced_query}'")
                print(f"   🔍 Términos de búsqueda: {response.search_terms}")
                print(f"   💡 Sugerencias: {response.suggestions}")
                if response.context_notes:
                    print(f"   📝 Notas: {response.context_notes}")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print("\n🎯 Probando sugerencias específicas...")
        
        # Probar sugerencias específicas
        suggestion_tests = [
            ("fruta", "desayuno"),
            ("proteína", "almuerzo"),
            ("snack", None)
        ]
        
        for query, context in suggestion_tests:
            try:
                suggestions = get_food_search_suggestions(
                    user_context, query, context, simulate=True
                )
                print(f"   Consulta: '{query}' -> Sugerencias: {suggestions}")
            except Exception as e:
                print(f"   Error con '{query}': {e}")
        
        print("\n✅ Pruebas completadas!")
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("Asegúrate de que estás ejecutando desde el directorio raíz del proyecto")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")


if __name__ == "__main__":
    test_smart_food_search()
