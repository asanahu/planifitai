/* eslint-disable react-refresh/only-export-components */
import { create } from 'zustand';
import { useEffect } from 'react';

interface Toast {
  id: number;
  message: string;
  type?: 'success' | 'error';
}

interface ToastState {
  toasts: Toast[];
  push: (t: Omit<Toast, 'id'>) => void;
  remove: (id: number) => void;
}

let idCounter = 0;

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  push: (t) => set((state) => ({ toasts: [...state.toasts, { ...t, id: ++idCounter }] })),
  remove: (id) => set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),
}));

export function ToastContainer() {
  const { toasts, remove } = useToastStore();
  useEffect(() => {
    const timers = toasts.map((t) => setTimeout(() => remove(t.id), 4000));
    return () => timers.forEach(clearTimeout);
  }, [toasts, remove]);
  return (
    <div className="fixed top-4 right-4 z-50 space-y-2" role="status" aria-live="polite">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`rounded px-4 py-2 text-white ${t.type === 'error' ? 'bg-red-500' : 'bg-green-500'}`}
        >
          {t.message}
        </div>
      ))}
    </div>
  );
}

export function pushToast(message: string, type: 'success' | 'error' = 'success') {
  useToastStore.getState().push({ message, type });
}
