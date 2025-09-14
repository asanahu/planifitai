export interface AsyncNutritionPlanStatus {
  status: 'PENDING' | 'PROGRESS' | 'SUCCESS' | 'FAILURE';
  progress: number;
  step?: string;
  message?: string;
  plan?: any;
  generated_at?: string;
  days_generated?: number;
  strategy?: string;
  targets?: any;
  error?: string;
  error_type?: string;
  failed_at?: string;
}

export interface AsyncNutritionPlanResponse {
  task_id: string;
  status: string;
  message: string;
  estimated_time?: string;
  strategy?: string;
  plan?: any;
  days_generated?: number;
  targets?: any;
}