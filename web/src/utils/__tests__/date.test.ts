import { describe, it, expect } from 'vitest';
import { today, daysAgo, startOfWeek } from '../date';

describe('date utils', () => {
  it('formats today as YYYY-MM-DD', () => {
    const t = today();
    expect(t).toMatch(/\d{4}-\d{2}-\d{2}/);
  });
  it('calculates daysAgo', () => {
    const d = daysAgo(1);
    expect(d).toMatch(/\d{4}-\d{2}-\d{2}/);
  });
  it('gets start of week on Monday', () => {
    const d = new Date('2024-05-15'); // Wednesday
    const start = startOfWeek(d);
    expect(start.toISOString().slice(0, 10)).toBe('2024-05-13');
  });
});
