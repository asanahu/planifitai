#!/usr/bin/env python3
"""Test simplificado del sistema inteligente con mejor manejo de errores"""

import requests
import json
import time

def test_simple_generation():
    """Prueba simple de generación de 1 día."""
    
    print("🔄 PROBANDO GENERACIÓN SIMPLE (1 DÍA)")
    print("-" * 40)
    
    # Datos simples para 1 día
    data = {
        "days": 1,
        "goal": "maintain_weight", 
        "activity_level": "moderately_active",
        "preferences": {}
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            "http://localhost:8000/api/v1/ai/test-14-days-working", 
            json=data, 
            timeout=60
        )
        generation_time = time.time() - start_time
        
        print(f"✅ Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("status") == "SUCCESS":
                plan = result.get("plan", {})
                days = plan.get("days", [])
                targets = result.get("targets", {})
                
                print(f"✅ Plan generado en {generation_time:.1f} segundos")
                print(f"📊 Días: {len(days)}")
                print(f"🎯 Objetivos: {targets}")
                
                if days:
                    first_day = days[0]
                    meals = first_day.get("meals", [])
                    totals = first_day.get("totals", {})
                    
                    print(f"🍽️ Día {first_day.get('date')}:")
                    print(f"   - Comidas: {len(meals)}")
                    print(f"   - Totales: {totals}")
                    
                    for meal in meals:
                        items = meal.get("items", [])
                        meal_kcal = meal.get("meal_kcal", 0)
                        print(f"   - {meal.get('type')}: {len(items)} items, {meal_kcal} kcal")
                
                return True
            else:
                error = result.get("error", "Unknown error")
                print(f"❌ Error: {error}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_profile_analysis():
    """Prueba el análisis de perfil."""
    
    print(f"\n📊 PROBANDO ANÁLISIS DE PERFIL")
    print("-" * 40)
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/ai/test-smart-generation",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("status") == "success":
                analysis = result.get("profile_analysis", {})
                print(f"✅ Análisis exitoso:")
                print(f"   - BMR: {analysis.get('bmr', 0):.0f} kcal")
                print(f"   - TDEE: {analysis.get('tdee', 0):.0f} kcal")
                print(f"   - Objetivo: {analysis.get('target_calories', 0):.0f} kcal")
                print(f"   - Proteínas: {analysis.get('protein_g', 0):.0f} g")
                print(f"   - Carbohidratos: {analysis.get('carbs_g', 0):.0f} g")
                print(f"   - Grasas: {analysis.get('fat_g', 0):.0f} g")
                return True
            else:
                print(f"❌ Error: {result.get('message')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    print("🧪 PRUEBAS SIMPLIFICADAS DEL SISTEMA INTELIGENTE")
    print("=" * 50)
    
    # Prueba análisis de perfil
    profile_ok = test_profile_analysis()
    
    # Prueba generación simple
    generation_ok = test_simple_generation()
    
    print(f"\n" + "=" * 50)
    if profile_ok and generation_ok:
        print(f"🎉 TODAS LAS PRUEBAS EXITOSAS")
        print(f"✅ Sistema listo para usar")
    else:
        print(f"⚠️ ALGUNAS PRUEBAS FALLARON")
        if profile_ok:
            print(f"✅ Análisis de perfil: OK")
        else:
            print(f"❌ Análisis de perfil: FALLO")
        
        if generation_ok:
            print(f"✅ Generación de planes: OK")
        else:
            print(f"❌ Generación de planes: FALLO")
    
    print(f"=" * 50)
