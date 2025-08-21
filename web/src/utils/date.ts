function format(d: Date): string {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function nowInMadrid(): Date {
  const now = new Date();
  const tz = now.toLocaleString('en-US', { timeZone: 'Europe/Madrid' });
  return new Date(tz);
}

export function today(): string {
  return format(nowInMadrid());
}

export function daysAgo(days: number): string {
  const d = nowInMadrid();
  d.setDate(d.getDate() - days);
  return format(d);
}

export function startOfWeek(d: Date): Date {
  const day = d.getDay();
  const diff = (day + 6) % 7; // monday start
  const result = new Date(d);
  result.setDate(d.getDate() - diff);
  return result;
}
