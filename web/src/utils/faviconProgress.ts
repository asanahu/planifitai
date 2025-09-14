let originalHref: string | null = null;
let canvas: HTMLCanvasElement | null = null;
let ctx: CanvasRenderingContext2D | null = null;

function getFaviconLink(): HTMLLinkElement | null {
  return document.querySelector("link[rel~='icon']") as HTMLLinkElement | null;
}

function ensureCanvas() {
  if (!canvas) {
    canvas = document.createElement('canvas');
    canvas.width = 64;
    canvas.height = 64;
    ctx = canvas.getContext('2d');
  }
}

export function startFaviconProgress(): void {
  const link = getFaviconLink();
  if (!link) return;
  if (!originalHref) originalHref = link.href;
}

export function setFaviconProgress(progressPercent: number, label?: string): void {
  const link = getFaviconLink();
  if (!link) return;
  ensureCanvas();
  if (!ctx || !canvas) return;

  // Background
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Base circle
  const cx = 32;
  const cy = 32;
  const r = 28;
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.fillStyle = '#f1f5f9';
  ctx.fill();

  // Progress arc (redondeado a múltiplos de 5)
  const clamped = Math.max(0, Math.min(100, progressPercent));
  const rounded = Math.round(clamped / 5) * 5;
  const p = rounded / 100;
  ctx.beginPath();
  ctx.arc(cx, cy, r, -Math.PI / 2, -Math.PI / 2 + (Math.PI * 2 * p));
  ctx.strokeStyle = '#2563eb';
  ctx.lineWidth = 6;
  ctx.stroke();

  // Text
  ctx.fillStyle = '#111827';
  ctx.font = 'bold 24px system-ui, -apple-system, Segoe UI, Roboto';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  const txt = label ?? `${rounded}`;
  ctx.fillText(txt, cx, cy);

  link.href = canvas.toDataURL('image/png');
}

export function endFaviconProgress(): void {
  const link = getFaviconLink();
  if (!link) return;
  if (originalHref) link.href = originalHref;
  originalHref = null;
}


