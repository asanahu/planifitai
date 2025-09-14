import React from 'react';
import { mapAiNutritionPlanToLocal } from './aiMap';
import type { AsyncNutritionPlanResponse } from '../../types/nutrition';
import { setMealPlanForWeek } from '../../utils/storage';
import { pushToast } from '../../components/ui/Toast';
import Overlay from '../../components/ui/Overlay';
import { useAsyncNutritionPlan } from '../../hooks/useAsyncNutritionPlan';
// import type { AsyncNutritionPlanStatus } from '../../types/nutrition';
import { ProgressIndicator, GenerationComplete, GenerationError } from '../../components/nutrition/ProgressIndicator';
import { requestBrowserNotificationPermission, notifyBrowser } from '../../utils/browserNotifications';
import Modal from '../../components/ui/Modal';
import Button from '../../components/ui/button';
import { startFaviconProgress, setFaviconProgress, endFaviconProgress } from '../../utils/faviconProgress';

export default function GeneratePlanFromAI() {
  const useAI = import.meta.env.VITE_FEATURE_AI === '1';
  const { 
    generatePlan,
    cancelGeneration,
    reset,
    status,
    isGenerating,
    error,
    plan,
    isComplete,
    isFailed
  } = useAsyncNutritionPlan();
  const [showBackgroundModal, setShowBackgroundModal] = React.useState(false);
  const [sendToBackground, setSendToBackground] = React.useState(false);
  const lastNotifiedProgressRef = React.useRef<number>(-10);
  const lastNotifiedStepRef = React.useRef<string | undefined>(undefined);
  
  const handleGeneratePlan = async () => {
    if (!useAI) {
      pushToast('IA deshabilitada. Configura VITE_FEATURE_AI=1', 'error');
      return;
    }

    try {
      setShowBackgroundModal(true);
    } catch (err: any) {
      console.error('Error generando plan:', err);
      pushToast(`Error: ${err.message || 'Error desconocido'}`, 'error');
    }
  };

  const handlePlanComplete = () => {
    if (plan) {
      // Mapear el plan de IA a formato local
      const localPlan = mapAiNutritionPlanToLocal(plan);
      
      console.log('Plan local mapeado:', localPlan); // Debug
      
      // Para un plan de 14 días, necesitamos distribuir los días correctamente
      // const dayKeys = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
      const week1Plan: any = {};
      const week2Plan: any = {};
      
      // El plan de IA viene con 14 días secuenciales con claves únicas
      const allDays = Object.keys(localPlan);
      console.log('Días disponibles:', allDays); // Debug
      
      // Separar días por semana basándose en las claves
      allDays.forEach(dayKey => {
        if (dayKey.includes('_W')) {
          // Días de semana 2 (tienen sufijo _W2)
          const baseDayKey = dayKey.split('_W')[0];
          week2Plan[baseDayKey] = localPlan[dayKey];
        } else {
          // Días de semana 1 (sin sufijo)
          week1Plan[dayKey] = localPlan[dayKey];
        }
      });
      
      // Guardar planes
      setMealPlanForWeek('week1', week1Plan);
      setMealPlanForWeek('week2', week2Plan);
      
      console.log('Week1 plan:', week1Plan); // Debug
      console.log('Week2 plan:', week2Plan); // Debug
      
      pushToast(`Plan de 14 días generado exitosamente - ${allDays.length} días mapeados`);
    }
  };

  // Efecto para manejar cuando el plan está completo
  React.useEffect(() => {
    if (isComplete && plan) {
      handlePlanComplete();
      if (sendToBackground) {
        notifyBrowser('Plan IA generado ✅', { body: 'El plan ya está disponible en tu planificador.' });
      }
    }
  }, [isComplete, plan]);

  const startWithMode = async (background: boolean) => {
    try {
      setShowBackgroundModal(false);
      setSendToBackground(background);
      if (background) await requestBrowserNotificationPermission();
      startFaviconProgress();
      setFaviconProgress(0);
      const resp = (await generatePlan({}, 14)) as unknown as AsyncNutritionPlanResponse | undefined;
      const planData = resp?.plan || status?.plan;
      if (planData) {
        const localPlan = mapAiNutritionPlanToLocal(planData as any);
        const allDays = Object.keys(localPlan);
        const week1Plan: any = {};
        const week2Plan: any = {};
        allDays.forEach((dayKey) => {
          if (dayKey.includes('_W')) {
            const baseDayKey = dayKey.split('_W')[0];
            week2Plan[baseDayKey] = (localPlan as any)[dayKey];
          } else {
            week1Plan[dayKey] = (localPlan as any)[dayKey];
          }
        });
        setMealPlanForWeek('week1', week1Plan);
        setMealPlanForWeek('week2', week2Plan);
        pushToast('Plan IA volcado a planificado (semana 1 y 2)');
      }
      if (background) {
        pushToast('Generación enviada a segundo plano. Te avisaremos al terminar.');
      }
    } catch (err: any) {
      pushToast(`Error: ${err.message || 'Error desconocido'}`, 'error');
      endFaviconProgress();
    }
  };

  // Notificaciones de progreso en segundo plano (throttled)
  React.useEffect(() => {
    if (!sendToBackground || !status) return;
    const st = status.status;
    if (st === 'PROGRESS') {
      const p = Math.max(0, Math.min(100, status.progress || 0));
      setFaviconProgress(p);
      const step = status.step;
      const shouldNotifyByProgress = p >= (lastNotifiedProgressRef.current + 10);
      const stepChanged = step && step !== lastNotifiedStepRef.current;
      if (shouldNotifyByProgress || stepChanged) {
        notifyBrowser(`Generando plan (${p}%)`, { body: step ? `Paso: ${step}` : status.message || 'Procesando...' });
        lastNotifiedProgressRef.current = p;
        lastNotifiedStepRef.current = step;
      }
    } else if (st === 'SUCCESS') {
      notifyBrowser('Plan listo ✅', { body: 'Tu plan de 2 semanas ha sido generado.' });
      setFaviconProgress(100);
      setTimeout(endFaviconProgress, 1000);
      lastNotifiedProgressRef.current = -10;
      lastNotifiedStepRef.current = undefined;
    } else if (st === 'FAILURE') {
      notifyBrowser('Error al generar ❌', { body: status.error || 'Hubo un problema generando tu plan.' });
      endFaviconProgress();
      lastNotifiedProgressRef.current = -10;
      lastNotifiedStepRef.current = undefined;
    }
  }, [sendToBackground, status]);

  return (
    <div className="space-y-4">
      <Modal
        isOpen={showBackgroundModal}
        onClose={() => setShowBackgroundModal(false)}
        title="Generar plan con IA"
        description={
          <div className="space-y-2 text-sm">
            <p>La generación tarda ~30-60s. ¿Deseas enviarla a segundo plano?</p>
            <ul className="list-inside list-disc opacity-80">
              <li>Si eliges segundo plano, te avisaremos al terminar.</li>
              <li>Podrás navegar por la app mientras tanto.</li>
            </ul>
          </div>
        }
        footer={
          <>
            <Button variant="ghost" onClick={() => setShowBackgroundModal(false)}>Cancelar</Button>
            <Button variant="secondary" onClick={() => startWithMode(false)}>Esperar aquí</Button>
            <Button onClick={() => startWithMode(true)}>Enviar a segundo plano</Button>
          </>
        }
      />
      {/* Botón de generación */}
      <div className="flex space-x-2">
        <button
          className="btn"
          disabled={isGenerating}
          onClick={handleGeneratePlan}
        >
          {isGenerating ? 'Generando plan…' : 'Generar plan IA (2 semanas)'}
        </button>
        
        {isGenerating && (
          <button
            className="btn btn-secondary"
            onClick={cancelGeneration}
          >
            Cancelar
          </button>
        )}
        
        {(isComplete || isFailed) && (
          <button
            className="btn btn-outline"
            onClick={reset}
          >
            Generar nuevo plan
          </button>
        )}
      </div>
      
      {/* Indicador de progreso */}
      {isGenerating && !sendToBackground && (
        <Overlay>
          <ProgressIndicator status={status} isGenerating={isGenerating} />
        </Overlay>
      )}
      
      {/* Plan completado */}
      {isComplete && status && (
        <GenerationComplete
          plan={status.plan}
          generatedAt={status.generated_at || ''}
          daysGenerated={status.days_generated || 0}
          strategy={status.strategy || 'standard'}
        />
      )}
      
      {/* Error */}
      {isFailed && status && (
        <GenerationError
          error={status.error || 'Error desconocido'}
          errorType={status.error_type}
          failedAt={status.failed_at}
        />
      )}
      
      {/* Error del hook */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-4">
          <div className="text-red-800 font-medium">Error:</div>
          <div className="text-red-600 text-sm">{error}</div>
        </div>
      )}
    </div>
  );
}

