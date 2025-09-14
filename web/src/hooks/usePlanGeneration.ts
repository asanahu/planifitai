import { useState, useCallback } from 'react';

interface GenerationState {
  isGenerating: boolean;
  startTime: number | null;
  estimatedTime: number; // en segundos
}

export function usePlanGeneration() {
  const [state, setState] = useState<GenerationState>({
    isGenerating: false,
    startTime: null,
    estimatedTime: 120 // 2 minutos por defecto
  });

  const startGeneration = useCallback(() => {
    setState({
      isGenerating: true,
      startTime: Date.now(),
      estimatedTime: 120
    });
  }, []);

  const finishGeneration = useCallback(() => {
    setState({
      isGenerating: false,
      startTime: null,
      estimatedTime: 120
    });
  }, []);

  const getElapsedTime = useCallback(() => {
    if (!state.startTime) return 0;
    return Math.floor((Date.now() - state.startTime) / 1000);
  }, [state.startTime]);

  const getRemainingTime = useCallback(() => {
    const elapsed = getElapsedTime();
    return Math.max(0, state.estimatedTime - elapsed);
  }, [getElapsedTime, state.estimatedTime]);

  const getProgressPercentage = useCallback(() => {
    const elapsed = getElapsedTime();
    return Math.min(100, (elapsed / state.estimatedTime) * 100);
  }, [getElapsedTime, state.estimatedTime]);

  return {
    ...state,
    startGeneration,
    finishGeneration,
    getElapsedTime,
    getRemainingTime,
    getProgressPercentage
  };
}
