// ============================================================
// DIFERENT 777 — POS JS (con temas y mejoras UX)
// ============================================================
'use strict';

let cart = [];
let allProducts = [];
let currentCat = '';

// ── FORMAT ────────────────────────────────────────────────────────────────
function fmtCOP(n) {
  return '$' + Math.round(n).toLocaleString('es-CO');
}

// ── ESCAPE HTML ──────────────────────────────────────────────────────────
function escHtml(s) {
  return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ── TOAST (usa el mismo del main.js) ─────────────────────────────────────
function showToast(msg, type = 'success') {
  // Si ya existe la función global, usarla
  if (window.showToast) {
    window.showToast(msg, type);
    return;
  }
  // Fallback local
  const icons = { success: '✓', error: '✕', info: 'ℹ' };
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    container.setAttribute('aria-live', 'polite');
    document.body.appendChild(container);
  }
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.setAttribute('role', 'alert');
  t.innerHTML = `<span>${icons[type] || '•'}</span><span>${msg}</span>`;
  container.appendChild(t);
  setTimeout(() => {
    t.style.opacity = '0';
    t.style.transform = 'translateX(20px)';
    setTimeout(() => t.remove(), 300);
  }, 3500);
}

// ── LOAD PRODUCTS ─────────────────────────────────────────────────────────
async function loadProducts(cat) {
  currentCat = cat || '';
  const grid = document.getElementById('posGrid');
  grid.innerHTML = `<div style="color:var(--text-muted);text-align:center;padding:40px;grid-column:1/-1;">
    ⏳ Cargando productos...
  </div>`;
  
  try {
    const url = '/api/productos' + (currentCat ? `?categoria=${encodeURIComponent(currentCat)}` : '');
    const r   = await fetch(url, { credentials: 'same-origin' });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    allProducts = await r.json();
    renderGrid(allProducts);
  } catch (e) {
    console.error('loadProducts:', e);
    showToast('Error cargando productos', 'error');
    grid.innerHTML = `<div style="color:var(--red);text-align:center;padding:40px;grid-column:1/-1;">
      ❌ Error al cargar productos
    </div>`;
  }
}

// ── RENDER PRODUCT GRID ───────────────────────────────────────────────────
function renderGrid(products) {
  const grid = document.getElementById('posGrid');
  if (!products || !products.length) {
    grid.innerHTML = `<div style="color:var(--text-muted);text-align:center;padding:40px;grid-column:1/-1;">
      📦 Sin productos disponibles en esta categoría
    </div>`;
    return;
  }
  
  grid.innerHTML = products.map(p => {
    const inCart = cart.some(c => c.id === p.id);
    const stockCls = p.stock < 5 ? 'badge-low' : 'badge-ok';
    const stockText = p.stock < 5 ? `⚠️ ${p.stock}` : p.stock;
    const isLowStock = p.stock < 5;
    
    return `<div class="pos-product${inCart ? ' in-cart' : ''}${isLowStock ? ' low-stock' : ''}" 
                onclick="addToCart(${p.id})" 
                data-id="${p.id}"
                title="${escHtml(p.nombre)} - Stock: ${p.stock}">
      <div class="pos-product-badge ${stockCls}">${stockText}</div>
      <span class="pos-emoji">${p.emoji || '📦'}</span>
      <div class="pos-name">${escHtml(p.nombre)}</div>
      <div class="pos-talla">${escHtml(p.talla || '')}</div>
      <div class="pos-price">${fmtCOP(p.precio_venta)}</div>
    </div>`;
  }).join('');
}

// ── CATEGORY FILTER ───────────────────────────────────────────────────────
function filterCategory(el, cat) {
  document.querySelectorAll('.filter-chip').forEach(b => b.classList.remove('active'));
  el.classList.add('active');
  loadProducts(cat);
}

// ── SEARCH ────────────────────────────────────────────────────────────────
let searchTimeout = null;

function searchProducts(q) {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    q = q.toLowerCase().trim();
    const filtered = q
      ? allProducts.filter(p => 
          p.nombre.toLowerCase().includes(q) || 
          p.codigo_barras.includes(q) ||
          (p.talla && p.talla.toLowerCase().includes(q))
        )
      : allProducts;
    renderGrid(filtered);
  }, 200);
}

// ── CART OPERATIONS ───────────────────────────────────────────────────────
function addToCart(pid) {
  const p = allProducts.find(x => x.id === pid);
  if (!p) {
    showToast('Producto no encontrado', 'error');
    return;
  }
  
  // Verificar stock
  const existing = cart.find(c => c.id === pid);
  const currentQty = existing ? existing.qty : 0;
  if (currentQty >= p.stock) {
    showToast(`⚠️ Stock insuficiente de "${p.nombre}" (disponible: ${p.stock})`, 'error');
    // Animación de feedback visual
    const gridItem = document.querySelector(`.pos-product[data-id="${pid}"]`);
    if (gridItem) {
      gridItem.style.borderColor = 'var(--red)';
      setTimeout(() => {
        gridItem.style.borderColor = '';
      }, 1000);
    }
    return;
  }
  
  if (existing) {
    existing.qty++;
  } else {
    cart.push({ ...p, qty: 1 });
  }
  
  renderCart();
  renderGrid(allProducts);
  
  // Feedback sutil
  const gridItem = document.querySelector(`.pos-product[data-id="${pid}"]`);
  if (gridItem) {
    gridItem.style.transform = 'scale(0.95)';
    setTimeout(() => {
      gridItem.style.transform = '';
    }, 150);
  }
  
  showToast(`✓ ${p.nombre}`, 'success');
}

function changeQty(pid, delta) {
  const item = cart.find(c => c.id === pid);
  const prod = allProducts.find(x => x.id === pid);
  if (!item) return;
  
  const newQty = item.qty + delta;
  if (newQty < 1) {
    removeFromCart(pid);
    return;
  }
  if (prod && newQty > prod.stock) {
    showToast(`⚠️ Stock máximo: ${prod.stock}`, 'error');
    return;
  }
  
  item.qty = newQty;
  renderCart();
  renderGrid(allProducts);
}

function removeFromCart(pid) {
  const item = cart.find(c => c.id === pid);
  if (item) {
    showToast(`✕ ${item.nombre} eliminado`, 'info');
  }
  cart = cart.filter(c => c.id !== pid);
  renderCart();
  renderGrid(allProducts);
}

function clearCart() {
  if (!cart.length) {
    showToast('Carrito ya está vacío', 'info');
    return;
  }
  if (!confirm('¿Vaciar todo el carrito?')) return;
  cart = [];
  ['clienteNombre','clienteDoc','notas'].forEach(id => { 
    const el = document.getElementById(id); 
    if(el) el.value = ''; 
  });
  const d = document.getElementById('descuento'); 
  if(d) d.value = '0';
  renderCart();
  renderGrid(allProducts);
  showToast('🧹 Carrito vaciado', 'info');
}

// ── RENDER CART ───────────────────────────────────────────────────────────
function renderCart() {
  const count = cart.reduce((a, c) => a + c.qty, 0);
  const countEl = document.getElementById('cartCount');
  if (countEl) countEl.textContent = count + ' items';

  const container = document.getElementById('cartItems');
  if (!cart.length) {
    container.innerHTML = `<div class="cart-empty">
      <div class="cart-empty-icon">🛒</div>
      <div class="cart-empty-text">Carrito vacío</div>
      <div class="cart-empty-sub">Selecciona productos o escanea</div>
    </div>`;
  } else {
    container.innerHTML = cart.map(item => `
      <div class="cart-row" data-id="${item.id}">
        <div class="cart-emoji">${item.emoji || '📦'}</div>
        <div class="cart-info">
          <div class="cart-name">${escHtml(item.nombre)}</div>
          <div class="cart-code">${escHtml(item.codigo_barras)}</div>
        </div>
        <div class="cart-qty-ctrl">
          <button class="qty-btn" onclick="changeQty(${item.id},-1)" aria-label="Disminuir cantidad">−</button>
          <span class="qty-num">${item.qty}</span>
          <button class="qty-btn" onclick="changeQty(${item.id},1)" aria-label="Aumentar cantidad">+</button>
        </div>
        <div class="cart-item-price">${fmtCOP(item.precio_venta * item.qty)}</div>
        <button class="cart-remove" onclick="removeFromCart(${item.id})" aria-label="Eliminar producto">✕</button>
      </div>`).join('');
  }
  updateTotals();
}

function updateTotals() {
  const sub  = cart.reduce((a, c) => a + c.precio_venta * c.qty, 0);
  const desc = Math.max(0, Math.min(100, parseFloat(document.getElementById('descuento').value) || 0));
  const dm   = sub * desc / 100;
  const tot  = sub - dm;
  
  const subEl = document.getElementById('subtotal');
  const descEl = document.getElementById('descMonto');
  const totalEl = document.getElementById('totalDisplay');
  const countEl = document.getElementById('cartCount');
  
  if (subEl) subEl.textContent = fmtCOP(sub);
  if (descEl) descEl.textContent = dm > 0 ? '-' + fmtCOP(dm) : fmtCOP(0);
  if (totalEl) totalEl.textContent = fmtCOP(tot);
  if (countEl) countEl.textContent = cart.reduce((a, c) => a + c.qty, 0) + ' items';
}

// ── SCANNER ───────────────────────────────────────────────────────────────
async function scanBarcode() {
  const input = document.getElementById('scanInput');
  const code  = (input.value || '').trim();
  if (!code) {
    showToast('Escanea o escribe un código de barras', 'info');
    input.focus();
    return;
  }
  
  try {
    const r    = await fetch(`/api/buscar-producto?codigo=${encodeURIComponent(code)}`, { credentials: 'same-origin' });
    const data = await r.json();
    if (data.found) {
      // Si el producto no está en allProducts, añadirlo
      if (!allProducts.find(p => p.id === data.producto.id)) {
        allProducts.push(data.producto);
      }
      addToCart(data.producto.id);
      input.value = '';
      input.focus();
    } else {
      showToast(data.error || 'Código no encontrado: ' + code, 'error');
      input.select();
    }
  } catch (e) {
    console.error('scanBarcode:', e);
    showToast('Error de conexión al escanear', 'error');
  }
}

// ── PROCESAR VENTA ────────────────────────────────────────────────────────
async function procesarVenta() {
  if (!cart.length) {
    showToast('⚠️ El carrito está vacío', 'error');
    return;
  }

  // Validar stock antes de procesar
  for (const item of cart) {
    const prod = allProducts.find(p => p.id === item.id);
    if (prod && item.qty > prod.stock) {
      showToast(`⚠️ Stock insuficiente: "${prod.nombre}" (${prod.stock} disponibles)`, 'error');
      return;
    }
  }

  const desc_pct = parseFloat(document.getElementById('descuento').value) || 0;
  const sedeEl   = document.getElementById('sedeId');
  const metodoPago = document.getElementById('metodoPago');
  
  const payload  = {
    items: cart.map(c => ({ 
      producto_id: c.id, 
      nombre: c.nombre, 
      cantidad: c.qty, 
      precio_unitario: c.precio_venta 
    })),
    cliente_nombre: (document.getElementById('clienteNombre').value || '').trim(),
    cliente_doc:    (document.getElementById('clienteDoc').value || '').trim(),
    metodo_pago:    metodoPago ? metodoPago.value : 'efectivo',
    descuento_pct:  desc_pct,
    notas:          (document.getElementById('notas').value || '').trim(),
    sede_id:        sedeEl ? parseInt(sedeEl.value) : 1
  };

  const btn = document.getElementById('btnProcesar');
  const originalText = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '⏳ Procesando...';

  try {
    const r    = await fetch('/ventas/procesar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify(payload)
    });
    const data = await r.json();

    if (data.ok) {
      showToast(`✅ ${data.numero_factura} — ${fmtCOP(data.total)}`, 'success');
      
      // Abrir factura en nueva ventana/pestaña
      if (data.venta_id) {
        window.open(`/ventas/${data.venta_id}/factura`, '_blank', 'width=460,height=720,scrollbars=yes');
      }
      
      clearCartSilent();
      loadProducts(currentCat);
    } else {
      showToast(data.error || 'Error procesando la venta', 'error');
      btn.disabled = false;
      btn.innerHTML = originalText;
    }
  } catch (e) {
    console.error('procesarVenta:', e);
    showToast('Error de conexión — verifica internet', 'error');
    btn.disabled = false;
    btn.innerHTML = originalText;
  }
}

function clearCartSilent() {
  cart = [];
  ['clienteNombre','clienteDoc','notas'].forEach(id => { 
    const el = document.getElementById(id); 
    if(el) el.value = ''; 
  });
  const d = document.getElementById('descuento'); 
  if(d) d.value = '0';
  renderCart();
}

// ── KEYBOARD SHORTCUTS ──────────────────────────────────────────────────
document.addEventListener('keydown', (e) => {
  // F1: focus en búsqueda
  if (e.key === 'F1') {
    e.preventDefault();
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
      searchInput.focus();
      searchInput.select();
    }
  }
  
  // F2: focus en scan
  if (e.key === 'F2') {
    e.preventDefault();
    const scanInput = document.getElementById('scanInput');
    if (scanInput) {
      scanInput.focus();
      scanInput.select();
    }
  }
  
  // Ctrl+Enter: procesar venta
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    e.preventDefault();
    procesarVenta();
  }
  
  // Escape: limpiar búsqueda o cerrar
  if (e.key === 'Escape') {
    const searchInput = document.getElementById('searchInput');
    const scanInput = document.getElementById('scanInput');
    if (document.activeElement === searchInput || document.activeElement === scanInput) {
      document.activeElement.blur();
    }
  }
});

// ── INIT ──────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadProducts();
  
  // Event listeners
  const descInput = document.getElementById('descuento');
  if (descInput) descInput.addEventListener('input', updateTotals);
  
  // Auto-focus en scan input al cargar
  const scanInput = document.getElementById('scanInput');
  if (scanInput) setTimeout(() => scanInput.focus(), 500);
  
  // Click en botón de limpiar
  const clearBtn = document.querySelector('.cart-clear-btn');
  if (clearBtn) clearBtn.addEventListener('click', clearCart);
  
  // Enter en scan input
  if (scanInput) {
    scanInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        scanBarcode();
      }
    });
  }
});

// ── EXPONER FUNCIONES GLOBALES ──────────────────────────────────────────
window.loadProducts = loadProducts;
window.renderGrid = renderGrid;
window.filterCategory = filterCategory;
window.searchProducts = searchProducts;
window.addToCart = addToCart;
window.changeQty = changeQty;
window.removeFromCart = removeFromCart;
window.clearCart = clearCart;
window.scanBarcode = scanBarcode;
window.procesarVenta = procesarVenta;
window.fmtCOP = fmtCOP;
window.showToast = showToast;
