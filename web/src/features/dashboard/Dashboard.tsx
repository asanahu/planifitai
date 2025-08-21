import { today } from "../../utils/date";
import type { DayLog } from "../../api/nutrition";
import { useQuery } from '@tanstack/react-query';
import { getDayLog, addWater } from '../../api/nutrition';
import { addEntry } from '../../api/progress';
import { useState } from 'react';

export function Dashboard() {
  const date = today();
  const { data: dayLog } = useQuery<DayLog>({ queryKey: ['nutrition-day', date], queryFn: () => getDayLog(date) });
  const [weight, setWeight] = useState('');

  const submitWeight = async () => {
    await addEntry({ metric: 'weight', value: parseFloat(weight), date: date });
    setWeight('');
  };

  return (
    <div className="p-4 space-y-4">
      <section className="border p-4 rounded">
        <h2 className="font-bold mb-2">Comidas de hoy</h2>
        {dayLog ? (
          <div>
            <p>Calorías: {dayLog.calories} / {dayLog.targets.calories}</p>
            <button onClick={() => addWater(250)} className="mt-2 bg-blue-500 text-white px-2 py-1 rounded">Añadir agua (250ml)</button>
          </div>
        ) : (
          <p>Cargando...</p>
        )}
      </section>
      <section className="border p-4 rounded">
        <h2 className="font-bold mb-2">Peso rápido</h2>
        <div className="flex space-x-2">
          <input value={weight} onChange={(e) => setWeight(e.target.value)} placeholder="kg" className="border p-2 flex-1" />
          <button onClick={submitWeight} className="bg-blue-500 text-white px-4 py-2 rounded">Guardar</button>
        </div>
      </section>
    </div>
  );
}
