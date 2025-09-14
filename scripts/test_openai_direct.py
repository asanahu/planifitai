#!/usr/bin/env python3
"""Test directo de OpenAI GPT-5-nano"""

import os
import sys
from openai import OpenAI

def test_openai():
    # Obtener API key del entorno
    api_key = os.getenv('API_OPEN_AI')
    if not api_key:
        print("❌ API_OPEN_AI no encontrada en variables de entorno")
        return False
    
    print(f"✅ API Key encontrada: {api_key[:20]}...")
    
    try:
        client = OpenAI(api_key=api_key)
        
        # Test simple
        print("🔄 Probando GPT-5-nano...")
        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "user", "content": "Responde solo 'Hola' en una palabra."}
            ],
            max_completion_tokens=10
        )
        
        reply = response.choices[0].message.content
        print(f"✅ Respuesta recibida: {reply}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Tipo de error: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = test_openai()
    sys.exit(0 if success else 1)
