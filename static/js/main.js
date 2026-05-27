// ============================================================
// DIFERENT 777 — MAIN JS
// ============================================================

// CLOCK
function updateClock() {
  const el = document.getElementById('clock');
  if (el) el.textContent = new Date().toLocaleTimeString('es-CO', {hour:'2-digit',minute:'2-digit',second:'2-digit'});
}
setInterval(updateClock, 1000);
updateClock();

// FRACTAL CANVAS
function initFractal() {
  const canvas = document.getElementById('fractalCanvas');
  if (!canvas) return;
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  const ctx = canvas.getContext('2d');

  function sierpinski(x, y, size, depth) {
    if (depth <= 0 || size < 6) return;
    const h = size * (Math.sqrt(3) / 2);
    ctx.beginPath();
    ctx.moveTo(x, y - h * 2 / 3);
    ctx.lineTo(x - size / 2, y + h / 3);
    ctx.lineTo(x + size / 2, y + h / 3);
    ctx.closePath();
    ctx.strokeStyle = `rgba(212,160,23,${0.1 * (depth / 5)})`;
    ctx.lineWidth = 0.5;
    ctx.stroke();
    sierpinski(x, y - h * 2 / 3, size / 2, depth - 1);
    sierpinski(x - size / 4, y + h / 6, size / 2, depth - 1);
    sierpinski(x + size / 4, y + h / 6, size / 2, depth - 1);
  }

  function kochSegment(x1, y1, x2, y2, depth) {
    if (depth <= 0) {
      ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2);
      ctx.strokeStyle = 'rgba(124,77,255,0.07)'; ctx.lineWidth = 0.3; ctx.stroke();
      return;
    }
    const dx = (x2-x1)/3, dy = (y2-y1)/3;
    const ax=x1+dx, ay=y1+dy, bx=x2-dx, by=y2-dy;
    const mx=(x1+x2)/2-Math.sqrt(3)*(y2-y1)/6;
    const my=(y1+y2)/2+Math.sqrt(3)*(x2-x1)/6;
    kochSegment(x1,y1,ax,ay,depth-1);
    kochSegment(ax,ay,mx,my,depth-1);
    kochSegment(mx,my,bx,by,depth-1);
    kochSegment(bx,by,x2,y2,depth-1);
  }

  const W = canvas.width, H = canvas.height;
  sierpinski(W * 0.15, H * 0.35, 350, 5);
  sierpinski(W * 0.82, H * 0.25, 280, 4);
  sierpinski(W * 0.5, H * 0.78, 300, 4);
  kochSegment(0, H * 0.5, W * 0.35, H * 0.5, 3);
  kochSegment(W * 0.65, H * 0.1, W, H * 0.65, 3);
}

window.addEventListener('load', initFractal);
window.addEventListener('resize', initFractal);

// TOAST
function showToast(msg, type = 'success') {
  const icons = { success: '✓', error: '✕', info: 'ℹ' };
  const container = document.getElementById('toastContainer') || (() => {
    const d = document.createElement('div');
    d.id = 'toastContainer';
    d.className = 'toast-container';
    document.body.appendChild(d);
    return d;
  })();
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icons[type] || '•'}</span><span>${msg}</span>`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}

// CONFIRM DELETE
function confirmAction(msg, formId) {
  if (confirm(msg)) {
    document.getElementById(formId).submit();
  }
}

// FORMAT COP
function fmtCOP(n) {
  return '$' + Math.round(n).toLocaleString('es-CO');
}

// AUTO-DISMISS ALERTS
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.alert[data-auto-dismiss]').forEach(a => {
    setTimeout(() => a.remove(), 4000);
  });
});

// MOBILE SIDEBAR TOGGLE
function toggleSidebar() {
  document.querySelector('.sidebar').classList.toggle('open');
}
