from flask import Blueprint, render_template, request
from flask_login import login_required
from models import db, Venta, ItemVenta, Producto, Sede
from datetime import datetime, timedelta
from sqlalchemy import func

reportes_bp = Blueprint('reportes', __name__)

def _period_dates(periodo, meses=1):
    now = datetime.utcnow()
    periods = {
        'hoy': now.replace(hour=0, minute=0, second=0, microsecond=0),
        'semana': now - timedelta(days=7),
        'mes': now - timedelta(days=30),
        'trimestre': now - timedelta(days=90),
        'anual': now - timedelta(days=365),
        'custom': now - timedelta(days=30 * max(1, int(meses))),
    }
    return periods.get(periodo, periods['mes']), now

@reportes_bp.route('/reportes')
@login_required
def reportes():
    periodo  = request.args.get('periodo', 'mes')
    meses    = request.args.get('meses', '1')
    desde_str = request.args.get('desde', '')
    hasta_str = request.args.get('hasta', '')

    if desde_str and hasta_str:
        fecha_desde = datetime.strptime(desde_str, '%Y-%m-%d')
        fecha_hasta = datetime.strptime(hasta_str, '%Y-%m-%d') + timedelta(days=1)
    else:
        fecha_desde, fecha_hasta = _period_dates(periodo, meses)

    ventas = Venta.query.filter(
        Venta.fecha >= fecha_desde, Venta.fecha < fecha_hasta,
        Venta.estado == 'completada'
    ).all()

    total      = sum(v.total for v in ventas)
    total_costo = sum(iv.cantidad * (iv.producto.costo if iv.producto else 0)
                      for v in ventas for iv in v.items)
    ganancia   = total - total_costo
    margen     = (ganancia / total * 100) if total > 0 else 0
    ticket_avg = total / max(1, len(ventas))

    metodos = {}
    cats    = {}
    prod_v  = {}
    dias    = {}

    delta = min((fecha_hasta - fecha_desde).days, 90)
    for i in range(delta):
        d = (fecha_desde + timedelta(days=i)).strftime('%Y-%m-%d')
        dias[d] = 0

    for v in ventas:
        metodos[v.metodo_pago] = metodos.get(v.metodo_pago, 0) + v.total
        d = v.fecha.strftime('%Y-%m-%d')
        if d in dias:
            dias[d] += v.total
        for iv in v.items:
            cat = iv.producto.categoria.nombre if iv.producto and iv.producto.categoria else 'Sin categoría'
            cats[cat] = cats.get(cat, 0) + iv.subtotal
            k = iv.nombre_producto
            if k not in prod_v:
                prod_v[k] = {'qty': 0, 'total': 0, 'emoji': iv.producto.categoria.emoji if iv.producto and iv.producto.categoria else '📦'}
            prod_v[k]['qty']   += iv.cantidad
            prod_v[k]['total'] += iv.subtotal

    top_productos = sorted(prod_v.items(), key=lambda x: x[1]['total'], reverse=True)[:10]

    # Ventas por sede
    sedes_v = {}
    for v in ventas:
        s = v.sede.nombre if v.sede else 'Sin sede'
        sedes_v[s] = sedes_v.get(s, 0) + v.total

    return render_template('reportes.html',
        total=total, ganancia=ganancia, margen=margen,
        count=len(ventas), ticket_avg=ticket_avg,
        metodos=metodos, categorias_venta=cats,
        top_productos=top_productos,
        dias_labels=list(dias.keys()), dias_values=list(dias.values()),
        sedes_venta=sedes_v,
        periodo=periodo, meses=meses,
        fecha_desde=desde_str, fecha_hasta=hasta_str)

@reportes_bp.route('/activos')
@login_required
def activos():
    productos = Producto.query.filter_by(activo=True).order_by(Producto.nombre).all()
    valor_costo = sum(p.costo * p.stock for p in productos)
    valor_venta = sum(p.precio_venta * p.stock for p in productos)

    sedes_r = {}
    resp_r  = {}
    for p in productos:
        s = p.sede.nombre if p.sede else 'Sin sede'
        r = p.responsable.nombre if p.responsable else 'Sin asignar'
        sedes_r.setdefault(s, {'count': 0, 'stock': 0, 'valor': 0})
        sedes_r[s]['count'] += 1
        sedes_r[s]['stock'] += p.stock
        sedes_r[s]['valor'] += p.precio_venta * p.stock
        resp_r.setdefault(r, {'count': 0})
        resp_r[r]['count'] += 1

    return render_template('activos.html',
        productos=productos, valor_costo=valor_costo, valor_venta=valor_venta,
        sedes_resumen=sedes_r, resp_resumen=resp_r)
