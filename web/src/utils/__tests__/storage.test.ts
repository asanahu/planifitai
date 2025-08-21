import { describe, it, expect, beforeEach } from 'vitest';
import { getMealPlan, setMealPlan, clearMealPlan } from '../storage';

describe('storage utils', () => {
  beforeEach(() => {
    localStorage.clear();
  });
  it('sets and gets meal plan', () => {
    setMealPlan({ lunes: { comida: ['a'] } });
    expect(getMealPlan()).toHaveProperty('lunes');
  });
  it('clears meal plan', () => {
    setMealPlan({ lunes: { comida: ['a'] } });
    clearMealPlan();
    expect(getMealPlan()).toEqual({});
  });
});
