import { useState, useCallback, useRef, useEffect } from 'react';
import { apiFetch } from '../api/client';
import type { AsyncNutritionPlanStatus, AsyncNutritionPlanResponse } from '../types/nutrition';

export function useAsyncNutritionPlanSSE() {
  const [taskId, setTaskId] = useState<string | null>(null);
  const [status, setStatus] = useState<AsyncNutritionPlanStatus | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const generatePlan = useCallback(async (preferences: any, days: number = 14) => {
    try {
      setIsGenerating(true);
      setError(null);
      setTaskId(null);
      setStatus(null);

      // Iniciar generación asíncrona
      const response = await apiFetch<AsyncNutritionPlanResponse>(
        '/ai/generate/nutrition-plan-14-days-async',
        {
          method: 'POST',
          body: JSON.stringify({ 
            days, 
            preferences 
          })
        }
      );

      setTaskId(response.task_id);

      // Conectar a SSE stream
      const eventSource = new EventSource(`/api/v1/ai/generate/nutrition-plan-stream/${response.task_id}`);
      eventSourceRef.current = eventSource;

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setStatus(data);

          if (data.status === 'SUCCESS') {
            stopSSE();
            setIsGenerating(false);
            setTaskId(null);
          } else if (data.status === 'FAILURE') {
            stopSSE();
            setError(data.error || 'Error desconocido');
            setIsGenerating(false);
            setTaskId(null);
          }
        } catch (parseError) {
          console.error('Error parsing SSE data:', parseError);
        }
      };

      eventSource.onerror = (error) => {
        console.error('SSE error:', error);
        stopSSE();
        setError('Error de conexión con el servidor');
        setIsGenerating(false);
        setTaskId(null);
      };

    } catch (err: any) {
      console.error('Error iniciando generación:', err);
      setError(err.message || 'Error iniciando la generación del plan');
      setIsGenerating(false);
    }
  }, []);

  const stopSSE = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }, []);

  const cancelGeneration = useCallback(async () => {
    if (!taskId) return;

    try {
      // Detener SSE inmediatamente
      stopSSE();

      await apiFetch(`/ai/generate/nutrition-plan-cancel/${taskId}`, {
        method: 'DELETE'
      });
      
      setIsGenerating(false);
      setTaskId(null);
      setStatus(null);
    } catch (err: any) {
      console.error('Error cancelando generación:', err);
    }
  }, [taskId, stopSSE]);

  const reset = useCallback(() => {
    // Detener SSE si está activo
    stopSSE();
    
    setTaskId(null);
    setStatus(null);
    setIsGenerating(false);
    setError(null);
  }, [stopSSE]);

  // Cleanup al desmontar el componente
  useEffect(() => {
    return () => {
      stopSSE();
    };
  }, [stopSSE]);

  return {
    generatePlan,
    cancelGeneration,
    reset,
    taskId,
    status,
    isGenerating,
    error,
    progress: status?.progress || 0,
    plan: status?.plan,
    isComplete: status?.status === 'SUCCESS',
    isFailed: status?.status === 'FAILURE'
  };
}
