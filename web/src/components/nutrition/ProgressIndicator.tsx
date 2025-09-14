import React from 'react';
import type { AsyncNutritionPlanStatus } from '../../types/nutrition';

interface ProgressIndicatorProps {
  status: AsyncNutritionPlanStatus | null;
  isGenerating: boolean;
}

export function ProgressIndicator({ status, isGenerating }: ProgressIndicatorProps) {
  if (!isGenerating || !status) return null;

  const getStepIcon = (step: string) => {
    switch (step) {
      case 'analyzing_profile':
        return '🔍';
      case 'generating_base_week':
        return '📅';
      case 'creating_variations':
        return '🔄';
      case 'combining_plans':
        return '🔗';
      case 'completed':
        return '✅';
      default:
        return '⚙️';
    }
  };

  const getStepDescription = (step: string) => {
    switch (step) {
      case 'analyzing_profile':
        return 'Analizando tu perfil nutricional...';
      case 'generating_base_week':
        return 'Generando plan base de 7 días...';
      case 'creating_variations':
        return 'Creando variaciones inteligentes...';
      case 'combining_plans':
        return 'Combinando planes de ambas semanas...';
      case 'completed':
        return '¡Plan generado exitosamente!';
      default:
        return 'Procesando...';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 max-w-md mx-auto">
      <div className="text-center space-y-4">
        {/* Título */}
        <div className="text-lg font-semibold text-gray-800">
          Generando tu plan de nutrición de 2 semanas
        </div>

        {/* Paso actual */}
        <div className="flex items-center justify-center space-x-2">
          <span className="text-2xl">{getStepIcon(status.step || 'processing')}</span>
          <span className="text-sm text-gray-600">
            {status.message || getStepDescription(status.step || 'processing')}
          </span>
        </div>

        {/* Barra de progreso */}
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div 
            className="bg-gradient-to-r from-blue-500 to-green-500 h-3 rounded-full transition-all duration-1000 ease-out"
            style={{ width: `${status.progress}%` }}
          ></div>
        </div>

        {/* Porcentaje */}
        <div className="text-sm font-medium text-gray-700">
          {status.progress}% completado
        </div>

        {/* Información adicional */}
        <div className="text-xs text-gray-500 space-y-1">
          <div>Estrategia: Plan base + variaciones inteligentes</div>
          <div>Tiempo estimado: 45-90 segundos</div>
          <div className="text-green-600">
            ✨ Generando 14 días completos con IA
          </div>
        </div>

        {/* Spinner */}
        <div className="flex justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>

        {/* Mensaje de paciencia */}
        <div className="text-xs text-gray-400 italic">
          La IA está creando un plan personalizado para ti. ¡No cierres esta ventana!
        </div>
      </div>
    </div>
  );
}

interface GenerationCompleteProps {
  plan: any;
  generatedAt: string;
  daysGenerated: number;
  strategy: string;
}

export function GenerationComplete({ 
  plan, 
  generatedAt, 
  daysGenerated, 
  strategy 
}: GenerationCompleteProps) {
  return (
    <div className="bg-green-50 border border-green-200 rounded-lg p-6 max-w-md mx-auto">
      <div className="text-center space-y-4">
        {/* Icono de éxito */}
        <div className="text-4xl">🎉</div>
        
        {/* Título */}
        <div className="text-lg font-semibold text-green-800">
          ¡Plan generado exitosamente!
        </div>

        {/* Detalles */}
        <div className="text-sm text-green-700 space-y-1">
          <div>✅ {daysGenerated} días generados</div>
          <div>🧠 Estrategia: {strategy}</div>
          <div>⏰ Generado: {new Date(generatedAt).toLocaleString()}</div>
        </div>

        {/* Objetivos nutricionales */}
        {plan?.targets && (
          <div className="bg-white rounded p-3 text-xs">
            <div className="font-medium text-gray-800 mb-2">Objetivos nutricionales:</div>
            <div className="grid grid-cols-2 gap-2 text-gray-600">
              <div>Calorías: {plan.targets.kcal}</div>
              <div>Proteína: {plan.targets.protein_g}g</div>
              <div>Carbohidratos: {plan.targets.carbs_g}g</div>
              <div>Grasas: {plan.targets.fat_g}g</div>
            </div>
          </div>
        )}

        {/* Mensaje de éxito */}
        <div className="text-sm text-green-600">
          Tu plan personalizado está listo para usar
        </div>
      </div>
    </div>
  );
}

interface GenerationErrorProps {
  error: string;
  errorType?: string;
  failedAt?: string;
}

export function GenerationError({ error, errorType, failedAt }: GenerationErrorProps) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md mx-auto">
      <div className="text-center space-y-4">
        {/* Icono de error */}
        <div className="text-4xl">❌</div>
        
        {/* Título */}
        <div className="text-lg font-semibold text-red-800">
          Error generando el plan
        </div>

        {/* Error details */}
        <div className="text-sm text-red-700 space-y-1">
          <div className="font-medium">Error: {error}</div>
          {errorType && <div>Tipo: {errorType}</div>}
          {failedAt && <div>Falló: {new Date(failedAt).toLocaleString()}</div>}
        </div>

        {/* Sugerencias */}
        <div className="text-xs text-red-600">
          <div>💡 Intenta nuevamente en unos momentos</div>
          <div>💡 Verifica tu conexión a internet</div>
          <div>💡 Contacta soporte si el problema persiste</div>
        </div>
      </div>
    </div>
  );
}
