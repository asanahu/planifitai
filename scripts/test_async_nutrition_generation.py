#!/usr/bin/env python3
"""
Script de prueba para la nueva funcionalidad de generación asíncrona de planes nutricionales.

Este script prueba:
1. Generación asíncrona de planes de 14 días
2. Consulta de estado en tiempo real
3. Manejo de errores
4. Cancelación de tareas
"""

import asyncio
import httpx
import json
import time
from typing import Dict, Any


class NutritionPlanTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def test_async_generation(self) -> Dict[str, Any]:
        """Prueba la generación asíncrona de un plan nutricional."""
        print("🧪 Probando generación asíncrona de plan nutricional...")
        
        # Datos de prueba
        payload = {
            "days": 14,
            "preferences": {
                "diet": "omnivore",
                "allergies": "none",
                "goals": "maintain_weight"
            }
        }
        
        try:
            # Iniciar generación asíncrona
            print("📤 Iniciando generación asíncrona...")
            response = await self.client.post(
                f"{self.base_url}/ai/generate/nutrition-plan-14-days-async",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            task_id = result["task_id"]
            print(f"✅ Tarea iniciada: {task_id}")
            print(f"📊 Estado inicial: {result['status']}")
            print(f"⏱️ Tiempo estimado: {result.get('estimated_time', 'N/A')}")
            
            # Monitorear progreso
            return await self.monitor_task_progress(task_id)
            
        except httpx.HTTPError as e:
            print(f"❌ Error HTTP: {e}")
            return {"error": str(e)}
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return {"error": str(e)}
    
    async def monitor_task_progress(self, task_id: str) -> Dict[str, Any]:
        """Monitorea el progreso de una tarea en tiempo real."""
        print(f"👀 Monitoreando progreso de tarea {task_id}...")
        
        start_time = time.time()
        max_wait_time = 120  # 2 minutos máximo
        
        while time.time() - start_time < max_wait_time:
            try:
                # Consultar estado
                response = await self.client.get(
                    f"{self.base_url}/ai/generate/nutrition-plan-status/{task_id}"
                )
                response.raise_for_status()
                
                status = response.json()
                current_time = time.time() - start_time
                
                print(f"⏰ {current_time:.1f}s - Estado: {status['status']} - Progreso: {status.get('progress', 0)}%")
                
                if status.get('message'):
                    print(f"💬 Mensaje: {status['message']}")
                
                if status['status'] == 'SUCCESS':
                    print("🎉 ¡Plan generado exitosamente!")
                    return self.analyze_plan_result(status)
                
                elif status['status'] == 'FAILURE':
                    print(f"❌ Error en la generación: {status.get('error', 'Error desconocido')}")
                    return {"error": status.get('error', 'Error desconocido')}
                
                # Esperar antes de la siguiente consulta
                await asyncio.sleep(2)
                
            except httpx.HTTPError as e:
                print(f"❌ Error consultando estado: {e}")
                return {"error": str(e)}
            except Exception as e:
                print(f"❌ Error inesperado: {e}")
                return {"error": str(e)}
        
        print("⏰ Timeout alcanzado")
        return {"error": "Timeout"}
    
    def analyze_plan_result(self, status: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza el resultado del plan generado."""
        plan = status.get('plan', {})
        days = plan.get('days', [])
        targets = plan.get('targets', {})
        
        print(f"📅 Días generados: {len(days)}")
        print(f"🎯 Objetivos nutricionales:")
        print(f"   - Calorías: {targets.get('kcal', 'N/A')}")
        print(f"   - Proteína: {targets.get('protein_g', 'N/A')}g")
        print(f"   - Carbohidratos: {targets.get('carbs_g', 'N/A')}g")
        print(f"   - Grasas: {targets.get('fat_g', 'N/A')}g")
        
        # Analizar estructura del plan
        meal_types = set()
        total_meals = 0
        
        for day in days:
            meals = day.get('meals', [])
            total_meals += len(meals)
            for meal in meals:
                meal_types.add(meal.get('type', 'unknown'))
        
        print(f"🍽️ Total de comidas: {total_meals}")
        print(f"📋 Tipos de comidas: {', '.join(sorted(meal_types))}")
        
        # Verificar calidad del plan
        quality_score = self.calculate_plan_quality(plan)
        print(f"⭐ Calidad del plan: {quality_score}/10")
        
        return {
            "success": True,
            "days_generated": len(days),
            "total_meals": total_meals,
            "meal_types": list(meal_types),
            "targets": targets,
            "quality_score": quality_score,
            "strategy": status.get('strategy', 'unknown')
        }
    
    def calculate_plan_quality(self, plan: Dict[str, Any]) -> int:
        """Calcula una puntuación de calidad del plan (1-10)."""
        score = 0
        days = plan.get('days', [])
        
        if not days:
            return 0
        
        # Verificar que tenga 14 días
        if len(days) == 14:
            score += 2
        elif len(days) >= 7:
            score += 1
        
        # Verificar estructura de días
        for day in days:
            meals = day.get('meals', [])
            totals = day.get('totals', {})
            
            # Verificar que tenga comidas
            if len(meals) >= 3:  # breakfast, lunch, dinner
                score += 0.5
            
            # Verificar que tenga totales nutricionales
            if all(key in totals for key in ['kcal', 'protein_g', 'carbs_g', 'fat_g']):
                score += 0.5
            
            # Verificar que los valores sean realistas
            kcal = totals.get('kcal', 0)
            if 1000 <= kcal <= 4000:  # Rango realista de calorías
                score += 0.2
        
        return min(10, int(score))
    
    async def test_cancellation(self) -> Dict[str, Any]:
        """Prueba la cancelación de una tarea en progreso."""
        print("🧪 Probando cancelación de tarea...")
        
        # Iniciar una tarea
        payload = {"days": 14, "preferences": {}}
        response = await self.client.post(
            f"{self.base_url}/ai/generate/nutrition-plan-14-days-async",
            json=payload
        )
        response.raise_for_status()
        
        task_id = response.json()["task_id"]
        print(f"📤 Tarea iniciada para cancelación: {task_id}")
        
        # Esperar un poco para que empiece
        await asyncio.sleep(3)
        
        # Cancelar la tarea
        try:
            cancel_response = await self.client.delete(
                f"{self.base_url}/ai/generate/nutrition-plan-cancel/{task_id}"
            )
            cancel_response.raise_for_status()
            
            result = cancel_response.json()
            print(f"🛑 Resultado de cancelación: {result}")
            
            return {"success": True, "cancellation_result": result}
            
        except Exception as e:
            print(f"❌ Error cancelando tarea: {e}")
            return {"error": str(e)}
    
    async def run_all_tests(self):
        """Ejecuta todas las pruebas."""
        print("🚀 Iniciando pruebas de generación asíncrona de planes nutricionales")
        print("=" * 70)
        
        results = {}
        
        # Prueba 1: Generación asíncrona
        print("\n1️⃣ PRUEBA: Generación asíncrona")
        print("-" * 40)
        results["async_generation"] = await self.test_async_generation()
        
        # Prueba 2: Cancelación
        print("\n2️⃣ PRUEBA: Cancelación de tarea")
        print("-" * 40)
        results["cancellation"] = await self.test_cancellation()
        
        # Resumen
        print("\n📊 RESUMEN DE PRUEBAS")
        print("=" * 70)
        
        for test_name, result in results.items():
            if "error" in result:
                print(f"❌ {test_name}: FALLÓ - {result['error']}")
            else:
                print(f"✅ {test_name}: EXITOSO")
        
        await self.client.aclose()
        return results


async def main():
    """Función principal."""
    tester = NutritionPlanTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
