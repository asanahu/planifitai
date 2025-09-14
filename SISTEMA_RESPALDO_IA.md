# Sistema de Respaldo de IA

## Descripción

Se ha implementado un sistema de respaldo automático para la IA que detecta cuando la IA principal llega al rate limit y automáticamente cambia a una segunda IA de respaldo.

## Configuración

### Variables de Entorno

Agrega estas variables a tu archivo `.env`:

```env
# IA Principal (DeepSeek V3.1 free)
OPENROUTER_KEY=tu_clave_principal_aqui

# IA de Respaldo (GLM-4.5 Air free) 
OPENROUTER_KEY2=tu_clave_respaldo_aqui
```

### Modelos Utilizados

- **IA Principal**: `deepseek/deepseek-chat-v3.1:free`
- **IA Respaldo**: `z-ai/glm-4.5-air:free`

## Funcionamiento

### Detección Automática de Rate Limit

El sistema detecta automáticamente los siguientes tipos de errores que indican rate limit:

- `rate limit`
- `too many requests`
- `quota exceeded`
- `429` (código HTTP)
- `limit exceeded`
- `throttled`

### Flujo de Fallback

1. **Intento Principal**: Se intenta usar la IA principal (DeepSeek)
2. **Detección de Error**: Si hay un error de rate limit, se detecta automáticamente
3. **Cambio Automático**: Se cambia a la IA de respaldo (GLM-4.5 Air)
4. **Continuidad**: El usuario no nota la diferencia, el servicio continúa normalmente

### Casos de Uso

- ✅ **Rate limit**: Cambia automáticamente al respaldo
- ✅ **Quota exceeded**: Cambia automáticamente al respaldo  
- ✅ **HTTP 429**: Cambia automáticamente al respaldo
- ❌ **Errores de autenticación**: NO cambia (error real que debe solucionarse)
- ❌ **Errores de red**: NO cambia (problema temporal)

## Archivos Modificados

### `app/core/config.py`
- Agregada configuración `OPENROUTER_KEY2`
- Agregada configuración `OPENROUTER_BACKUP_CHAT_MODEL`

### `app/ai/provider.py`
- Nueva clase `OpenRouterBackupProvider`
- Implementa el mismo interfaz que `OpenRouterProvider`
- Usa la clave de respaldo y modelo GLM-4.5 Air

### `app/ai_client.py`
- Modificada clase `LocalAiClient`
- Implementada lógica de detección de rate limit
- Implementada lógica de fallback automático

## Pruebas

### Scripts de Prueba

Se crearon dos scripts para verificar el funcionamiento:

1. **`scripts/test_ai_fallback.py`**: Prueba general del sistema
2. **`scripts/test_rate_limit_detection.py`**: Prueba específica de detección de rate limit

### Ejecutar Pruebas

```bash
python scripts/test_ai_fallback.py
python scripts/test_rate_limit_detection.py
```

## Ventajas

- **Transparente**: El usuario no nota el cambio
- **Automático**: No requiere intervención manual
- **Robusto**: Detecta múltiples tipos de rate limit
- **Eficiente**: Solo cambia cuando es necesario
- **Gratuito**: Ambos modelos son gratuitos

## Monitoreo

El sistema registra automáticamente cuando ocurre un fallback, lo que permite:

- Monitorear el uso de cada IA
- Detectar patrones de rate limit
- Optimizar la distribución de carga
- Planificar upgrades si es necesario

## Consideraciones

- Ambos modelos son gratuitos pero tienen límites diferentes
- El modelo GLM-4.5 Air puede tener características ligeramente diferentes
- El sistema mantiene la misma interfaz para ambos modelos
- Los embeddings siguen siendo simulados en ambos casos
