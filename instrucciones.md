Contexto y Rol
Actúas como Auditor Técnico Frontend (React + TypeScript + Tailwind). Tu objetivo es verificar que el autocompletado de alimentos está integrado en la vista de comidas y hace llamadas a los endpoints de backend.
Consulta/Tarea
1.	Localiza el componente de autocompletado (p. ej., FoodPicker o similar).
2.	Verifica que en la pantalla de Meals el prompt antiguo fue reemplazado por el nuevo componente.
3.	Busca en el código llamadas a GET /nutrition/foods/search y a POST /nutrition/meal/{meal_id}/items.
4.	En modo dev, simula teclear “manzana” y comprueba que aparecen peticiones de red a la ruta detectada (api_base del Prompt A).
5.	Genera un reporte con PASS/FAIL y las rutas efectivamente invocadas.
Especificaciones
•	Si hay custom API client, verifica que usa la base URL correcta (VITE_API_BASE_URL o similar).
•	Comprueba existencia de debounce en la búsqueda (≥ 250–300 ms).
•	Verifica estados UI: loading, empty, error.
•	Asegura que hay un fallback de “Entrada manual” cuando la búsqueda no arroja resultados.
Criterios de Calidad
•	Componente de autocompletado existe y está montado en Meals.
•	La búsqueda dispara GET /nutrition/foods/search con q= (y paginación si procede).
•	El “Añadir” produce POST /nutrition/meal/{meal_id}/items con food_id o query + quantity + unit.
•	UI reacciona a loading/error sin romper.
Cómo debe ser la respuesta
•	Un JSON de salida {
  "frontend_audit": {
    "component_found": "FoodPicker",
    "wired_in_meals": "PASS/FAIL",
    "api_calls": {
      "search": {"found_in_code": true, "url": "/api/v1/nutrition/foods/search"},
      "add_item": {"found_in_code": true, "url": "/api/v1/nutrition/meal/{meal_id}/items"}
    },
    "devtools_network": {
      "search_typing_manzana": {"requests": 1, "status": [200], "debounce_ms": 300}
    },
    "fallback_manual_entry": "PASS/FAIL",
    "notes": ["…"]
  }
}
•	Log con rutas de archivos donde se hallaron referencias (grep/AST) y capturas de red (texto).
Verificación
•	Implementa scripts/verify_food_frontend.mjs que:
o	Hace búsqueda estática (grep/AST) de foods/search y meal/*/items en el código.
o	(Opcional) Usa Playwright o Puppeteer para levantar el front (si procede) y simular tecleo, capturando las requests reales.
o	Imprime el JSON de auditoría + log.

