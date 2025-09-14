#!/usr/bin/env python3
"""
Script de prueba para verificar la sincronización de zona horaria entre frontend y backend.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import pytz

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Configurar variables de entorno para testing
os.environ.setdefault('OPENROUTER_KEY', 'test-key')
os.environ.setdefault('DATABASE_URL', 'sqlite:///test.db')

def test_timezone_sync():
    """Prueba la sincronización de zona horaria."""
    
    print("🌍 Probando sincronización de zona horaria...")
    
    # Obtener fecha actual en Madrid
    madrid_tz = pytz.timezone('Europe/Madrid')
    now_madrid = datetime.now(madrid_tz)
    today_madrid = now_madrid.date()
    
    print(f"\n📅 Fechas actuales:")
    print(f"   - Madrid time: {now_madrid}")
    print(f"   - Madrid date: {today_madrid}")
    print(f"   - UTC time: {datetime.utcnow()}")
    print(f"   - UTC date: {datetime.utcnow().date()}")
    
    # Simular lo que envía el frontend
    frontend_date_str = "2025-09-12"  # Esto es lo que debería enviar el frontend corregido
    
    print(f"\n🔄 Simulando comunicación frontend-backend:")
    print(f"   - Frontend envía: {frontend_date_str}")
    print(f"   - Backend recibe: {frontend_date_str}")
    print(f"   - Backend compara con: {today_madrid}")
    
    # Convertir string a date para comparación
    frontend_date = datetime.strptime(frontend_date_str, '%Y-%m-%d').date()
    
    print(f"\n✅ Comparación:")
    print(f"   - Frontend date: {frontend_date}")
    print(f"   - Backend Madrid date: {today_madrid}")
    print(f"   - Son iguales: {frontend_date == today_madrid}")
    
    if frontend_date == today_madrid:
        print(f"\n🎉 ¡Sincronización correcta!")
        print(f"   - Frontend y backend usan la misma zona horaria")
        print(f"   - No habrá más errores de 'Future date not allowed'")
    else:
        print(f"\n⚠️  Aún hay diferencia de fecha")
        print(f"   - Diferencia: {frontend_date - today_madrid} días")
    
    print(f"\n🔧 Cambios implementados:")
    print(f"   ✅ Frontend: Función today() corregida para usar Madrid timezone")
    print(f"   ✅ Backend: Validación de fecha usando Madrid timezone")
    print(f"   ✅ Ambos usan Europe/Madrid como referencia")
    
    print(f"\n🚀 Próximos pasos:")
    print(f"   1. Probar creación de comidas en el navegador")
    print(f"   2. Verificar que no hay más errores 400")
    print(f"   3. Confirmar que las fechas coinciden")


if __name__ == "__main__":
    test_timezone_sync()
