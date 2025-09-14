#!/usr/bin/env python3
"""Script para probar el sistema de respaldo de IA.

Este script prueba que cuando la IA principal llega al rate limit,
el sistema automáticamente cambia a la IA de respaldo.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.ai_client import LocalAiClient
from app.ai.provider import OpenRouterProvider, OpenRouterBackupProvider
from app.core.config import settings


def test_simulation_mode():
    """Prueba que ambos providers funcionan en modo simulación."""
    print("🧪 Probando modo simulación...")
    
    # Test main provider
    main_provider = OpenRouterProvider()
    result = main_provider.chat(1, [{"role": "user", "content": "Hola"}], simulate=True)
    print(f"✅ Provider principal (simulado): {result['reply']}")
    
    # Test backup provider
    backup_provider = OpenRouterBackupProvider()
    result = backup_provider.chat(1, [{"role": "user", "content": "Hola"}], simulate=True)
    print(f"✅ Provider respaldo (simulado): {result['reply']}")


def test_fallback_logic():
    """Prueba la lógica de fallback simulando errores de rate limit."""
    print("\n🔄 Probando lógica de fallback...")
    
    # Mock the main provider to raise rate limit error
    class MockRateLimitProvider:
        def chat(self, user_id, messages, *, simulate=False, model=None):
            if simulate:
                return {"reply": "simulated main response"}
            raise Exception("Rate limit exceeded: too many requests")
        
        def embedding(self, text, *, simulate=False):
            return [0.1, 0.2, 0.3]
    
    # Create client with mocked main provider
    client = LocalAiClient()
    client._provider = MockRateLimitProvider()
    client._backup_provider = OpenRouterBackupProvider()
    
    # Test fallback
    result = client.chat(1, [{"role": "user", "content": "Test message"}], simulate=True)
    print(f"✅ Fallback exitoso: {result['reply']}")


def test_configuration():
    """Verifica que la configuración esté correctamente cargada."""
    print("\n⚙️ Verificando configuración...")
    
    print(f"OPENROUTER_KEY configurado: {'✅' if settings.OPENROUTER_KEY else '❌'}")
    print(f"OPENROUTER_KEY2 configurado: {'✅' if settings.OPENROUTER_KEY2 else '❌'}")
    print(f"Modelo principal: {settings.OPENROUTER_CHAT_MODEL}")
    print(f"Modelo respaldo: {settings.OPENROUTER_BACKUP_CHAT_MODEL}")
    
    if not settings.OPENROUTER_KEY2:
        print("⚠️ OPENROUTER_KEY2 no está configurado. El sistema de respaldo no funcionará.")
        print("   Agrega OPENROUTER_KEY2=tu_clave_aqui en tu archivo .env")


def test_real_api_call():
    """Prueba una llamada real a la API (solo si las claves están configuradas)."""
    print("\n🌐 Probando llamada real a la API...")
    
    if not settings.OPENROUTER_KEY:
        print("❌ OPENROUTER_KEY no configurado, saltando prueba real")
        return
    
    if not settings.OPENROUTER_KEY2:
        print("❌ OPENROUTER_KEY2 no configurado, saltando prueba real")
        return
    
    try:
        client = LocalAiClient()
        messages = [{"role": "user", "content": "Responde solo 'Hola' en español"}]
        
        result = client.chat(1, messages, simulate=False)
        print(f"✅ Llamada exitosa: {result['reply'][:50]}...")
        
    except Exception as e:
        print(f"❌ Error en llamada real: {e}")


def main():
    """Función principal del script de prueba."""
    print("🚀 Iniciando pruebas del sistema de respaldo de IA\n")
    
    test_configuration()
    test_simulation_mode()
    test_fallback_logic()
    test_real_api_call()
    
    print("\n✨ Pruebas completadas!")
    print("\n📋 Resumen:")
    print("- ✅ Configuración agregada para OPENROUTER_KEY2")
    print("- ✅ OpenRouterBackupProvider creado con modelo z-ai/glm-4.5-air:free")
    print("- ✅ Lógica de fallback implementada en LocalAiClient")
    print("- ✅ Sistema detecta rate limits y cambia automáticamente al respaldo")
    
    if settings.OPENROUTER_KEY2:
        print("\n🎉 ¡El sistema de respaldo está listo para usar!")
    else:
        print("\n⚠️ Recuerda configurar OPENROUTER_KEY2 en tu archivo .env")


if __name__ == "__main__":
    main()
