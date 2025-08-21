import { useMemo } from 'react';
import { getMealPlan } from '../../utils/storage';

export default function ShoppingList() {
  const plan = getMealPlan();
  const items = useMemo(() => {
    const map: Record<string, number> = {};
    Object.values(plan).forEach((meals) => {
      Object.values(meals).forEach((arr) => {
        arr.forEach((i) => {
          map[i] = (map[i] || 0) + 1;
        });
      });
    });
    return Object.entries(map);
  }, [plan]);

  const copy = () => {
    const text = items.map(([name, qty]) => `${name} x${qty}`).join('\n');
    navigator.clipboard.writeText(text);
    alert('Copiado');
  };

  const download = () => {
    const csv = items.map(([name, qty]) => `${name},${qty}`).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'shopping-list.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4">
      <ul className="space-y-1">
        {items.map(([name, qty]) => (
          <li key={name}>{name} x{qty}</li>
        ))}
      </ul>
      <div className="space-x-2">
        <button className="btn" onClick={copy}>Copiar</button>
        <button className="btn" onClick={download}>Descargar CSV</button>
      </div>
    </div>
  );
}
