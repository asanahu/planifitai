#!/usr/bin/env python3
"""Test específico del smart generator para verificar generación de 14 días"""

import requests
import json

def test_smart_generator():
    """Prueba específica del smart generator."""
    
    print("🧠 PROBANDO SMART GENERATOR")
    print("=" * 35)
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/ai/test-smart-generation",
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("status") == "success":
                analysis = result.get("profile_analysis", {})
                print(f"✅ Análisis de perfil funcionando:")
                print(f"   - BMR: {analysis.get('bmr', 0):.0f} kcal")
                print(f"   - TDEE: {analysis.get('tdee', 0):.0f} kcal")
                print(f"   - Objetivo: {analysis.get('target_calories', 0):.0f} kcal")
                
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

def test_full_generation():
    """Prueba la generación completa de 14 días."""
    
    print(f"\n🔄 PROBANDO GENERACIÓN COMPLETA DE 14 DÍAS")
    print("-" * 45)
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/ai/test-web-generation",
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("status") == "SUCCESS":
                plan = result.get("plan", {})
                days = plan.get("days", [])
                targets = result.get("targets", {})
                
                print(f"✅ Generación exitosa:")
                print(f"   📅 Días generados: {len(days)}")
                print(f"   🎯 Objetivos: {targets}")
                
                if len(days) == 14:
                    print(f"✅ CORRECTO: Se generaron exactamente 14 días")
                    
                    # Verificar que cada día tiene comidas
                    days_with_meals = 0
                    total_meals = 0
                    
                    for i, day in enumerate(days):
                        meals = day.get("meals", [])
                        if meals:
                            days_with_meals += 1
                            total_meals += len(meals)
                    
                    print(f"   🍽️ Días con comidas: {days_with_meals}/{len(days)}")
                    print(f"   📊 Total de comidas: {total_meals}")
                    
                    if days_with_meals == 14 and total_meals >= 40:  # Al menos ~3 comidas por día
                        print(f"✅ PERFECTO: Todos los días tienen comidas")
                        return True
                    else:
                        print(f"⚠️ PROBLEMA: Algunos días sin comidas suficientes")
                        return False
                else:
                    print(f"❌ PROBLEMA: Se generaron {len(days)} días en lugar de 14")
                    return False
            else:
                error = result.get("error", result.get("message", "Unknown error"))
                print(f"❌ Error: {error}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    print("🔍 DIAGNÓSTICO DEL PROBLEMA DE 0 DÍAS")
    
    # Test 1: Smart generator
    smart_ok = test_smart_generator()
    
    # Test 2: Generación completa
    generation_ok = test_full_generation()
    
    print(f"\n" + "=" * 45)
    print(f"📋 DIAGNÓSTICO FINAL:")
    
    if smart_ok:
        print(f"✅ Smart Generator: FUNCIONANDO")
    else:
        print(f"❌ Smart Generator: CON PROBLEMAS")
    
    if generation_ok:
        print(f"✅ Generación de 14 días: FUNCIONANDO")
        print(f"   El problema puede estar en la interfaz web")
        print(f"   o en el endpoint con autenticación")
    else:
        print(f"❌ Generación de 14 días: CON PROBLEMAS")
        print(f"   El problema está en el backend")
    
    print(f"\n🎯 CONCLUSIÓN:")
    if smart_ok and generation_ok:
        print(f"✅ BACKEND FUNCIONANDO CORRECTAMENTE")
        print(f"   El problema está en la interfaz web o autenticación")
    else:
        print(f"❌ PROBLEMA EN EL BACKEND")
        print(f"   Necesita corrección en el generador")
    
    print(f"=" * 45)
