import { describe, it, expect, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import GeneratePlanFromAI from '../GeneratePlanFromAI';
import * as ai from '../../../api/ai';
import * as storage from '../../../utils/storage';

describe('GeneratePlanFromAI', () => {
  it('stores plan locally', async () => {
    vi.stubEnv('VITE_USE_AI_NUTRITION_GENERATOR', 'true');
    vi.spyOn(ai, 'generateNutritionPlanAI').mockResolvedValue({ days: [] });
    const setSpy = vi.spyOn(storage, 'setMealPlan');
    const qc = new QueryClient();
    render(
      <QueryClientProvider client={qc}>
        <GeneratePlanFromAI />
      </QueryClientProvider>
    );
    await userEvent.click(screen.getByText('Generar plan IA'));
    expect(setSpy).toHaveBeenCalled();
  });
});
