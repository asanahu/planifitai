import { useEffect, useRef } from 'react';
import { pushToast } from './ui/Toast';
import { requestBrowserNotificationPermission, notifyBrowser } from '../utils/browserNotifications';

interface PlanGenerationNotificationProps {
  isGenerating: boolean;
  onGenerationComplete: () => void;
}

export function PlanGenerationNotification({ 
  isGenerating, 
  onGenerationComplete 
}: PlanGenerationNotificationProps) {
  const hasShownStartNotification = useRef(false);
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (isGenerating && !hasShownStartNotification.current) {
      // Mostrar notificación de inicio solo una vez
      pushToast('🚀 Iniciando generación de plan de nutrición de 2 semanas...');
      requestBrowserNotificationPermission();
      hasShownStartNotification.current = true;
      
      // Mostrar notificaciones de progreso cada 45 segundos
      progressIntervalRef.current = setInterval(() => {
        pushToast('⏳ Plan en generación... La IA está trabajando en tu plan personalizado');
      }, 45000);
      
    } else if (!isGenerating && hasShownStartNotification.current) {
      // Limpiar intervalo cuando termine
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
        progressIntervalRef.current = null;
      }
      
      // Mostrar notificación de finalización
      pushToast('🎉 ¡Plan de nutrición de 2 semanas generado exitosamente!', 'success');
      notifyBrowser('Plan listo ✅', { body: 'Tu plan de nutrición ha sido generado.' });
      onGenerationComplete();
      
      // Reset para la próxima generación
      hasShownStartNotification.current = false;
    }

    // Cleanup al desmontar
    return () => {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
      }
    };
  }, [isGenerating, onGenerationComplete]);

  return null; // Este componente no renderiza nada
}
