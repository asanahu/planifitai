export interface AchievementBadgeProps {
  title: string;
  icon: string;
  dateUnlocked: string;
}

export function AchievementBadge({ title, icon, dateUnlocked }: AchievementBadgeProps) {
  return (
    <div className="flex items-center gap-2 rounded bg-yellow-100 px-2 py-1 text-xs">
      <span>{icon}</span>
      <span>{title}</span>
      <span className="text-[10px] text-gray-500">{new Date(dateUnlocked).toLocaleDateString()}</span>
    </div>
  );
}

export default AchievementBadge;
