# 🛠️ Solución de Problemas - Generación Asíncrona de Planes Nutricionales

## 🚨 **Problema Reportado**

```
Access to fetch at 'http://localhost:8000/api/v1/ai/generate/nutrition-plan-status/...' 
from origin 'http://localhost:5173' has been blocked by CORS policy: 
No 'Access-Control-Allow-Origin' header is present on the requested resource.

GET http://localhost:8000/api/v1/ai/generate/nutrition-plan-status/... 
net::ERR_FAILED 500 (Internal Server Error)
```

## 🔍 **Análisis del Problema**

Este error indica **dos problemas separados**:

1. **Error CORS**: El navegador bloquea la petición por políticas CORS
2. **Error 500**: El servidor devuelve un error interno al procesar la petición

## ✅ **Soluciones Implementadas**

### **1. Archivo de Tipos Faltante**
- ✅ Creado `web/src/types/nutrition.ts` con las interfaces necesarias

### **2. Corrección del Error 500**
- ✅ Mejorado el endpoint `/ai/generate/nutrition-plan-status/{task_id}`
- ✅ Agregado manejo de errores robusto
- ✅ Configuración correcta de AsyncResult con la instancia de Celery

### **3. Endpoints de Diagnóstico**
- ✅ Agregado `/ai/test-celery` para probar Celery
- ✅ Agregado `/ai/test-nutrition-task` para probar tareas de nutrición

### **4. Script de Diagnóstico**
- ✅ Creado `scripts/diagnose_nutrition_system.py` para diagnóstico completo

## 🚀 **Pasos para Resolver**

### **Paso 1: Verificar Servicios**
```bash
# Asegúrate de que todos los servicios estén ejecutándose
docker-compose up --build

# Verificar que el worker de Celery esté activo
docker-compose logs worker
```

### **Paso 2: Ejecutar Diagnóstico**
```bash
# Ejecutar script de diagnóstico
python scripts/diagnose_nutrition_system.py
```

### **Paso 3: Probar Endpoints Individualmente**

#### **Probar Celery**
```bash
curl http://localhost:8000/ai/test-celery
```

**Respuesta esperada:**
```json
{
  "status": "success",
  "message": "Celery está funcionando",
  "task_id": "abc123...",
  "celery_configured": true
}
```

#### **Probar Tareas de Nutrición**
```bash
curl http://localhost:8000/ai/test-nutrition-task
```

**Respuesta esperada:**
```json
{
  "status": "success",
  "message": "Tarea de nutrición registrada correctamente",
  "task_id": "def456...",
  "nutrition_tasks_available": true
}
```

#### **Probar Generación Asíncrona**
```bash
# Iniciar generación
curl -X POST http://localhost:8000/ai/generate/nutrition-plan-async \
  -H "Content-Type: application/json" \
  -d '{"days": 1, "preferences": {}}'

# Consultar estado (reemplaza TASK_ID)
curl http://localhost:8000/ai/generate/nutrition-plan-status/TASK_ID
```

### **Paso 4: Verificar Logs**

#### **Logs del Worker**
```bash
docker-compose logs -f worker
```

#### **Logs de la Aplicación**
```bash
docker-compose logs -f web
```

#### **Logs de Redis**
```bash
docker-compose logs -f redis
```

## 🔧 **Configuración Requerida**

### **Variables de Entorno**
```bash
# En .env o docker-compose.yml
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
OPENROUTER_KEY=tu_clave_openrouter
```

### **Servicios Necesarios**
```yaml
# docker-compose.yml debe incluir:
services:
  web:      # API principal
  worker:   # Worker de Celery
  redis:    # Broker de Celery
  db:       # Base de datos
```

## 🚨 **Problemas Comunes y Soluciones**

### **Problema: "Celery no configurado"**
**Causa**: Worker de Celery no está ejecutándose
**Solución**:
```bash
docker-compose up worker
```

### **Problema: "Tareas de nutrición no disponibles"**
**Causa**: Las tareas no están registradas en Celery
**Solución**:
```bash
# Verificar que app/background/celery_app.py incluya:
include=["app.background.tasks", "app.background.nutrition_tasks"]
```

### **Problema: "Error 500 en status endpoint"**
**Causa**: AsyncResult no configurado correctamente
**Solución**: Ya corregido en la implementación

### **Problema: "CORS bloqueado"**
**Causa**: Configuración CORS incorrecta
**Solución**: Ya configurado en app/main.py

### **Problema: "Timeout en polling"**
**Causa**: Tarea tarda demasiado o falla
**Solución**: 
- Verificar logs del worker
- Probar con `days: 1` primero
- Verificar configuración de OpenRouter

## 📊 **Verificación de Funcionamiento**

### **Flujo Completo de Prueba**
1. ✅ API responde (`/ai/echo`)
2. ✅ Celery funciona (`/ai/test-celery`)
3. ✅ Tareas registradas (`/ai/test-nutrition-task`)
4. ✅ Generación inicia (`/ai/generate/nutrition-plan-async`)
5. ✅ Estado consultable (`/ai/generate/nutrition-plan-status/{id}`)
6. ✅ Frontend puede hacer polling
7. ✅ Plan se genera correctamente

### **Indicadores de Éxito**
- Task ID se genera correctamente
- Estado cambia de PENDING → PROGRESS → SUCCESS
- Plan contiene 14 días con estructura correcta
- Frontend muestra progreso en tiempo real

## 🎯 **Próximos Pasos**

Si el diagnóstico falla:

1. **Revisar logs** para errores específicos
2. **Verificar configuración** de Redis y Celery
3. **Probar con datos mínimos** (days: 1)
4. **Verificar conectividad** entre servicios
5. **Reiniciar servicios** si es necesario

## 📞 **Soporte Adicional**

Si los problemas persisten:

1. Ejecutar el script de diagnóstico completo
2. Recopilar logs de todos los servicios
3. Probar endpoints individualmente
4. Verificar configuración de red y puertos

La implementación está diseñada para ser robusta y proporcionar información detallada sobre cualquier problema que pueda surgir.
