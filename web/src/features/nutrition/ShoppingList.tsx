import { useMemo, useState } from 'react';
import { getMealPlan, getMealActuals, clearMealPlan, clearMealActuals } from '../../utils/storage';
import Button from '../../components/ui/button';

type Grouped = Record<string, Array<{ name: string; qty?: number; unit?: string; count?: number }>>;
type Source = 'plan' | 'actuals' | 'both';

function tokenize(s: string): string[] {
  return s
    .toLowerCase()
    .normalize('NFD')
    .replace(/\p{M}+/gu, '')
    .split(/[^a-zA-Z]+/)
    .filter(Boolean);
}

function categorize(name: string): string {
  const t = tokenize(name);
  const has = (xs: string[]) => xs.some((k) => t.includes(k));
  if (has(['manzana', 'platano', 'banana', 'pera', 'naranja', 'fresa', 'uva', 'kiwi', 'mango', 'pina', 'limon', 'arandano', 'aguacate'])) return 'Frutas';
  if (has(['lechuga', 'tomate', 'zanahoria', 'pepino', 'pimiento', 'cebolla', 'ajo', 'espinaca', 'brocoli', 'coliflor', 'calabacin', 'berenjena', 'acelga', 'apio', 'verdura', 'verduras', 'ensalada'])) return 'Verduras';
  if (has(['pollo', 'pavo', 'ternera', 'res', 'cerdo', 'huevo', 'huevos', 'atun', 'salmon', 'pescado', 'pechuga', 'tofu'])) return 'Proteínas';
  if (has(['lenteja', 'garbanzo', 'alubia', 'judia'])) return 'Legumbres';
  if (has(['arroz', 'pasta', 'pan', 'avena', 'quinoa', 'cuscus', 'maiz'])) return 'Cereales';
  if (has(['leche', 'yogur', 'yoghurt', 'queso', 'mantequilla', 'nata', 'kefir'])) return 'Lácteos';
  if (has(['nuez', 'almendra', 'cacahuete', 'avellana', 'pistacho', 'anacardo', 'semilla', 'semillas'])) return 'Frutos secos y semillas';
  if (has(['aceite', 'sal', 'azucar', 'vinagre', 'pimienta', 'especias', 'salsa', 'soja'])) return 'Aceites y condimentos';
  if (has(['agua', 'zumo', 'jugo', 'cafe', 'te'])) return 'Bebidas';
  return 'Otros';
}

function parseItem(raw: string): { name: string; qty?: number; unit?: string } {
  // Expected formats like: "30 g aguacate", "50g arroz", "1 unidad manzana", or plain name
  const s = raw.trim();
  const m = s.match(/^\s*(\d+[\.,]?\d*)\s*([a-zA-Z]+)?\s+(.+)$/);
  if (m) {
    const qty = parseFloat(m[1].replace(',', '.'));
    let unit = (m[2] || '').toLowerCase();
    let name = m[3].trim();
    // Normalize units
    if (unit === 'gr' || unit === 'gramos' || unit === 'g') unit = 'g';
    else if (unit === 'ml') unit = 'ml';
    else if (unit.startsWith('uni')) unit = 'unidad';
    else if (!unit) unit = 'unidad';
    // Clean name of trailing unit words
    name = name.replace(/^de\s+/, '');
    return { name, qty, unit };
  }
  // Try trailing quantity, e.g., "aguacate 30 g"
  const m2 = s.match(/^(.+?)\s+(\d+[\.,]?\d*)\s*([a-zA-Z]+)$/);
  if (m2) {
    const name = m2[1].trim();
    const qty = parseFloat(m2[2].replace(',', '.'));
    let unit = m2[3].toLowerCase();
    if (unit === 'gr' || unit === 'gramos' || unit === 'g') unit = 'g';
    else if (unit === 'ml') unit = 'ml';
    else if (unit.startsWith('uni')) unit = 'unidad';
    return { name, qty, unit };
  }
  // Fallback: just a name
  return { name: s };
}

export default function ShoppingList() {
  const [source, setSource] = useState<Source>('plan');
  const plan = getMealPlan();
  const actuals = getMealActuals();
  const grouped = useMemo<Grouped>(() => {
    type Key = string; // name::unit (unit optional)
    const sums: Record<Key, { name: string; unit?: string; qty?: number; count?: number }> = {};
    const datasets: Array<Record<string, string[]>> = [];
    if (source === 'plan' || source === 'both') datasets.push(...Object.values(plan));
    if (source === 'actuals' || source === 'both') datasets.push(...Object.values(actuals as any));
    datasets.forEach((meals) => {
      Object.values(meals).forEach((arr) => {
        arr.forEach((raw) => {
          const { name, qty, unit } = parseItem(raw);
          const key = `${name.toLowerCase()}::${unit || ''}`;
          if (!sums[key]) sums[key] = { name, unit, qty: 0, count: 0 };
          if (qty != null) sums[key].qty = (sums[key].qty || 0) + qty;
          else sums[key].count = (sums[key].count || 0) + 1;
        });
      });
    });
    const out: Grouped = {};
    Object.values(sums).forEach((item) => {
      const cat = categorize(item.name);
      if (!out[cat]) out[cat] = [];
      out[cat].push(item);
    });
    Object.values(out).forEach((arr) =>
      arr.sort((a, b) => a.name.localeCompare(b.name, 'es'))
    );
    return out;
  }, [plan, actuals, source]);

  const fmtNumber = (n: number) => (Number.isInteger(n) ? String(n) : n.toFixed(1));
  const fmt = (it: { name: string; qty?: number; unit?: string; count?: number }) =>
    it.qty != null && it.unit ? `${it.name} ${fmtNumber(it.qty)} ${it.unit}` : `${it.name} x${it.count || 1}`;

  const copy = () => {
    const text = Object.entries(grouped)
      .map(([cat, arr]) => `# ${cat}\n` + arr.map((it) => `- ${fmt(it)}`).join('\n'))
      .join('\n\n');
    navigator.clipboard.writeText(text);
    alert('Copiado');
  };

  const download = () => {
    const csv = Object.entries(grouped)
      .flatMap(([cat, arr]) => arr.map((it) => `${cat},${it.name},${it.qty ?? it.count ?? 1},${it.unit ?? ''}`))
      .join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'shopping-list.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  const cats = Object.keys(grouped).sort();
  const clear = () => {
    if (source === 'plan') clearMealPlan();
    else if (source === 'actuals') clearMealActuals();
    else { clearMealPlan(); clearMealActuals(); }
    setSource((s) => s); // trigger recompute
    alert('Limpieza completada');
  };
  const totalItems = Object.values(grouped).reduce((acc, arr) => acc + arr.length, 0);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3 text-sm">
          <span>Fuente:</span>
          <label className="inline-flex items-center gap-1"><input type="radio" name="src" checked={source==='plan'} onChange={() => setSource('plan')} /> Planificado</label>
          <label className="inline-flex items-center gap-1"><input type="radio" name="src" checked={source==='actuals'} onChange={() => setSource('actuals')} /> Real</label>
          <label className="inline-flex items-center gap-1"><input type="radio" name="src" checked={source==='both'} onChange={() => setSource('both')} /> Ambos</label>
          <span className="opacity-70">({totalItems} artículos)</span>
        </div>
        <div className="space-x-2">
          <Button onClick={copy} className="h-9">Copiar</Button>
          <Button onClick={download} className="h-9" variant="secondary">Descargar CSV</Button>
          <Button onClick={clear} className="h-9" variant="ghost" title="Vaciar según la fuente seleccionada">Limpiar</Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {cats.map((cat) => (
          <div key={cat} className="rounded border p-3">
            <h3 className="mb-2 font-semibold">{cat}</h3>
            <ul className="space-y-1 text-sm">
              {grouped[cat].map((it) => (
                <li key={`${cat}-${it.name}-${it.unit || ''}`} className="flex justify-between">
                  <span>{it.name}</span>
                  <span className="text-gray-600">
                    {it.qty != null && it.unit ? `${fmtNumber(it.qty)} ${it.unit}` : `x${it.count || 1}`}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}

