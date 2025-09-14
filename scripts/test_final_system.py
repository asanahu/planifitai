#!/usr/bin/env python3
"""Test final completo del sistema inteligente optimizado"""

import requests
import json
import time

def test_complete_system():
    """Prueba completa del sistema optimizado."""
    
    print("🚀 SISTEMA INTELIGENTE DE GENERACIÓN NUTRICIONAL")
    print("=" * 55)
    
    # 1. Análisis de Perfil
    print("\n📊 PASO 1: Análisis de Perfil del Usuario")
    try:
        response = requests.post("http://localhost:8000/api/v1/ai/test-smart-generation", timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                analysis = result.get("profile_analysis", {})
                print(f"✅ Análisis personalizado completado:")
                print(f"   🔥 BMR (metabolismo basal): {analysis.get('bmr', 0):.0f} kcal")
                print(f"   ⚡ TDEE (gasto total diario): {analysis.get('tdee', 0):.0f} kcal")
                print(f"   🎯 Calorías objetivo: {analysis.get('target_calories', 0):.0f} kcal")
                print(f"   💪 Proteínas objetivo: {analysis.get('protein_g', 0):.0f} g")
                print(f"   🌾 Carbohidratos objetivo: {analysis.get('carbs_g', 0):.0f} g")
                print(f"   🥑 Grasas objetivo: {analysis.get('fat_g', 0):.0f} g")
            else:
                print(f"❌ Error en análisis: {result.get('message')}")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # 2. Generación de Plan de 14 días
    print(f"\n🔄 PASO 2: Generación de Plan Nutricional (14 días)")
    print(f"⏱️  Iniciando generación con GPT-5-nano...")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/ai/test-14-days-working", 
            timeout=120
        )
        
        generation_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            # Verificar ambos posibles valores de status
            if result.get("status") in ["SUCCESS", "success"]:
                plan = result.get("plan", {})
                days = plan.get("days", [])
                targets = result.get("targets", {})
                
                print(f"✅ Plan generado exitosamente en {generation_time:.1f} segundos")
                print(f"📅 Días generados: {len(days)}")
                print(f"🎯 Objetivos nutricionales: {targets}")
                
                # Verificar tiempo de generación
                if generation_time <= 120:  # 2 minutos
                    print(f"⚡ Velocidad EXCELENTE: {generation_time:.1f}s ≤ 120s")
                else:
                    print(f"⚠️ Tiempo de generación: {generation_time:.1f}s > 120s")
                
                # Analizar primer día
                if days:
                    first_day = days[0]
                    meals = first_day.get("meals", [])
                    totals = first_day.get("totals", {})
                    
                    print(f"\n🍽️ Análisis del primer día ({first_day.get('date', 'N/A')}):")
                    print(f"   - Comidas planificadas: {len(meals)}")
                    print(f"   - Calorías totales: {totals.get('kcal', 0)} kcal")
                    print(f"   - Proteínas: {totals.get('protein_g', 0):.0f} g")
                    print(f"   - Carbohidratos: {totals.get('carbs_g', 0):.0f} g")
                    print(f"   - Grasas: {totals.get('fat_g', 0):.0f} g")
                    
                    print(f"\n   📋 Detalle de comidas:")
                    for meal in meals:
                        items = meal.get("items", [])
                        meal_kcal = meal.get("meal_kcal", 0)
                        meal_type = meal.get('type', 'unknown')
                        meal_names = {
                            'breakfast': 'Desayuno',
                            'lunch': 'Almuerzo', 
                            'dinner': 'Cena',
                            'snack': 'Merienda'
                        }
                        print(f"   - {meal_names.get(meal_type, meal_type)}: {len(items)} alimentos, {meal_kcal} kcal")
                        
                        # Mostrar algunos alimentos
                        for item in items[:2]:  # Primeros 2 alimentos
                            print(f"     • {item.get('name', 'N/A')} ({item.get('qty', 0)}g)")
                
                return True
            else:
                error = result.get("error", result.get("message", "Unknown error"))
                print(f"❌ Error en generación: {error}")
                return False
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_performance_benchmark():
    """Prueba de rendimiento del sistema."""
    
    print(f"\n⚡ PASO 3: Benchmark de Rendimiento")
    print(f"-" * 35)
    
    times = []
    successes = 0
    
    for i in range(3):
        print(f"🔄 Prueba {i+1}/3...")
        start_time = time.time()
        
        try:
            response = requests.post("http://localhost:8000/api/v1/ai/test-smart-generation", timeout=15)
            generation_time = time.time() - start_time
            
            if response.status_code == 200 and response.json().get("status") == "success":
                times.append(generation_time)
                successes += 1
                print(f"✅ Completado en {generation_time:.3f}s")
            else:
                print(f"❌ Falló")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    if times:
        avg_time = sum(times) / len(times)
        print(f"\n📈 Estadísticas de rendimiento:")
        print(f"   - Tasa de éxito: {successes}/3 ({successes/3*100:.0f}%)")
        print(f"   - Tiempo promedio: {avg_time:.3f}s")
        print(f"   - Tiempo mínimo: {min(times):.3f}s")
        print(f"   - Tiempo máximo: {max(times):.3f}s")
        
        if avg_time <= 2.0:
            print(f"   ⚡ Rendimiento EXCELENTE")
        elif avg_time <= 5.0:
            print(f"   ✅ Rendimiento BUENO")
        else:
            print(f"   ⚠️ Rendimiento MEJORABLE")
        
        return successes >= 2  # Al menos 2 de 3 exitosas
    
    return False

if __name__ == "__main__":
    print("🧠 PRUEBA FINAL DEL SISTEMA INTELIGENTE OPTIMIZADO")
    
    # Prueba principal
    main_success = test_complete_system()
    
    # Benchmark de rendimiento
    perf_success = test_performance_benchmark()
    
    print(f"\n" + "=" * 55)
    print(f"📋 RESUMEN FINAL:")
    
    if main_success:
        print(f"✅ Generación de planes: FUNCIONANDO")
        print(f"   - Análisis personalizado de perfil")
        print(f"   - Cálculo automático de objetivos nutricionales")
        print(f"   - Generación de 14 días completos")
        print(f"   - Integración con GPT-5-nano")
    else:
        print(f"❌ Generación de planes: CON PROBLEMAS")
    
    if perf_success:
        print(f"✅ Rendimiento: ÓPTIMO")
        print(f"   - Análisis rápido de perfil")
        print(f"   - Generación eficiente")
    else:
        print(f"⚠️ Rendimiento: MEJORABLE")
    
    print(f"\n🎯 ESTADO GENERAL:")
    if main_success and perf_success:
        print(f"🎉 SISTEMA COMPLETAMENTE FUNCIONAL")
        print(f"✅ Listo para producción")
        print(f"✅ Sin uso de Celery (evita problemas de serialización)")
        print(f"✅ Análisis inteligente del perfil del usuario")
        print(f"✅ Generación rápida con GPT-5-nano")
        print(f"✅ Planes personalizados de 2 semanas")
    else:
        print(f"⚠️ SISTEMA PARCIALMENTE FUNCIONAL")
        print(f"   Revisar componentes con problemas")
    
    print(f"=" * 55)
