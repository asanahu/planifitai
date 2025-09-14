"""Sistema optimizado de generación de planes nutricionales con IA."""

from __future__ import annotations

import json
import re
from datetime import date, timedelta
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.ai_client import get_ai_client
from app.auth.deps import UserContext
from app.user_profile.models import UserProfile
from app.nutrition import services as nutrition_services
from app.ai import schemas
from services.food_sources import get_food_source_adapter, FoodHit, FoodDetails


class SmartNutritionPlanGenerator:
    """Generador inteligente de planes nutricionales que analiza el perfil del usuario."""
    
    def __init__(self):
        self.food_adapter = get_food_source_adapter()
    
    def analyze_user_profile(self, profile: UserProfile) -> Dict[str, Any]:
        """Analiza el perfil del usuario para personalizar el plan nutricional."""
        
        # Calcular BMR (Basal Metabolic Rate) usando Mifflin-St Jeor
        bmr = None
        if profile.weight_kg and profile.height_cm and profile.age and profile.sex:
            weight = float(profile.weight_kg)
            height = float(profile.height_cm)
            age = int(profile.age)
            sex = str(profile.sex).lower()
            
            if sex == "male":
                bmr = 10 * weight + 6.25 * height - 5 * age + 5
            elif sex == "female":
                bmr = 10 * weight + 6.25 * height - 5 * age - 161
        
        # Calcular TDEE (Total Daily Energy Expenditure)
        activity_multipliers = {
            "sedentary": 1.2,
            "lightly_active": 1.375,
            "moderately_active": 1.55,
            "very_active": 1.725,
            "extra_active": 1.9
        }
        
        tdee = None
        if bmr and profile.activity_level:
            multiplier = activity_multipliers.get(str(profile.activity_level), 1.55)
            tdee = bmr * multiplier
        
        # Ajustar calorías según objetivo
        target_calories = tdee
        if profile.goal and tdee:
            if profile.goal.value == "lose_weight":
                target_calories = tdee - 500  # Déficit de 500 kcal
            elif profile.goal.value == "gain_weight":
                target_calories = tdee + 300  # Superávit de 300 kcal
        
        # Calcular macronutrientes
        protein_g = None
        carbs_g = None
        fat_g = None
        
        if target_calories:
            # Proteína: 1.6-2.2g por kg de peso corporal
            if profile.weight_kg:
                protein_g = float(profile.weight_kg) * 1.8
            else:
                protein_g = target_calories * 0.25 / 4  # 25% de calorías
            
            # Grasas: 25-30% de calorías totales
            fat_g = target_calories * 0.28 / 9
            
            # Carbohidratos: el resto
            carbs_g = (target_calories - (protein_g * 4) - (fat_g * 9)) / 4
        
        return {
            "bmr": bmr,
            "tdee": tdee,
            "target_calories": target_calories,
            "protein_g": protein_g,
            "carbs_g": carbs_g,
            "fat_g": fat_g,
            "profile_summary": {
                "age": profile.age,
                "sex": profile.sex,
                "weight_kg": float(profile.weight_kg) if profile.weight_kg else None,
                "height_cm": float(profile.height_cm) if profile.height_cm else None,
                "goal": profile.goal.value if profile.goal else None,
                "activity_level": profile.activity_level.value if profile.activity_level else None,
                "allergies": profile.allergies,
                "medical_conditions": profile.medical_conditions
            }
        }
    
    def get_available_foods(self) -> List[Dict[str, Any]]:
        """Obtiene una lista de alimentos disponibles de la base de datos."""
        
        # Lista de alimentos españoles comunes para buscar
        spanish_foods = [
            "pollo", "salmón", "atún", "huevos", "yogur griego", 
            "arroz integral", "quinoa", "avena", "patata", "boniato",
            "aguacate", "aceite de oliva", "brócoli", "espinacas", 
            "tomate", "pimiento", "cebolla", "ajo", "plátano", 
            "manzana", "naranja", "fresas", "nueces", "almendras",
            "leche", "queso fresco", "lentejas", "garbanzos", "judías"
        ]
        
        available_foods = []
        
        for food_name in spanish_foods:
            try:
                # Buscar alimento en la base de datos
                hits = self.food_adapter.search(food_name, page_size=3)
                
                if hits:
                    # Tomar el primer resultado y obtener detalles
                    best_hit = hits[0]
                    details = self.food_adapter.get_details(best_hit.source_id)
                    
                    if details.calories_kcal and details.protein_g is not None:
                        available_foods.append({
                            "name": best_hit.name,
                            "source_id": best_hit.source_id,
                            "source": best_hit.source,
                            "calories_kcal": details.calories_kcal,
                            "protein_g": details.protein_g or 0,
                            "carbs_g": details.carbs_g or 0,
                            "fat_g": details.fat_g or 0
                        })
                        
                        # Limitar a 30 alimentos para no saturar el prompt
                        if len(available_foods) >= 30:
                            break
                            
            except Exception as e:
                # Si falla la búsqueda de un alimento, continuar con el siguiente
                continue
        
        return available_foods
    
    def generate_optimized_plan(
        self, 
        user: UserContext, 
        req: schemas.NutritionPlanRequest, 
        db: Session
    ) -> schemas.NutritionPlan:
        """Genera un plan nutricional optimizado usando análisis de perfil y alimentos de BD."""
        
        # Obtener perfil del usuario
        profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        
        if not profile:
            # Crear perfil por defecto si no existe
            from app.user_profile.models import Goal, ActivityLevel
            profile = UserProfile(
                user_id=user.id,
                age=30,  # Edad por defecto
                sex="male",  # Sexo por defecto
                weight_kg=70.0,  # Peso por defecto
                height_cm=170.0,  # Altura por defecto
                goal=Goal.MAINTAIN_WEIGHT,  # Objetivo por defecto
                activity_level=ActivityLevel.MODERATELY_ACTIVE  # Actividad por defecto
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)
        
        # Analizar perfil
        profile_analysis = self.analyze_user_profile(profile)
        
        # Obtener alimentos disponibles de la BD
        available_foods = self.get_available_foods()
        
        if not available_foods:
            # Fallback a alimentos básicos si no hay conexión a BD
            available_foods = [
                {"name": "Pollo", "calories_kcal": 165, "protein_g": 31, "carbs_g": 0, "fat_g": 3.6},
                {"name": "Arroz integral", "calories_kcal": 111, "protein_g": 2.6, "carbs_g": 23, "fat_g": 0.9},
                {"name": "Brócoli", "calories_kcal": 34, "protein_g": 2.8, "carbs_g": 7, "fat_g": 0.4},
                {"name": "Aceite de oliva", "calories_kcal": 884, "protein_g": 0, "carbs_g": 0, "fat_g": 100},
                {"name": "Huevos", "calories_kcal": 155, "protein_g": 13, "carbs_g": 1.1, "fat_g": 11}
            ]
        
        # Generar fechas
        today = date.today()
        dates = [(today + timedelta(days=i)).isoformat() for i in range(req.days)]
        
        # Construir prompt optimizado
        system_prompt = self._build_system_prompt(available_foods)
        user_prompt = self._build_user_prompt(req, profile_analysis, dates, available_foods)
        
        # Generar con IA
        client = get_ai_client()
        resp = client.chat(
            user.id,
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        
        # Parsear respuesta
        data = self._parse_json_payload(resp.get("reply", ""))

        # Normalizar/Completar campos faltantes (meal_kcal, totals, números)
        data = self._normalize_plan_data(data)
        
        try:
            return schemas.NutritionPlan.model_validate(data)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"AI nutrition validation failed: {exc}")
    
    def _build_system_prompt(self, available_foods: List[Dict[str, Any]]) -> str:
        """Construye el prompt del sistema optimizado."""
        
        foods_list = "\n".join([
            f"- {food['name']}: {food['calories_kcal']:.0f} kcal, "
            f"{food['protein_g']:.1f}g proteína, {food['carbs_g']:.1f}g carbohidratos, "
            f"{food['fat_g']:.1f}g grasas (por 100g)"
            for food in available_foods[:15]  # Reducir a 15 para evitar prompts muy largos
        ])
        
        return f"""Eres PlanifitAI, un experto nutricionista. Genera planes nutricionales en JSON válido.

FORMATO JSON EXACTO (sin comentarios, sin texto adicional):
{{
  "days": [
    {{
      "date": "2025-09-13",
      "meals": [
        {{
          "type": "breakfast",
          "items": [
            {{
              "name": "Avena",
              "qty": 50,
              "unit": "g",
              "kcal": 190,
              "protein_g": 7,
              "carbs_g": 32,
              "fat_g": 4
            }}
          ],
          "meal_kcal": 190
        }}
      ],
      "totals": {{
        "kcal": 2200,
        "protein_g": 120,
        "carbs_g": 250,
        "fat_g": 70
      }}
    }}
  ],
  "targets": {{
    "kcal": 2200,
    "protein_g": 120,
    "carbs_g": 250,
    "fat_g": 70
  }}
}}

ALIMENTOS DISPONIBLES (por 100g):
{foods_list}

REGLAS CRÍTICAS:
1. USA SOLO alimentos de la lista
2. CALCULA correctamente: kcal = (qty/100) * kcal_por_100g
3. Incluye breakfast, lunch, dinner, snack
4. JSON válido SIN comentarios ni texto extra
5. Números enteros para cantidades y calorías

IMPORTANTE: Responde SOLO JSON válido."""
    
    def _build_user_prompt(
        self, 
        req: schemas.NutritionPlanRequest, 
        profile_analysis: Dict[str, Any], 
        dates: List[str],
        available_foods: List[Dict[str, Any]]
    ) -> str:
        """Construye el prompt del usuario personalizado."""
        
        profile_summary = profile_analysis["profile_summary"]
        targets = {
            "kcal": int(profile_analysis.get("target_calories", 2000)),
            "protein_g": int(profile_analysis.get("protein_g", 120)),
            "carbs_g": int(profile_analysis.get("carbs_g", 250)),
            "fat_g": int(profile_analysis.get("fat_g", 70))
        }
        
        restrictions = []
        if profile_summary.get("allergies"):
            restrictions.append(f"Alergias: {profile_summary['allergies']}")
        if profile_summary.get("medical_conditions"):
            restrictions.append(f"Condiciones médicas: {profile_summary['medical_conditions']}")
        
        return f"""Genera un plan nutricional personalizado para {req.days} días.

PERFIL DEL USUARIO:
- Edad: {profile_summary.get('age', 'No especificada')} años
- Sexo: {profile_summary.get('sex', 'No especificado')}
- Peso: {profile_summary.get('weight_kg', 'No especificado')} kg
- Altura: {profile_summary.get('height_cm', 'No especificada')} cm
- Objetivo: {profile_summary.get('goal', 'mantener peso')}
- Nivel de actividad: {profile_summary.get('activity_level', 'moderado')}
{f"- Restricciones: {'; '.join(restrictions)}" if restrictions else ""}

OBJETIVOS NUTRICIONALES CALCULADOS:
- Calorías diarias: {targets['kcal']} kcal
- Proteínas: {targets['protein_g']} g
- Carbohidratos: {targets['carbs_g']} g
- Grasas: {targets['fat_g']} g

FECHAS: {dates[0]} a {dates[-1]}

INSTRUCCIONES:
1. Crea un plan PERSONALIZADO basado en el perfil del usuario
2. RESPETA los objetivos nutricionales calculados
3. USA SOLO alimentos de la lista disponible
4. Incluye 4 comidas por día: desayuno, almuerzo, cena, merienda
5. Varía los alimentos entre días para evitar monotonía
6. Considera horarios españoles de comida
7. CALCULA correctamente las cantidades para alcanzar los objetivos

Genera el JSON completo para los {req.days} días."""
    
    def _parse_json_payload(self, reply: str) -> Dict[str, Any]:
        """Parsea la respuesta JSON de la IA con manejo robusto de errores."""
        clean_reply = reply.strip()
        
        # Remover markdown si existe
        if clean_reply.startswith('```json'):
            clean_reply = clean_reply[7:]
        if clean_reply.startswith('```'):
            clean_reply = clean_reply[3:]
        if clean_reply.endswith('```'):
            clean_reply = clean_reply[:-3]
        clean_reply = clean_reply.strip()
        
        # Encontrar el JSON válido si hay texto adicional
        json_start = clean_reply.find('{')
        json_end = clean_reply.rfind('}')
        
        if json_start != -1 and json_end != -1:
            clean_reply = clean_reply[json_start:json_end+1]
        
        try:
            data = json.loads(clean_reply)
            
            # Validar estructura mínima
            if not isinstance(data, dict):
                raise ValueError("Response is not a JSON object")
            
            if 'days' not in data or 'targets' not in data:
                raise ValueError("Missing required fields: days or targets")
            
            if not isinstance(data['days'], list) or len(data['days']) == 0:
                raise ValueError("Days must be a non-empty list")
            
            return data
            
        except json.JSONDecodeError as e:
            # Log del error para debugging
            print(f"JSON Parse Error: {e}")
            print(f"Problematic JSON (first 500 chars): {clean_reply[:500]}")
            
            # Intentar reparaciones automáticas múltiples
            repaired_json = self._attempt_json_repair(clean_reply, str(e))
            
            if repaired_json:
                try:
                    data = json.loads(repaired_json)
                    print("✅ JSON reparado exitosamente")
                    # Validar estructura del JSON reparado
                    if isinstance(data, dict) and 'days' in data and 'targets' in data:
                        return data
                except:
                    pass
            
            # Si no se puede reparar, generar plan de emergencia
            print("⚠️ Generando plan de emergencia debido a JSON malformado")
            return self._generate_emergency_plan()
    
    def _attempt_json_repair(self, json_str: str, error_msg: str) -> str | None:
        """Intenta reparar JSON malformado con técnicas comunes."""
        
        repairs = [
            # Reparar comas finales
            lambda s: s.replace(',}', '}').replace(',]', ']'),
            # Reparar comas faltantes entre objetos
            lambda s: s.replace('}\n    {', '},\n    {').replace('} {', '}, {'),
            # Reparar comillas faltantes en claves
            lambda s: re.sub(r'(\w+):', r'"\1":', s),
            # Truncar en el último objeto válido si está incompleto
            lambda s: self._truncate_to_last_valid_object(s),
        ]
        
        for repair in repairs:
            try:
                repaired = repair(json_str)
                json.loads(repaired)  # Validar que es JSON válido
                return repaired
            except:
                continue
                
        return None
    
    def _truncate_to_last_valid_object(self, json_str: str) -> str:
        """Trunca el JSON al último objeto válido completo."""
        
        # Buscar el último '}' que podría cerrar un día completo
        lines = json_str.split('\n')
        for i in range(len(lines) - 1, -1, -1):
            if '}' in lines[i] and 'day' not in lines[i].lower():
                # Intentar truncar aquí y cerrar la estructura
                truncated = '\n'.join(lines[:i+1])
                
                # Agregar cierre de arrays/objetos si es necesario
                if truncated.count('{') > truncated.count('}'):
                    truncated += '\n    }\n  ]\n}'
                elif not truncated.endswith('}'):
                    truncated += '\n}'
                
                try:
                    json.loads(truncated)
                    return truncated
                except:
                    continue
        
        return json_str
    
    def _generate_emergency_plan(self) -> Dict[str, Any]:
        """Genera un plan de emergencia cuando falla la IA."""
        
        # Plan básico de emergencia con 14 días
        emergency_days: list[dict] = []
        
        base_meals = [
            {
                "type": "breakfast",
                "items": [
                    {"name": "Avena", "qty": 80, "unit": "g", "kcal": 300, "protein_g": 10, "carbs_g": 50, "fat_g": 6},
                    {"name": "Leche", "qty": 200, "unit": "ml", "kcal": 120, "protein_g": 8, "carbs_g": 12, "fat_g": 3}
                ]
            },
            {
                "type": "lunch", 
                "items": [
                    {"name": "Pollo", "qty": 150, "unit": "g", "kcal": 250, "protein_g": 30, "carbs_g": 0, "fat_g": 12},
                    {"name": "Arroz", "qty": 100, "unit": "g", "kcal": 350, "protein_g": 7, "carbs_g": 75, "fat_g": 2},
                    {"name": "Brócoli", "qty": 150, "unit": "g", "kcal": 50, "protein_g": 4, "carbs_g": 10, "fat_g": 1}
                ]
            },
            {
                "type": "dinner",
                "items": [
                    {"name": "Salmón", "qty": 120, "unit": "g", "kcal": 200, "protein_g": 25, "carbs_g": 0, "fat_g": 12},
                    {"name": "Ensalada", "qty": 200, "unit": "g", "kcal": 40, "protein_g": 3, "carbs_g": 8, "fat_g": 1}
                ]
            },
            {
                "type": "snack",
                "items": [
                    {"name": "Yogur", "qty": 150, "unit": "g", "kcal": 120, "protein_g": 15, "carbs_g": 12, "fat_g": 3},
                    {"name": "Nueces", "qty": 30, "unit": "g", "kcal": 200, "protein_g": 5, "carbs_g": 4, "fat_g": 18}
                ]
            }
        ]

        # Construir 14 días con meal_kcal y totals
        from copy import deepcopy
        for d in range(14):
            meals = deepcopy(base_meals)
            day_totals = {"kcal": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}
            for m in meals:
                mkcal = 0.0
                for it in m.get("items", []):
                    mkcal += float(it.get("kcal", 0) or 0)
                    day_totals["protein_g"] += float(it.get("protein_g", 0) or 0)
                    day_totals["carbs_g"] += float(it.get("carbs_g", 0) or 0)
                    day_totals["fat_g"] += float(it.get("fat_g", 0) or 0)
                m["meal_kcal"] = round(mkcal, 2)
                day_totals["kcal"] += mkcal
            day = {
                "date": (date.today() + timedelta(days=d)).isoformat(),
                "meals": meals,
                "totals": {
                    "kcal": round(day_totals["kcal"], 2),
                    "protein_g": round(day_totals["protein_g"], 2),
                    "carbs_g": round(day_totals["carbs_g"], 2),
                    "fat_g": round(day_totals["fat_g"], 2),
                },
            }
            emergency_days.append(day)
        
        return {
            "days": emergency_days,
            "targets": {
                "kcal": 2200,
                "protein_g": 120,
                "carbs_g": 250,
                "fat_g": 70,
            },
        }

    def _normalize_plan_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza y completa campos faltantes del plan para cumplir el esquema.
        - Agrega meal_kcal si falta (suma de items.kcal)
        - Agrega totals por día si falta (suma de items por todas las comidas)
        - Asegura tipos numéricos
        """
        if not isinstance(data, dict):
            return data
        days = data.get("days")
        if not isinstance(days, list):
            return data
        for day in days:
            meals = day.get("meals") or []
            # Acumular totales del día
            sum_kcal = 0.0
            sum_p = 0.0
            sum_c = 0.0
            sum_f = 0.0
            for meal in meals:
                items = meal.get("items") or []
                mkcal = 0.0
                for it in items:
                    # Asegurar números
                    it["kcal"] = float(it.get("kcal", 0) or 0)
                    it["protein_g"] = float(it.get("protein_g", 0) or 0)
                    it["carbs_g"] = float(it.get("carbs_g", 0) or 0)
                    it["fat_g"] = float(it.get("fat_g", 0) or 0)
                    mkcal += it["kcal"]
                    sum_p += it["protein_g"]
                    sum_c += it["carbs_g"]
                    sum_f += it["fat_g"]
                if "meal_kcal" not in meal or meal.get("meal_kcal") is None:
                    meal["meal_kcal"] = round(mkcal, 2)
                sum_kcal += mkcal
            if "totals" not in day or not isinstance(day.get("totals"), dict):
                day["totals"] = {
                    "kcal": round(sum_kcal, 2),
                    "protein_g": round(sum_p, 2),
                    "carbs_g": round(sum_c, 2),
                    "fat_g": round(sum_f, 2),
                }
        # Targets por defecto si faltan
        if "targets" not in data or not isinstance(data.get("targets"), dict):
            # Usar el primer día como guía
            first = (days[0].get("totals") if days and isinstance(days[0], dict) else None) or {}
            data["targets"] = {
                "kcal": int(first.get("kcal", 2000) or 2000),
                "protein_g": float(first.get("protein_g", 120) or 120),
                "carbs_g": float(first.get("carbs_g", 250) or 250),
                "fat_g": float(first.get("fat_g", 70) or 70),
            }
        return data


# Instancia global del generador
smart_generator = SmartNutritionPlanGenerator()


def generate_smart_nutrition_plan(
    user: UserContext,
    req: schemas.NutritionPlanRequest,
    db: Session
) -> schemas.NutritionPlan:
    """Función principal para generar planes nutricionales inteligentes."""
    return smart_generator.generate_optimized_plan(user, req, db)
