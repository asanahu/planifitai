import type { Meal } from '../../api/nutrition';

interface Props {
  meal?: Meal;
  onSave: (data: { name: string }) => void;
  onCancel: () => void;
}

export default function MealEditor({ meal, onSave, onCancel }: Props) {
  let name = meal?.name ?? '';
  return (
    <div className="space-y-2">
      <input
        className="input"
        defaultValue={name}
        onChange={(e) => (name = e.target.value)}
      />
      <div className="space-x-2">
        <button className="btn" onClick={() => onSave({ name })}>Guardar</button>
        <button className="btn" onClick={onCancel}>Cancelar</button>
      </div>
    </div>
  );
}
