import * as React from 'react';
import { useDebouncedValue } from '../hooks/useDebouncedValue';
import { addMealItemFlexible, getFoodDetails, searchFoods, type FoodDetails, type FoodHit } from '../api/nutrition';

type Unit = 'g' | 'ml' | 'unidad';

export interface FoodPickerProps {
  mealId: string | number;
  onAdded?: () => void;
  onManual?: (prefill?: { name?: string }) => void;
  defaultUnit?: Unit;
  defaultQty?: number;
}

export default function FoodPicker({ mealId, onAdded, onManual, defaultUnit = 'g', defaultQty = 100 }: FoodPickerProps) {
  const [q, setQ] = React.useState('');
  const dq = useDebouncedValue(q, 300);
  const [hits, setHits] = React.useState<FoodHit[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [active, setActive] = React.useState(0);

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
        setError(null);
        setLoading(false);
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const res = await searchFoods(dq, 1, 10);
        const map = new Map(res.map((h) => [h.id, h]));
        if (!closed) setHits(Array.from(map.values()));
      } catch (e) {
        if (!closed) {
          setHits([]);
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
  }, [dq]);

  React.useEffect(() => {
    let stop = false;
    async function loadDetails() {
      if (!sel) return setDetails(null);
      try {
        const d = await getFoodDetails(sel.id);
        if (!stop) setDetails(d);
      } catch (e) {
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
    await addMealItemFlexible(String(mealId), { food_id: sel.id, quantity: qty, unit });
    setQ('');
    setHits([]);
    setSel(null);
    setDetails(null);
    setQty(defaultQty);
    setUnit(defaultUnit);
    onAdded?.();
  }

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium">Buscar alimento</label>
      <input
        value={q}
        onChange={(e) => {
          setQ(e.target.value);
          setSel(null);
          setDetails(null);
        }}
        className="w-full border rounded px-3 py-2"
        role="combobox"
        aria-expanded={!!hits.length}
        aria-controls={listboxId}
        aria-autocomplete="list"
        aria-activedescendant={hits[active]?.id || ''}
        placeholder="Escribe para buscar (p. ej., manzana)"
        onKeyDown={(e) => {
          if (e.key === 'ArrowDown') setActive((i) => Math.min(i + 1, Math.max(hits.length - 1, 0)));
          if (e.key === 'ArrowUp') setActive((i) => Math.max(i - 1, 0));
          if (e.key === 'Enter' && hits[active]) setSel(hits[active]);
        }}
      />
      {q && (
        <ul id={listboxId} role="listbox" className="border rounded max-h-60 overflow-auto">
          {loading && <li className="px-3 py-2 text-sm">Buscando…</li>}
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
              onClick={() => setSel(h)}
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


