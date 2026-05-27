// ============================================================
// DIFERENT 777 — POS JS  (production ready)
// ============================================================
'use strict';

let cart = [];
let allProducts = [];
let currentCat = '';

// ── FORMAT ────────────────────────────────────────────────────────────────
function fmtCOP(n) {
  return '$' + Math.round(n).toLocaleString('es-CO');
}

// ── LOAD PRODUCTS ─────────────────────────────────────────────────────────
async function loadProducts(cat) {
  currentCat = cat || '';
  try {
    const url = '/api/productos' + (currentCat ? `?categoria=${encodeURIComponent(currentCat)}` : '');
    const r   = await fetch(url, { credentials: 'same-origin' });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    allProducts = await r.json();
    renderGrid(allProducts);
  } catch (e) {
    console.error('loadProducts:', e);
    showToast('Error cargando productos', 'error');
  }
}

// ── RENDER PRODUCT GRID ───────────────────────────────────────────────────
function renderGrid(products) {
  const grid = document.getElementById('posGrid');
  if (!products || !products.length) {
    grid.innerHTML = `<div style="color:var(--muted);text-align:center;padding:40px;grid-column:1/-1;">
      Sin productos disponibles en esta categoría
    </div>`;
    return;
  }
  grid.innerHTML = products.map(p => {
    const inCart = cart.some(c => c.id === p.id);
    const stockCls = p.stock < 5 ? 'badge-low' : 'badge-ok';
    return `<div class="pos-product${inCart ? ' in-cart' : ''}" onclick="addToCart(${p.id})" data-id="${p.id}">
      <div class="pos-product-badge ${stockCls}">${p.stock}</div>
      <span class="pos-emoji">${p.emoji}</span>
      <div class="pos-name">${escHtml(p.nombre)}</div>
      <div class="pos-talla">${escHtml(p.talla)}</div>
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
function searchProducts(q) {
  q = q.toLowerCase().trim();
  const filtered = q
    ? allProducts.filter(p => p.nombre.toLowerCase().includes(q) || p.codigo_barras.includes(q))
    : allProducts;
  renderGrid(filtered);
}

// ── CART OPERATIONS ───────────────────────────────────────────────────────
function addToCart(pid) {
  const p = allProducts.find(x => x.id === pid);
  if (!p) return;
  const existing = cart.find(c => c.id === pid);
  if (existing) {
    if (existing.qty >= p.stock) { showToast('⚠️ Sin más stock disponible', 'error'); return; }
    existing.qty++;
  } else {
    cart.push({ ...p, qty: 1 });
  }
  renderCart();
  renderGrid(allProducts);
  showToast(`✓ ${p.nombre}`, 'success');
}

function changeQty(pid, delta) {
  const item = cart.find(c => c.id === pid);
  const prod = allProducts.find(x => x.id === pid);
  if (!item) return;
  item.qty = Math.max(1, Math.min(item.qty + delta, prod ? prod.stock : 999));
  renderCart();
}

function removeFromCart(pid) {
  cart = cart.filter(c => c.id !== pid);
  renderCart();
  renderGrid(currentCat ? allProducts.filter(p => p.categoria === currentCat) : allProducts);
}

function clearCart() {
  cart = [];
  ['clienteNombre','clienteDoc','notas'].forEach(id => { const el = document.getElementById(id); if(el) el.value=''; });
  const d = document.getElementById('descuento'); if(d) d.value='0';
  renderCart();
  renderGrid(allProducts);
}

// ── RENDER CART ───────────────────────────────────────────────────────────
function renderCart() {
  const count = cart.reduce((a, c) => a + c.qty, 0);
  document.getElementById('cartCount').textContent = count + ' items';

  const container = document.getElementById('cartItems');
  if (!cart.length) {
    container.innerHTML = `<div style="text-align:center;padding:28px 16px;color:var(--muted);font-size:13px;">
      Selecciona productos o escanea un código de barras
    </div>`;
  } else {
    container.innerHTML = cart.map(item => `
      <div class="cart-row">
        <div class="cart-emoji">${item.emoji}</div>
        <div class="cart-info">
          <div class="cart-name">${escHtml(item.nombre)}</div>
          <div class="cart-code">${escHtml(item.codigo_barras)}</div>
        </div>
        <div class="cart-qty-ctrl">
          <button class="qty-btn" onclick="changeQty(${item.id},-1)">−</button>
          <span class="qty-num">${item.qty}</span>
          <button class="qty-btn" onclick="changeQty(${item.id},1)">+</button>
        </div>
        <div class="cart-item-price">${fmtCOP(item.precio_venta * item.qty)}</div>
        <button class="cart-remove" onclick="removeFromCart(${item.id})">✕</button>
      </div>`).join('');
  }
  updateTotals();
}

function updateTotals() {
  const sub  = cart.reduce((a, c) => a + c.precio_venta * c.qty, 0);
  const desc = Math.max(0, Math.min(100, parseFloat(document.getElementById('descuento').value) || 0));
  const dm   = sub * desc / 100;
  const tot  = sub - dm;
  document.getElementById('subtotal').textContent    = fmtCOP(sub);
  document.getElementById('descMonto').textContent   = '-' + fmtCOP(dm);
  document.getElementById('totalDisplay').textContent = fmtCOP(tot);
}

// ── SCANNER ───────────────────────────────────────────────────────────────
async function scanBarcode() {
  const input = document.getElementById('scanInput');
  const code  = (input.value || '').trim();
  if (!code) return;
  try {
    const r    = await fetch(`/api/buscar-producto?codigo=${encodeURIComponent(code)}`, { credentials: 'same-origin' });
    const data = await r.json();
    if (data.found) {
      if (!allProducts.find(p => p.id === data.producto.id)) allProducts.push(data.producto);
      addToCart(data.producto.id);
      input.value = '';
    } else {
      showToast(data.error || 'Código no encontrado: ' + code, 'error');
    }
  } catch (e) { showToast('Error de conexión', 'error'); }
}

// ── PROCESAR VENTA ────────────────────────────────────────────────────────
async function procesarVenta() {
  if (!cart.length) { showToast('El carrito está vacío', 'error'); return; }

  const desc_pct = parseFloat(document.getElementById('descuento').value) || 0;
  const sedeEl   = document.getElementById('sedeId');
  const payload  = {
    items: cart.map(c => ({ producto_id: c.id, nombre: c.nombre, cantidad: c.qty, precio_unitario: c.precio_venta })),
    cliente_nombre: (document.getElementById('clienteNombre').value || '').trim(),
    cliente_doc:    (document.getElementById('clienteDoc').value || '').trim(),
    metodo_pago:    document.getElementById('metodoPago').value,
    descuento_pct:  desc_pct,
    notas:          (document.getElementById('notas').value || '').trim(),
    sede_id:        sedeEl ? parseInt(sedeEl.value) : 1
  };

  const btn = document.getElementById('btnProcesar');
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
      // Open receipt in new tab/window
      window.open(`/ventas/${data.venta_id}/factura`, '_blank', 'width=460,height=720,scrollbars=yes');
      clearCart();
      loadProducts(currentCat);
    } else {
      showToast(data.error || 'Error procesando la venta', 'error');
    }
  } catch (e) {
    showToast('Error de conexión — verifica internet', 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '✓ PROCESAR VENTA';
  }
}

// ── UTILS ─────────────────────────────────────────────────────────────────
function escHtml(s) {
  return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function showToast(msg, type = 'success') {
  const icons = { success: '✓', error: '✕', info: 'ℹ' };
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<span>${icons[type] || '•'}</span><span>${msg}</span>`;
  container.appendChild(t);
  setTimeout(() => t.remove(), 3500);
}

// ── INIT ──────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadProducts();
  document.getElementById('descuento').addEventListener('input', updateTotals);

  // Global keyboard: typing goes to scan input
  document.addEventListener('keydown', e => {
    const scanInput = document.getElementById('scanInput');
    const tag = document.activeElement.tagName;
    if (tag !== 'INPUT' && tag !== 'TEXTAREA' && tag !== 'SELECT'
        && e.key.length === 1 && !e.ctrlKey && !e.altKey && !e.metaKey) {
      scanInput.focus();
    }
    if (e.key === 'Enter' && document.activeElement === scanInput) {
      e.preventDefault();
      scanBarcode();
    }
  });
});
