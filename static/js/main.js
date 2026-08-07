// ============================================================
// DIFERENT 777 — MAIN JS (VERSIÓN COMPLETA CON TEMAS)
// ============================================================

// ---------- TEMA (claro / oscuro) ----------
const ThemeManager = (function () {
  const STORAGE_KEY = 'd777-theme';
  const root = document.documentElement;

  function getTheme() {
    return root.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
  }

  function reflectUI(theme) {
    const icon = theme === 'light' ? '☀️' : '🌙';
    document.querySelectorAll('[data-theme-icon]').forEach(el => {
      el.textContent = icon;
    });
    document.querySelectorAll('[data-theme-toggle]').forEach(btn => {
      btn.setAttribute('aria-pressed', String(theme === 'light'));
    });
    // Actualizar meta theme-color para la barra del navegador
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) {
      const color = theme === 'light' ? '#f6f5f2' : '#0a0a0f';
      meta.setAttribute('content', color);
    }
  }

  function setTheme(theme) {
    root.setAttribute('data-theme', theme);
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch (e) { /* no disponible */ }
    reflectUI(theme);
    document.dispatchEvent(new CustomEvent('themechange', { detail: { theme } }));
  }

  function toggle() {
    setTheme(getTheme() === 'light' ? 'dark' : 'light');
  }

  function init() {
    // Aplicar tema guardado o preferencia del sistema
    const stored = localStorage.getItem(STORAGE_KEY);
    let theme;
    if (stored) {
      theme = stored;
    } else {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      theme = prefersDark ? 'dark' : 'light';
    }
    setTheme(theme);
    
    // Conectar botones de toggle
    document.querySelectorAll('[data-theme-toggle]').forEach(btn => {
      btn.addEventListener('click', toggle);
    });
    
    // Escuchar cambios de preferencia del sistema
    try {
      window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', (e) => {
        if (!localStorage.getItem(STORAGE_KEY)) {
          setTheme(e.matches ? 'light' : 'dark');
        }
      });
    } catch (e) { /* navegador antiguo */ }
  }

  return { getTheme, setTheme, toggle, init };
})();

// ---------- CLOCK ----------
function updateClock() {
  const el = document.getElementById('clock');
  if (el) {
    el.textContent = new Date().toLocaleTimeString('es-CO', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  }
}
setInterval(updateClock, 1000);
updateClock();

// ---------- FRACTAL CANVAS (sensible al tema) ----------
function initFractal() {
  const canvas = document.getElementById('fractalCanvas');
  if (!canvas) return;
  
  const ctx = canvas.getContext('2d');
  const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
  let rafId = null;
  let isAnimating = !reducedMotionQuery.matches;

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }

  function cssVar(name, fallback) {
    const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
  }

  function hexToRgb(hex) {
    hex = hex.replace('#', '').trim();
    if (hex.length === 3) hex = hex.split('').map(c => c + c).join('');
    const num = parseInt(hex, 16);
    if (Number.isNaN(num)) return '212,160,23';
    return `${(num >> 16) & 255},${(num >> 8) & 255},${num & 255}`;
  }

  function getPalette() {
    const isLight = ThemeManager.getTheme() === 'light';
    const gold = hexToRgb(cssVar('--gold', '#d4a017'));
    const purple = hexToRgb(cssVar('--purple', '#bb86fc'));
    
    return {
      from: isLight ? '#f6f5f2' : '#0a0a0f',
      to: isLight ? '#ebe9e4' : '#050508',
      gold: gold,
      purple: purple,
      goldAlpha: isLight ? 0.16 : 0.1,
      purpleAlpha: isLight ? 0.12 : 0.07,
      waveAlpha: isLight ? 0.05 : 0.02
    };
  }

  function sierpinski(x, y, size, depth, rgb, alpha) {
    if (depth <= 0 || size < 6) return;
    const h = size * (Math.sqrt(3) / 2);
    ctx.beginPath();
    ctx.moveTo(x, y - h * 2 / 3);
    ctx.lineTo(x - size / 2, y + h / 3);
    ctx.lineTo(x + size / 2, y + h / 3);
    ctx.closePath();
    ctx.strokeStyle = `rgba(${rgb},${alpha * (depth / 5)})`;
    ctx.lineWidth = 0.5;
    ctx.stroke();
    sierpinski(x, y - h * 2 / 3, size / 2, depth - 1, rgb, alpha);
    sierpinski(x - size / 4, y + h / 6, size / 2, depth - 1, rgb, alpha);
    sierpinski(x + size / 4, y + h / 6, size / 2, depth - 1, rgb, alpha);
  }

  function kochSegment(x1, y1, x2, y2, depth, rgb, alpha) {
    if (depth <= 0) {
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.strokeStyle = `rgba(${rgb},${alpha})`;
      ctx.lineWidth = 0.3;
      ctx.stroke();
      return;
    }
    const dx = (x2 - x1) / 3, dy = (y2 - y1) / 3;
    const ax = x1 + dx, ay = y1 + dy;
    const bx = x2 - dx, by = y2 - dy;
    const mx = (x1 + x2) / 2 - Math.sqrt(3) * (y2 - y1) / 6;
    const my = (y1 + y2) / 2 + Math.sqrt(3) * (x2 - x1) / 6;
    kochSegment(x1, y1, ax, ay, depth - 1, rgb, alpha);
    kochSegment(ax, ay, mx, my, depth - 1, rgb, alpha);
    kochSegment(mx, my, bx, by, depth - 1, rgb, alpha);
    kochSegment(bx, by, x2, y2, depth - 1, rgb, alpha);
  }

  function drawWaves(time, pal) {
    const W = canvas.width, H = canvas.height;
    for (let i = 0; i < 3; i++) {
      ctx.beginPath();
      for (let x = 0; x < W; x += 30) {
        const y = H - 30 + 
          Math.sin(x * 0.008 + time + i * 2) * 20 + 
          Math.cos(x * 0.012 - time + i) * 15;
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.lineTo(W, H);
      ctx.lineTo(0, H);
      ctx.fillStyle = `rgba(${pal.gold},${Math.max(pal.waveAlpha - i * 0.006, 0)})`;
      ctx.fill();
    }
  }

  function paint() {
    const pal = getPalette();
    const W = canvas.width, H = canvas.height;
    
    // Fondo con gradiente
    const gradient = ctx.createLinearGradient(0, 0, W, H);
    gradient.addColorStop(0, pal.from);
    gradient.addColorStop(1, pal.to);
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, W, H);

    // Fractales
    sierpinski(W * 0.15, H * 0.35, 350, 5, pal.gold, pal.goldAlpha);
    sierpinski(W * 0.82, H * 0.25, 280, 4, pal.gold, pal.goldAlpha);
    sierpinski(W * 0.5, H * 0.78, 300, 4, pal.gold, pal.goldAlpha);
    kochSegment(0, H * 0.5, W * 0.35, H * 0.5, 3, pal.purple, pal.purpleAlpha);
    kochSegment(W * 0.65, H * 0.1, W, H * 0.65, 3, pal.purple, pal.purpleAlpha);

    // Ondas (solo si no hay reducción de movimiento)
    if (!reducedMotionQuery.matches) {
      drawWaves(Date.now() / 3000, pal);
    }
  }

  function loop() {
    paint();
    if (!reducedMotionQuery.matches) {
      rafId = requestAnimationFrame(loop);
    }
  }

  function start() {
    if (rafId) {
      cancelAnimationFrame(rafId);
      rafId = null;
    }
    resize();
    loop();
  }

  function handleResize() {
    resize();
    if (reducedMotionQuery.matches) {
      paint(); // Solo pintar una vez si hay reduced motion
    }
  }

  // Iniciar
  resize();
  paint();
  if (!reducedMotionQuery.matches) {
    rafId = requestAnimationFrame(loop);
  }

  // Event listeners
  window.addEventListener('resize', handleResize);
  document.addEventListener('themechange', () => {
    if (reducedMotionQuery.matches) {
      paint(); // Redibujar con nuevo tema
    }
  });
  
  // Respetar prefers-reduced-motion
  reducedMotionQuery.addEventListener('change', () => {
    if (reducedMotionQuery.matches) {
      if (rafId) {
        cancelAnimationFrame(rafId);
        rafId = null;
      }
      paint();
    } else {
      loop();
    }
  });
}

// ---------- TOAST ----------
function showToast(msg, type = 'success') {
  const icons = { success: '✓', error: '✕', info: 'ℹ' };
  const container = document.getElementById('toastContainer') || (() => {
    const d = document.createElement('div');
    d.id = 'toastContainer';
    d.className = 'toast-container';
    d.setAttribute('aria-live', 'polite');
    document.body.appendChild(d);
    return d;
  })();
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.setAttribute('role', 'alert');
  toast.innerHTML = `<span>${icons[type] || '•'}</span><span>${msg}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ---------- CONFIRM DELETE ----------
function confirmAction(msg, formId) {
  if (confirm(msg)) {
    const form = document.getElementById(formId);
    if (form) form.submit();
  }
}

// ---------- FORMAT COP ----------
function fmtCOP(n) {
  return '$' + Math.round(n).toLocaleString('es-CO');
}

// ---------- MOBILE SIDEBAR ----------
function openSidebar() {
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.getElementById('sidebarOverlay');
  const btn = document.getElementById('mobileMenuBtn');
  if (sidebar) sidebar.classList.add('open');
  if (overlay) overlay.style.display = 'block';
  if (btn) btn.setAttribute('aria-expanded', 'true');
}

function closeSidebar() {
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.getElementById('sidebarOverlay');
  const btn = document.getElementById('mobileMenuBtn');
  if (sidebar) sidebar.classList.remove('open');
  if (overlay) overlay.style.display = 'none';
  if (btn) btn.setAttribute('aria-expanded', 'false');
}

function toggleSidebar() {
  const sidebar = document.querySelector('.sidebar');
  if (sidebar && sidebar.classList.contains('open')) {
    closeSidebar();
  } else {
    openSidebar();
  }
}

// ---------- INIT ----------
document.addEventListener('DOMContentLoaded', () => {
  // Inicializar tema
  ThemeManager.init();

  // Auto-dismiss alerts
  document.querySelectorAll('.alert[data-auto-dismiss]').forEach(a => {
    setTimeout(() => {
      a.style.opacity = '0';
      a.style.transform = 'translateY(-10px)';
      setTimeout(() => a.remove(), 300);
    }, 4000);
  });

  // Mobile sidebar
  const mobileMenuBtn = document.getElementById('mobileMenuBtn');
  const overlay = document.getElementById('sidebarOverlay');

  if (mobileMenuBtn) {
    mobileMenuBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleSidebar();
    });
  }
  
  if (overlay) {
    overlay.addEventListener('click', closeSidebar);
  }

  // Cerrar con Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeSidebar();
  });

  // Cerrar sidebar al hacer click en un link (móvil)
  document.querySelectorAll('.nav-item').forEach(link => {
    link.addEventListener('click', () => {
      if (window.innerWidth <= 768) closeSidebar();
    });
  });

  // Cerrar sidebar al redimensionar a desktop
  window.addEventListener('resize', () => {
    if (window.innerWidth > 768) closeSidebar();
  });
});

// Iniciar fractal después de que todo esté cargado
window.addEventListener('load', () => {
  // Pequeño delay para asegurar que el DOM esté listo
  setTimeout(initFractal, 50);
});

// ============================================================
// EXPONER FUNCIONES GLOBALES (para uso en HTML / Jinja)
// ============================================================
window.showToast = showToast;
window.confirmAction = confirmAction;
window.fmtCOP = fmtCOP;
window.toggleSidebar = toggleSidebar;
window.openSidebar = openSidebar;
window.closeSidebar = closeSidebar;
window.ThemeManager = ThemeManager;
