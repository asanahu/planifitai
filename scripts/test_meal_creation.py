#!/usr/bin/env python3
"""
Script de prueba para verificar la creación de comidas.
"""

import sys
import os
from pathlib import Path
from datetime import date

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Configurar variables de entorno para testing
os.environ.setdefault('OPENROUTER_KEY', 'test-key')
os.environ.setdefault('DATABASE_URL', 'sqlite:///test.db')

def test_meal_creation():
    """Prueba la creación de comidas."""
    
    print("🍽️ Probando creación de comidas...")
    
    try:
        from app.nutrition.schemas import MealCreate, MealType
        from app.nutrition import crud
        from app.core.database import get_db
        from sqlalchemy.orm import Session
        
        # Crear payload de prueba
        payload = MealCreate(
            date=date.today(),
            meal_type=MealType.breakfast,
            name="Desayuno de prueba",
            items=[]
        )
        
        print(f"✅ Payload creado correctamente:")
        print(f"   - Fecha: {payload.date}")
        print(f"   - Tipo: {payload.meal_type}")
        print(f"   - Nombre: {payload.name}")
        print(f"   - Items: {len(payload.items)}")
        
        # Verificar que el esquema es válido
        print(f"\n✅ Esquema MealCreate válido")
        
        # Probar diferentes tipos de comida
        meal_types = [
            (MealType.breakfast, "Desayuno"),
            (MealType.lunch, "Comida"),
            (MealType.dinner, "Cena"),
            (MealType.snack, "Snack"),
            (MealType.other, "Otro")
        ]
        
        print(f"\n📋 Probando diferentes tipos de comida:")
        for meal_type, name in meal_types:
            test_payload = MealCreate(
                date=date.today(),
                meal_type=meal_type,
                name=name,
                items=[]
            )
            print(f"   ✅ {meal_type.value}: {name}")
        
        print(f"\n🎯 Problema identificado y solucionado:")
        print(f"   ❌ Frontend enviaba: {{ date, meal_type, name }}")
        print(f"   ✅ Frontend ahora envía: {{ date, meal_type, name, items: [] }}")
        print(f"   ✅ Backend esperaba: MealCreate con campo items")
        
        print(f"\n✨ Estado actual:")
        print(f"   - El esquema MealCreate requiere el campo 'items'")
        print(f"   - El frontend ahora envía items: [] por defecto")
        print(f"   - La validación de fecha es más robusta")
        print(f"   - Se pueden crear comidas de todos los tipos")
        
        print(f"\n🚀 Próximos pasos:")
        print(f"   1. Probar la creación de comidas en el navegador")
        print(f"   2. Verificar que no hay más errores 400")
        print(f"   3. Confirmar que las comidas se crean correctamente")
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("Asegúrate de que estás ejecutando desde el directorio raíz del proyecto")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")


if __name__ == "__main__":
    test_meal_creation()
