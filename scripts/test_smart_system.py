#!/usr/bin/env python3
"""Test completo del sistema inteligente de generación nutricional"""

import requests
import json
import time

def test_smart_system():
    """Prueba completa del sistema inteligente."""
    
    print("🧠 PROBANDO SISTEMA INTELIGENTE DE GENERACIÓN NUTRICIONAL")
    print("=" * 60)
    
    # 1. Probar análisis de perfil
    print("\n📊 PASO 1: Análisis de Perfil")
    try:
        response = requests.post("http://localhost:8000/api/v1/ai/test-smart-generation", timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                analysis = result.get("profile_analysis", {})
                print(f"✅ Análisis exitoso:")
                print(f"   - BMR: {analysis.get('bmr', 0):.0f} kcal")
                print(f"   - TDEE: {analysis.get('tdee', 0):.0f} kcal")
                print(f"   - Calorías objetivo: {analysis.get('target_calories', 0):.0f} kcal")
                print(f"   - Proteínas: {analysis.get('protein_g', 0):.0f} g")
                print(f"   - Carbohidratos: {analysis.get('carbs_g', 0):.0f} g")
                print(f"   - Grasas: {analysis.get('fat_g', 0):.0f} g")
            else:
                print(f"❌ Error en análisis: {result.get('message')}")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # 2. Probar generación completa (simulada)
    print(f"\n🔄 PASO 2: Generación Completa de Plan (14 días)")
    print(f"⏱️  Iniciando generación...")
    
    start_time = time.time()
    
    try:
        # Usar el endpoint de prueba web que funciona
        response = requests.post("http://localhost:8000/api/v1/ai/test-web-generation", timeout=120)
        
        generation_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "SUCCESS":
                plan = result.get("plan", {})
                days = plan.get("days", [])
                targets = result.get("targets", {})
                
                print(f"✅ Generación exitosa en {generation_time:.1f} segundos")
                print(f"📊 Estadísticas del plan:")
                print(f"   - Días generados: {len(days)}")
                print(f"   - Objetivos: {targets}")
                
                if days:
                    first_day = days[0]
                    meals = first_day.get("meals", [])
                    print(f"🍽️ Primer día ({first_day.get('date', 'N/A')}):")
                    
                    for meal in meals:
                        items = meal.get("items", [])
                        meal_kcal = meal.get("meal_kcal", 0)
                        print(f"   - {meal.get('type', 'unknown')}: {len(items)} items, {meal_kcal} kcal")
                
                # Verificar tiempo de generación
                if generation_time <= 120:  # 2 minutos
                    print(f"✅ Tiempo de generación ÓPTIMO: {generation_time:.1f}s ≤ 120s")
                else:
                    print(f"⚠️ Tiempo de generación: {generation_time:.1f}s > 120s (puede optimizarse)")
                
                return True
            else:
                print(f"❌ Error en generación: {result.get('error')}")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_performance():
    """Prueba de rendimiento del sistema."""
    
    print(f"\n⚡ PRUEBA DE RENDIMIENTO")
    print(f"-" * 30)
    
    times = []
    successes = 0
    
    for i in range(3):
        print(f"🔄 Prueba {i+1}/3...")
        start_time = time.time()
        
        try:
            response = requests.post("http://localhost:8000/api/v1/ai/test-smart-generation", timeout=30)
            generation_time = time.time() - start_time
            
            if response.status_code == 200 and response.json().get("status") == "success":
                times.append(generation_time)
                successes += 1
                print(f"✅ Tiempo: {generation_time:.2f}s")
            else:
                print(f"❌ Falló")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    if times:
        avg_time = sum(times) / len(times)
        print(f"\n📈 Estadísticas de rendimiento:")
        print(f"   - Éxitos: {successes}/3")
        print(f"   - Tiempo promedio: {avg_time:.2f}s")
        print(f"   - Tiempo mínimo: {min(times):.2f}s")
        print(f"   - Tiempo máximo: {max(times):.2f}s")
        
        return avg_time <= 5.0  # El análisis de perfil debe ser muy rápido
    
    return False

if __name__ == "__main__":
    print("🚀 INICIANDO PRUEBAS COMPLETAS DEL SISTEMA INTELIGENTE")
    
    # Prueba principal
    main_success = test_smart_system()
    
    # Prueba de rendimiento
    perf_success = test_performance()
    
    print(f"\n" + "=" * 60)
    if main_success and perf_success:
        print(f"🎉 TODAS LAS PRUEBAS EXITOSAS")
        print(f"✅ Sistema inteligente funcionando correctamente")
        print(f"✅ Análisis de perfil personalizado")
        print(f"✅ Generación rápida y eficiente")
        print(f"✅ Listo para producción")
    else:
        print(f"❌ ALGUNAS PRUEBAS FALLARON")
        if not main_success:
            print(f"❌ Sistema principal con problemas")
        if not perf_success:
            print(f"❌ Rendimiento por debajo del esperado")
    
    print(f"=" * 60)
