import * as React from 'react';
import { useDebouncedValue } from '../hooks/useDebouncedValue';
import { addMealItemFlexible, getFoodDetails, searchFoods, searchFoodsSmart, type FoodDetails, type FoodHit } from '../api/nutrition';
import { getEnhancedSearchTerms } from '../api/ai';

type Unit = 'g' | 'ml' | 'unidad';

export interface FoodPickerProps {
  mealId: string | number;
  onAdded?: () => void;
  onManual?: (prefill?: { name?: string }) => void;
  defaultUnit?: Unit;
  defaultQty?: number;
  useSmartSearch?: boolean; // Nueva prop para habilitar búsqueda inteligente
  searchContext?: string; // Contexto para la búsqueda (ej: "desayuno", "alto en proteína")
}

export default function FoodPicker({ 
  mealId, 
  onAdded, 
  onManual, 
  defaultUnit = 'g', 
  defaultQty = 100,
  useSmartSearch = true, // Habilitar búsqueda inteligente por defecto
  searchContext
}: FoodPickerProps) {
  const [q, setQ] = React.useState('');
  const dq = useDebouncedValue(q, 300);
  const [hits, setHits] = React.useState<FoodHit[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [active, setActive] = React.useState(0);
  // Estados para sugerencias deshabilitados para mejorar rendimiento

  const [sel, setSel] = React.useState<FoodHit | null>(null);
  const [details, setDetails] = React.useState<FoodDetails | null>(null);
  const [qty, setQty] = React.useState<number>(defaultQty);
  const [unit, setUnit] = React.useState<Unit>(defaultUnit);
  const listboxId = React.useId();

  React.useEffect(() => {
    let closed = false;
    async function run() {
      if (!dq) {
        setHits([]);
        // Limpiar estados de sugerencias
        setError(null);
        setLoading(false);
        return;
      }
      
      setLoading(true);
      setError(null);
      
      try {
        // Usar búsqueda inteligente si está habilitada
        if (useSmartSearch) {
          // Solo búsqueda tradicional - sin sugerencias inteligentes
          let res = await searchFoods(dq, 1, 10);
          let map = new Map(res.map((h) => [h.id, h]));
          
          // Si no hay resultados, intentar con términos mejorados de IA
          if (res.length === 0) {
            try {
              const enhancedRes = await getEnhancedSearchTerms(dq, searchContext, false);
              console.log('🔍 Términos mejorados:', enhancedRes);
              
              // Probar cada término mejorado
              for (const term of enhancedRes.slice(0, 2)) { // Solo 2 términos para ser más rápido
                if (term !== dq) { // No repetir la consulta original
                  try {
                    const termRes = await searchFoods(term, 1, 3); // Menos resultados por término
                    termRes.forEach(h => map.set(h.id, h));
                  } catch (e) {
                    console.log('⚠️ Error buscando término:', term, e);
                  }
                }
              }
              
              res = Array.from(map.values());
              console.log('🔍 Resultados con términos mejorados:', res.length);
            } catch (e) {
              console.log('⚠️ Error obteniendo términos mejorados:', e);
            }
          }
          
          if (!closed) {
            setHits(res);
            // Sugerencias deshabilitadas
          }
        } else {
          // Búsqueda tradicional
          const res = await searchFoods(dq, 1, 10);
          const map = new Map(res.map((h) => [h.id, h]));
          if (!closed) setHits(Array.from(map.values()));
        }
      } catch (e) {
        if (!closed) {
          setHits([]);
        // Sugerencias deshabilitadas
          setError('search');
        }
      } finally {
        if (!closed) setLoading(false);
      }
    }
    run();
    return () => {
      closed = true;
    };
  }, [dq, useSmartSearch, searchContext]);

  React.useEffect(() => {
    let stop = false;
    async function loadDetails() {
      if (!sel) return setDetails(null);
      try {
        console.log('🔍 Cargando detalles para:', sel.id, sel.name);
        const d = await getFoodDetails(sel.id);
        console.log('✅ Detalles cargados:', d);
        if (!stop) setDetails(d);
      } catch (e) {
        console.error('❌ Error cargando detalles:', e);
        if (!stop) setDetails(null);
      }
    }
    loadDetails();
    return () => {
      stop = true;
    };
  }, [sel]);

  function computeFactorInfo() {
    if (!details) return { f: 0, estimated: false } as const;
    if (unit === 'g' || unit === 'ml') {
      return { f: qty / 100, estimated: false } as const;
    }
    const ps = (details.portion_suggestions || {}) as Record<string, unknown>;
    const unitG = (ps['unit_g'] || ps['unit_grams'] || ps['grams_per_unit'] || ps['g_per_unit'] || ps['per_unit_g']) as number | undefined;
    if (unit === 'unidad' && unitG && unitG > 0) {
      return { f: (qty * unitG) / 100, estimated: false } as const;
    }
    if (unit === 'unidad') {
      return { f: qty, estimated: true } as const; // fallback 1 unidad = 100 g
    }
    return { f: 0, estimated: false } as const;
  }

  const { f, estimated } = computeFactorInfo();
  const kcal = sel && details ? Math.round(((details.calories_kcal || 0) as number) * f) : 0;
  const pro = sel && details ? (details.protein_g || 0) * f : 0;
  const carb = sel && details ? (details.carbs_g || 0) * f : 0;
  const fat = sel && details ? (details.fat_g || 0) * f : 0;

  async function addItem() {
    if (!sel) return;
    console.log('➕ Agregando alimento:', sel, 'Cantidad:', qty, 'Unidad:', unit);
    try {
      await addMealItemFlexible(String(mealId), { food_id: sel.id, quantity: qty, unit });
      console.log('✅ Alimento agregado exitosamente');
      setQ('');
      setHits([]);
        // Sugerencias deshabilitadas
      setSel(null);
      setDetails(null);
      setQty(defaultQty);
      setUnit(defaultUnit);
      onAdded?.();
    } catch (error) {
      console.error('❌ Error agregando alimento:', error);
    }
  }

  // Función de sugerencias eliminada para mejorar rendimiento

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium">Buscar alimento</label>
      <div className="relative">
        <input
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setSel(null);
            setDetails(null);
            // Sugerencias deshabilitadas
          }}
          onFocus={() => {
            // No mostrar sugerencias inteligentes
            // Sugerencias deshabilitadas
          }}
          className="w-full border rounded px-3 py-2"
          role="combobox"
          aria-expanded={!!hits.length}
          aria-controls={listboxId}
          aria-autocomplete="list"
          aria-activedescendant={hits[active]?.id || ''}
          placeholder={useSmartSearch ? 'Buscar alimento' : 'Buscar alimento (sin sugerencias)'}
          onKeyDown={(e) => {
            if (e.key === 'ArrowDown') setActive((i) => Math.min(i + 1, Math.max(hits.length - 1, 0)));
            if (e.key === 'ArrowUp') setActive((i) => Math.max(i - 1, 0));
            if (e.key === 'Enter' && hits[active]) setSel(hits[active]);
          }}
        />
        
        {/* Sugerencias de IA deshabilitadas para mejorar rendimiento */}
      </div>
      {q && (
        <ul id={listboxId} role="listbox" className="border rounded max-h-60 overflow-auto">
          {loading && <li className="px-3 py-2 text-sm">Buscando...</li>}
          {!loading && error && (
            <li className="px-3 py-2 text-sm">
              Sin resultados (error de búsqueda). Puedes usar «Entrada manual».
            </li>
          )}
          {!loading && !error && hits.length === 0 && <li className="px-3 py-2 text-sm">Sin resultados</li>}
          {hits.map((h, i) => (
            <li
              key={h.id}
              role="option"
              aria-selected={i === active}
              className={`px-3 py-2 cursor-pointer ${i === active ? 'bg-gray-100' : ''}`}
              onMouseEnter={() => setActive(i)}
              onClick={() => {
                console.log('🍎 Seleccionando alimento:', h);
                setSel(h);
              }}
            >
              <div className="flex justify-between">
                <span>
                  {h.name}
                  {h.brand ? ` · ${h.brand}` : ''}
                </span>
                <span className="text-xs text-gray-500">{h.calories_kcal ?? '—'} kcal/100g</span>
              </div>
            </li>
          ))}
        </ul>
      )}

      {sel && details && (
        <div className="border rounded p-3 space-y-3" aria-live="polite">
          <div className="flex gap-2 items-center">
            <input
              type="number"
              min={0}
              step={1}
              value={qty}
              onChange={(e) => setQty(Number(e.target.value) || 0)}
              className="w-28 border rounded px-2 py-1"
              aria-label="Cantidad"
            />
            <select
              value={unit}
              onChange={(e) => setUnit(e.target.value as Unit)}
              className="border rounded px-2 py-1"
              aria-label="Unidad"
            >
              <option value="g">g</option>
              <option value="ml">ml</option>
              <option value="unidad">unidad</option>
            </select>
            <button onClick={addItem} className="ml-auto bg-blue-600 text-white px-3 py-1 rounded">
              Añadir
            </button>
            <button onClick={() => onManual?.({ name: sel.name })} className="px-3 py-1 rounded border">
              Entrada manual
            </button>
          </div>
          <div className="text-sm text-gray-700">
            {estimated && <div className="text-amber-600">Porción estimada (1 unidad ≈ 100 g)</div>}
            <div className="flex gap-4">
              <span>
                <b>{Math.round(kcal)}</b> kcal
              </span>
              <span>Prot {pro.toFixed(1)} g</span>
              <span>Carb {carb.toFixed(1)} g</span>
              <span>Grasa {fat.toFixed(1)} g</span>
            </div>
          </div>
        </div>
      )}

      {!sel && (
        <button onClick={() => onManual?.()} className="text-sm underline">
          Entrada manual
        </button>
      )}
    </div>
  );
}


