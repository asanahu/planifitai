import { describe, it, expect } from 'vitest';
import { mapAiNutritionPlanToLocal } from '../aiMap';

describe('mapAiNutritionPlanToLocal', () => {
  it('maps plan', () => {
    const plan = mapAiNutritionPlanToLocal({
      days: [
        { day: 'Mon', meals: [{ name: 'Breakfast', items: ['Eggs'] }] },
      ],
    });
    expect(plan['Mon'].Breakfast[0]).toBe('Eggs');
  });
});
