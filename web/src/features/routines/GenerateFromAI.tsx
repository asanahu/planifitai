import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createRoutineFromAI } from '../../api/routines';
import { useNavigate } from 'react-router-dom';

export default function GenerateFromAI() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const mutation = useMutation({
    mutationFn: () => createRoutineFromAI(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['routines'] });
      navigate('/workout');
    }
  });
  return (
    <button
      className="btn"
      onClick={() => mutation.mutate()}
    >
      Generar plan demo
    </button>
  );
}
