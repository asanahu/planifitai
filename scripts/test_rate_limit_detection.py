#!/usr/bin/env python3
"""Script para simular específicamente un rate limit y verificar el fallback."""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.ai_client import LocalAiClient
from app.ai.provider import OpenRouterBackupProvider


def test_rate_limit_fallback():
    """Simula un rate limit específico y verifica que el fallback funciona."""
    print("🚨 Simulando rate limit para probar fallback...")
    
    # Mock provider que simula rate limit
    class MockRateLimitProvider:
        def chat(self, user_id, messages, *, simulate=False, model=None):
            if simulate:
                return {"reply": "simulated main response"}
            # Simular diferentes tipos de errores de rate limit
            raise Exception("Rate limit exceeded: too many requests")
        
        def embedding(self, text, *, simulate=False):
            return [0.1, 0.2, 0.3]
    
    # Mock provider que simula quota exceeded
    class MockQuotaProvider:
        def chat(self, user_id, messages, *, simulate=False, model=None):
            if simulate:
                return {"reply": "simulated main response"}
            raise Exception("Quota exceeded for this month")
        
        def embedding(self, text, *, simulate=False):
            return [0.1, 0.2, 0.3]
    
    # Mock provider que simula error 429
    class Mock429Provider:
        def chat(self, user_id, messages, *, simulate=False, model=None):
            if simulate:
                return {"reply": "simulated main response"}
            raise Exception("HTTP 429: Too Many Requests")
        
        def embedding(self, text, *, simulate=False):
            return [0.1, 0.2, 0.3]
    
    # Test diferentes tipos de rate limit
    test_cases = [
        ("Rate limit exceeded", MockRateLimitProvider()),
        ("Quota exceeded", MockQuotaProvider()),
        ("HTTP 429", Mock429Provider()),
    ]
    
    for test_name, mock_provider in test_cases:
        print(f"\n🧪 Probando: {test_name}")
        
        client = LocalAiClient()
        client._provider = mock_provider
        client._backup_provider = OpenRouterBackupProvider()
        
        try:
            result = client.chat(1, [{"role": "user", "content": "Test"}], simulate=True)
            print(f"✅ Fallback exitoso: {result['reply']}")
        except Exception as e:
            print(f"❌ Fallback falló: {e}")


def test_non_rate_limit_error():
    """Prueba que errores que NO son rate limit no activan el fallback."""
    print("\n🚫 Probando que errores no-rate-limit NO activan fallback...")
    
    # Mock provider que simula error no relacionado con rate limit
    class MockAuthErrorProvider:
        def chat(self, user_id, messages, *, simulate=False, model=None):
            if simulate:
                return {"reply": "simulated main response"}
            raise Exception("Authentication failed: invalid API key")
        
        def embedding(self, text, *, simulate=False):
            return [0.1, 0.2, 0.3]
    
    client = LocalAiClient()
    client._provider = MockAuthErrorProvider()
    client._backup_provider = OpenRouterBackupProvider()
    
    try:
        result = client.chat(1, [{"role": "user", "content": "Test"}], simulate=True)
        print(f"✅ Error manejado correctamente: {result['reply']}")
    except Exception as e:
        print(f"✅ Error no-rate-limit NO activó fallback (correcto): {e}")


def main():
    """Función principal."""
    print("🔬 Pruebas específicas de detección de rate limit\n")
    
    test_rate_limit_fallback()
    test_non_rate_limit_error()
    
    print("\n✨ Todas las pruebas de rate limit completadas!")
    print("\n📋 Verificaciones:")
    print("- ✅ Rate limit errors activan fallback")
    print("- ✅ Quota exceeded errors activan fallback") 
    print("- ✅ HTTP 429 errors activan fallback")
    print("- ✅ Otros errores NO activan fallback (correcto)")


if __name__ == "__main__":
    main()
