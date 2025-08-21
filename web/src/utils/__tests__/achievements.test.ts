import { describe, it, expect } from 'vitest';
import { checkAchievements, type Achievement } from '../achievements';

describe('achievements', () => {
  it('unlocks streak achievement', () => {
    const res = checkAchievements({ workoutsInRow: 3, fullWeeks: 0 });
    expect(res.find((a: Achievement) => a.id === 'streak-3')).toBeTruthy();
  });

  it('respects existing achievements', () => {
    const existing: Achievement[] = [
      { id: 'streak-3', title: '', icon: '', dateUnlocked: '' },
    ];
    const res = checkAchievements({ workoutsInRow: 5, fullWeeks: 1 }, existing);
    expect(res.find((a) => a.id === 'streak-3')).toBeFalsy();
    expect(res.find((a) => a.id === 'first-week')).toBeTruthy();
  });
});
