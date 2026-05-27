from flask import Blueprint, render_template
from flask_login import login_required
from models import db, Producto, Venta, ItemVenta
from datetime import datetime, timedelta
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    today = datetime.utcnow().date()
    week_ago = datetime.utcnow() - timedelta(days=7)
    month_ago = datetime.utcnow() - timedelta(days=30)

    def sales_sum(since=None, date_only=None):
        q = db.session.query(func.sum(Venta.total)).filter(Venta.estado == 'completada')
        if date_only:
            q = q.filter(func.date(Venta.fecha) == date_only)
        elif since:
            q = q.filter(Venta.fecha >= since)
        return float(q.scalar() or 0)

    def sales_count(since=None, date_only=None):
        q = Venta.query.filter_by(estado='completada')
        if date_only:
            q = q.filter(func.date(Venta.fecha) == date_only)
        elif since:
            q = q.filter(Venta.fecha >= since)
        return q.count()

    total_hoy    = sales_sum(date_only=today)
    count_hoy    = sales_count(date_only=today)
    total_semana = sales_sum(since=week_ago)
    total_mes    = sales_sum(since=month_ago)

    total_productos = Producto.query.filter_by(activo=True).count()
    stock_bajo = Producto.query.filter(Producto.activo==True, Producto.stock<=Producto.stock_minimo, Producto.stock>0).count()
    sin_stock  = Producto.query.filter_by(activo=True, stock=0).count()

    ventas_recientes = Venta.query.filter_by(estado='completada').order_by(Venta.fecha.desc()).limit(8).all()

    # Last 7 days chart
    dias_esp = ['Lun','Mar','Mié','Jue','Vie','Sáb','Dom']
    chart_labels, chart_values = [], []
    for i in range(6, -1, -1):
        d = (datetime.utcnow() - timedelta(days=i)).date()
        label = 'Hoy' if i == 0 else dias_esp[d.weekday()]
        val = float(db.session.query(func.sum(Venta.total)).filter(
            func.date(Venta.fecha)==d, Venta.estado=='completada').scalar() or 0)
        chart_labels.append(label)
        chart_values.append(val)

    # Top products this week
    top_items = db.session.query(
        ItemVenta.nombre_producto,
        func.sum(ItemVenta.cantidad).label('qty'),
        func.sum(ItemVenta.subtotal).label('monto')
    ).join(Venta).filter(
        Venta.estado=='completada', Venta.fecha>=week_ago
    ).group_by(ItemVenta.nombre_producto).order_by(func.sum(ItemVenta.cantidad).desc()).limit(5).all()

    return render_template('dashboard.html',
        total_hoy=total_hoy, count_hoy=count_hoy,
        total_semana=total_semana, total_mes=total_mes,
        total_productos=total_productos, stock_bajo=stock_bajo, sin_stock=sin_stock,
        ventas_recientes=ventas_recientes,
        chart_labels=chart_labels, chart_values=chart_values,
        top_items=top_items)
