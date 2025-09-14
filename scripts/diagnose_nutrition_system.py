#!/usr/bin/env python3
"""
Script de diagnóstico para problemas con la generación asíncrona de planes nutricionales.

Este script verifica:
1. Conectividad con la API
2. Configuración de Celery
3. Estado de Redis
4. Registro de tareas
"""

import asyncio
import httpx
import json
import sys
from typing import Dict, Any


class NutritionDiagnostic:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def run_diagnostics(self) -> Dict[str, Any]:
        """Ejecuta todos los diagnósticos."""
        print("🔍 DIAGNÓSTICO DEL SISTEMA DE GENERACIÓN ASÍNCRONA")
        print("=" * 60)
        
        results = {}
        
        # Diagnóstico 1: Conectividad básica
        print("\n1️⃣ DIAGNÓSTICO: Conectividad básica")
        print("-" * 40)
        results["connectivity"] = await self.test_connectivity()
        
        # Diagnóstico 2: Configuración de Celery
        print("\n2️⃣ DIAGNÓSTICO: Configuración de Celery")
        print("-" * 40)
        results["celery"] = await self.test_celery()
        
        # Diagnóstico 3: Tareas de nutrición
        print("\n3️⃣ DIAGNÓSTICO: Tareas de nutrición")
        print("-" * 40)
        results["nutrition_tasks"] = await self.test_nutrition_tasks()
        
        # Diagnóstico 4: Generación asíncrona completa
        print("\n4️⃣ DIAGNÓSTICO: Generación asíncrona completa")
        print("-" * 40)
        results["async_generation"] = await self.test_async_generation()
        
        # Resumen
        print("\n📊 RESUMEN DE DIAGNÓSTICOS")
        print("=" * 60)
        
        all_passed = True
        for test_name, result in results.items():
            if result.get("status") == "success":
                print(f"✅ {test_name}: EXITOSO")
            else:
                print(f"❌ {test_name}: FALLÓ - {result.get('message', 'Error desconocido')}")
                all_passed = False
        
        if all_passed:
            print("\n🎉 ¡Todos los diagnósticos pasaron! El sistema está funcionando correctamente.")
        else:
            print("\n⚠️ Algunos diagnósticos fallaron. Revisa los errores arriba.")
        
        await self.client.aclose()
        return results
    
    async def test_connectivity(self) -> Dict[str, Any]:
        """Prueba la conectividad básica con la API."""
        try:
            response = await self.client.get(f"{self.base_url}/ai/echo")
            response.raise_for_status()
            
            print("✅ API respondiendo correctamente")
            return {"status": "success", "message": "API accesible"}
            
        except httpx.ConnectError:
            print("❌ No se puede conectar a la API")
            return {"status": "error", "message": "API no accesible - verifica que el servidor esté ejecutándose"}
        except httpx.HTTPError as e:
            print(f"❌ Error HTTP: {e}")
            return {"status": "error", "message": f"Error HTTP: {e}"}
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return {"status": "error", "message": f"Error inesperado: {e}"}
    
    async def test_celery(self) -> Dict[str, Any]:
        """Prueba la configuración de Celery."""
        try:
            response = await self.client.get(f"{self.base_url}/ai/test-celery")
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("celery_configured"):
                print("✅ Celery configurado correctamente")
                print(f"   Task ID: {result.get('task_id')}")
                return {"status": "success", "message": "Celery funcionando", "task_id": result.get("task_id")}
            else:
                print("❌ Celery no configurado correctamente")
                return {"status": "error", "message": result.get("message", "Celery no configurado")}
                
        except httpx.HTTPError as e:
            print(f"❌ Error HTTP: {e}")
            return {"status": "error", "message": f"Error HTTP: {e}"}
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return {"status": "error", "message": f"Error inesperado: {e}"}
    
    async def test_nutrition_tasks(self) -> Dict[str, Any]:
        """Prueba las tareas de nutrición específicas."""
        try:
            response = await self.client.get(f"{self.base_url}/ai/test-nutrition-task")
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("nutrition_tasks_available"):
                print("✅ Tareas de nutrición registradas correctamente")
                print(f"   Task ID: {result.get('task_id')}")
                return {"status": "success", "message": "Tareas de nutrición disponibles", "task_id": result.get("task_id")}
            else:
                print("❌ Tareas de nutrición no disponibles")
                return {"status": "error", "message": result.get("message", "Tareas de nutrición no disponibles")}
                
        except httpx.HTTPError as e:
            print(f"❌ Error HTTP: {e}")
            return {"status": "error", "message": f"Error HTTP: {e}"}
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return {"status": "error", "message": f"Error inesperado: {e}"}
    
    async def test_async_generation(self) -> Dict[str, Any]:
        """Prueba la generación asíncrona completa."""
        try:
            # Iniciar generación
            payload = {"days": 1, "preferences": {}}
            response = await self.client.post(
                f"{self.base_url}/ai/generate/nutrition-plan-async",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            task_id = result.get("task_id")
            
            if not task_id:
                print("❌ No se recibió task_id")
                return {"status": "error", "message": "No se recibió task_id"}
            
            print(f"✅ Generación iniciada - Task ID: {task_id}")
            
            # Consultar estado
            status_response = await self.client.get(
                f"{self.base_url}/ai/generate/nutrition-plan-status/{task_id}"
            )
            status_response.raise_for_status()
            
            status = status_response.json()
            print(f"✅ Estado consultado: {status.get('status')}")
            
            return {
                "status": "success", 
                "message": "Generación asíncrona funcionando",
                "task_id": task_id,
                "initial_status": status.get("status")
            }
            
        except httpx.HTTPError as e:
            print(f"❌ Error HTTP: {e}")
            return {"status": "error", "message": f"Error HTTP: {e}"}
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return {"status": "error", "message": f"Error inesperado: {e}"}


async def main():
    """Función principal."""
    diagnostic = NutritionDiagnostic()
    await diagnostic.run_diagnostics()


if __name__ == "__main__":
    asyncio.run(main())
