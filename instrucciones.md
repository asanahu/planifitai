Resumen rápido: he trazado el flujo completo de generación del plan (modelo usado, prompts, uso de perfil, persistencia y renderizado en web). El modelo que se usa por defecto en tu entorno es OpenAI con “gpt-5-nano” y eso es frágil. El plan se genera y se persiste, pero el “volcado” al planner de la web es inconsistente porque la UI lee del localStorage con un useMemo que no reacciona a cambios, y además el endpoint de status “directo” no devuelve el plan en el polling.

Diagnóstico

Proveedor/modelo:

OpenAI principal: app/ai/provider.py:66 usa model="gpt-5-nano" con parámetros no estándar (reasoning_effort, verbosity). Esto no es el modelo por defecto configurado y puede fallar con la API. Ruta: app/ai/provider.py:66.
Config: app/core/config.py: valores por defecto establecen OPENAI_CHAT_MODEL="gpt-4o-mini" y OpenRouter deepseek/deepseek-chat-v3.1:free. Ruta: app/core/config.py:22.
Selección real: como en tu .env hay API_OPEN_AI y OPENAI_API_KEY vacío, LocalAiClient elige OpenAIProvider (gpt-5-nano) en vez de OpenRouter. Ruta: app/ai_client.py:72.
OpenRouter providers están disponibles como fallback, pero solo se usan por rate limit. Rutas: app/ai/provider.py:101 y app/ai_client.py:105.
Prompts:

Smart generator (recomendado): prompts estructurados con formato JSON estricto, lista de alimentos de BD y reglas claras. Rutas: app/ai/smart_generator.py:98 (system prompt) y :162 (user prompt).
Servicios “rápidos”: prompts concisos con esquema JSON mínimo. Rutas: app/ai/services.py:339 (system prompt de optimized).
Uso de perfil:

Smart generator calcula BMR/TDEE/targets, usa edad/sexo/peso/altura/objetivo/actividad y restricciones. Ruta: app/ai/smart_generator.py:18, :43, :94.
Si falta perfil, crea uno por defecto y sigue. Ruta: app/ai/smart_generator.py:61.
Persistencia:

Al generar 14 días, limpia comidas IA previas y persiste nuevas comidas + targets diarios. Ruta: app/ai/routers.py:1124 y app/ai/plan_persistence.py:44.
Mapeo flexible de campos (kcal/protein/carb/fat), unidades y tipos de comida. Ruta: app/ai/plan_persistence.py:76, :94.
Web / volcado del plan:

La UI “Plan semanal” usa localStorage como fuente del “plan” y lee con useMemo(() => getMealPlanForWeek(selectedWeek), [selectedWeek]). Esto no reacciona a que GeneratePlanFromAI escriba el plan (no hay dependencia del cambio ni evento). Ruta: web/src/features/nutrition/MealsPlan.tsx:131.
GeneratePlanFromAI mapea el plan IA a localStorage para week1/week2, pero no notifica al padre para refrescar la lectura. Ruta: web/src/features/nutrition/GeneratePlanFromAI.tsx:34, :49, :78.
El hook de polling consulta /ai/generate/nutrition-plan-status/{task_id}. Para tareas “directas” (ids ‘smart-/direct-’), el backend devuelve plan=None por diseño, así que status.plan no sirve para “handlePlanComplete”; solo el primer response trae el plan. Rutas: web/src/hooks/useAsyncNutritionPlan.ts:26; app/ai/routers.py:1195.
Causas raíz del “no vuelca correctamente”

Reactividad localStorage: MealsPlan memoiza el “plan de semana” por weekKey y no se vuelve a calcular cuando GeneratePlanFromAI escribe; no hay señal (estado/efecto/evento) que dispare un reread.
API de status “directa”: el polling devuelve SUCCESS sin plan, por lo que componentes que dependan de status.plan no podrán mapear. Aunque tú lo solventaste usando el response.plan inicial, es frágil si cambia el flujo.
Plan de acción recomendado

Backend

Modelo/Proveedor:

Alinear OpenAIProvider al modelo configurado: usar settings.OPENAI_CHAT_MODEL en vez de literal “gpt-5-nano”. Quitar parámetros no soportados.
app/ai/provider.py:66-71.
Opcional: si quieres priorizar OpenRouter free, invierte la preferencia en LocalAiClient cuando OPENROUTER_KEY exista aunque API_OPEN_AI esté definido. Ruta: app/ai_client.py:64-86.
JSON mode: si usas OpenAI 4o-mini, activa response_format={"type":"json_object"} para robustecer la salida JSON (en Providers compatibles).
Smart generator:

Mantener el prompt actual, pero deja claro:
Unidades permitidas “g/ml/unit”, cantidades y kcal enteras, macros float.
“Usa solo alimentos listados” ya está.
Limitar alimentos a 12-15 (ya lo haces) y asegurar targets en salida incluso si el modelo los omite (ya normalizas). Rutas: app/ai/smart_generator.py:129, :340.
Endpoint de status:

Para task_id “directos” (‘smart-’, ‘direct-’), devuelve también days_generated y targets ya lo haces; opcionalmente incluye un plan_summary (primer día, conteo de meals) para UX sin exponer el plan completo.
Frontend

Reactividad del planner:

Sustituir useMemo(() => getMealPlanForWeek(selectedWeek), [selectedWeek]) por un estado sincronizado con localStorage (useSyncExternalStore o un evento custom).
Opción simple: en GeneratePlanFromAI, tras setMealPlanForWeek(...), emite window.dispatchEvent(new Event('mealplan:updated')); en MealsPlan añade un useEffect que al capturar mealplan:updated recarga getMealPlanForWeek(selectedWeek) en estado.
Archivos: web/src/features/nutrition/GeneratePlanFromAI.tsx, web/src/features/nutrition/MealsPlan.tsx.
Polling vs streaming:

Cambiar a SSE GET /ai/generate/nutrition-plan-stream/{task_id} para progreso en tiempo real y menos carga. Rutas: app/ai/routers.py:624.
Si mantienes polling, conserva el fallback a response.plan tal como haces y documenta que el status “directo” no trae plan.
Timezone/weekday mapping:

En aiMap.ts, al derivar el día desde date, usa UTC estable para evitar off-by-one en husos: por ejemplo, crear la fecha con new Date(date + 'T12:00:00Z') antes de getUTCDay() y mapear a Mon..Sun. Ruta: web/src/features/nutrition/aiMap.ts:18.
UX del volcado:

Después de guardar week1/week2, muestra CTA para “Copiar plan a comidas reales” o automatízalo solo para días del pasado/presente (invocando syncCurrentDay() ya haces parte para el día actual).
Validación y observabilidad

Logs: en plan_persistence.persist_nutrition_plan ya registras conteo de comidas/targets y errores; propaga persist al frontend (ya devuelves ese objeto en la respuesta del endpoint de generación).
Pruebas:
Unit tests de _normalize_plan_data y _parse_json_payload (ya son robustos).
Test de aiMap.ts con 14 fechas cruzando semanas y distintos husos.
Test E2E del flujo: generar → mapear → planner muestra week1/week2 → copiar a “comidas reales”.
Cambios concretos (sugeridos)

app/ai/provider.py:66

Antes: model="gpt-5-nano", reasoning_effort="low", verbosity="low"
Después: model=settings.OPENAI_CHAT_MODEL y sin extras. Opcional añadir response_format si procede.
web/src/features/nutrition/GeneratePlanFromAI.tsx

Tras setMealPlanForWeek('week1', ...) y week2, dispara window.dispatchEvent(new Event('mealplan:updated')).
web/src/features/nutrition/MealsPlan.tsx

Reemplaza useMemo(() => getMealPlanForWeek(selectedWeek), [selectedWeek]) por:
const [currentWeekPlan, setCurrentWeekPlan] = useState(() => getMealPlanForWeek(selectedWeek));
Efecto: al cambiar selectedWeek o al recibir mealplan:updated, llama setCurrentWeekPlan(getMealPlanForWeek(selectedWeek)).
Idem para currentWeekActuals si quieres coherencia.
web/src/features/nutrition/aiMap.ts

En toUiDayKey, usa getUTCDay() con fecha “anclada” a mediodía UTC: const dt = new Date(dateStr + 'T12:00:00Z').
Roadmap de implementación

Fase 1: Robustez del backend

Corrige modelo OpenAI y parámetros.
Mantén smart_generator y normalización como fuente principal.
Confirma persistencia correcta leyendo persist.meals_created en las respuestas.
Fase 2: UX del planner

Añade evento mealplan:updated y suscripción en MealsPlan.
Ajusta mapeo de días a UTC para evitar desalineaciones.
Fase 3: Progreso y consumo

Cambia hook a SSE o mantén polling con tolerancia a “directo”.
Opcional: añadir botón “Volcar a comidas reales (semana actual)” tras generación.
Fase 4: Fuente de verdad (opcional)

Evoluciona MealsPlan para leer “planificado” desde el backend (ya se persiste) en lugar de localStorage, con endpoints “get planned week” y “apply planned → actuals”.
Notas y referencias útiles

Modelo OpenAI actual: app/ai/provider.py:66
Config modelos: app/core/config.py:22
Cliente AI y selección proveedor: app/ai_client.py:64
Smart generator: app/ai/smart_generator.py:98, 162
Persistencia plan: app/ai/plan_persistence.py:44
Endpoint 14 días (con persistencia): app/ai/routers.py:1097
Status directo sin plan: app/ai/routers.py:1195
UI planner (lee localStorage con useMemo): web/src/features/nutrition/MealsPlan.tsx:131
Mapeo IA → planner: web/src/features/nutrition/aiMap.ts:18
¿Quieres que haga yo mismo estos cambios mínimos (evento de actualización en la web y el modelo en el provider), o prefieres que te deje un PR con diffs propuestos para revisarlos?