export interface Achievement {
  id: string;
  title: string;
  icon: string;
  dateUnlocked: string;
}

export interface AchievementState {
  workoutsInRow: number;
  fullWeeks: number;
}

export function checkAchievements(
  state: AchievementState,
  existing: Achievement[] = []
): Achievement[] {
  const unlocked: Achievement[] = [];
  const has = (id: string) => existing.some((a) => a.id === id);
  if (state.fullWeeks >= 1 && !has('first-week')) {
    unlocked.push({
      id: 'first-week',
      title: '🏅 Primera semana completa',
      icon: '🏅',
      dateUnlocked: new Date().toISOString(),
    });
  }
  if (state.workoutsInRow >= 3 && !has('streak-3')) {
    unlocked.push({
      id: 'streak-3',
      title: '🔥 3 días seguidos entrenando',
      icon: '🔥',
      dateUnlocked: new Date().toISOString(),
    });
  }
  return unlocked;
}

const KEY = 'achievements:v1';

export function saveAchievements(achievements: Achievement[]) {
  localStorage.setItem(KEY, JSON.stringify(achievements));
}

export function loadAchievements(): Achievement[] {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as Achievement[]) : [];
  } catch {
    return [];
  }
}
