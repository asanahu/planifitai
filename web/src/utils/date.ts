function format(d: Date): string {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function nowInMadrid(): Date {
  // Usar Intl.DateTimeFormat para obtener la fecha correcta en Madrid
  const now = new Date();
  const madridFormatter = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Europe/Madrid',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  });
  
  const parts = madridFormatter.formatToParts(now);
  const year = parts.find(part => part.type === 'year')?.value;
  const month = parts.find(part => part.type === 'month')?.value;
  const day = parts.find(part => part.type === 'day')?.value;
  
  if (year && month && day) {
    return new Date(`${year}-${month}-${day}T00:00:00`);
  }
  
  // Fallback: usar fecha local
  return new Date();
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