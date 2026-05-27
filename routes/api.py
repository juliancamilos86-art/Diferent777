from flask import Blueprint, jsonify, request
from flask_login import login_required
from models import db, Producto, Venta, Categoria
from datetime import datetime, timedelta
from sqlalchemy import func

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/productos')
@login_required
def get_productos():
    cat_name = request.args.get('categoria', '').strip()
    query = Producto.query.filter_by(activo=True)
    if cat_name:
        cat = Categoria.query.filter_by(nombre=cat_name).first()
        if cat:
            query = query.filter_by(categoria_id=cat.id)
    productos = query.filter(Producto.stock > 0).order_by(Producto.nombre).all()
    return jsonify([{
        'id': p.id, 'nombre': p.nombre, 'codigo_barras': p.codigo_barras,
        'precio_venta': p.precio_venta, 'stock': p.stock, 'talla': p.talla or '',
        'emoji': p.categoria.emoji if p.categoria else '📦',
        'categoria': p.categoria.nombre if p.categoria else ''
    } for p in productos])

@api_bp.route('/stats')
@login_required
def stats():
    today = datetime.utcnow().date()
    total_hoy = float(db.session.query(func.sum(Venta.total)).filter(
        func.date(Venta.fecha)==today, Venta.estado=='completada').scalar() or 0)
    count_hoy = Venta.query.filter(
        func.date(Venta.fecha)==today, Venta.estado=='completada').count()
    stock_bajo = Producto.query.filter(
        Producto.activo==True, Producto.stock<=Producto.stock_minimo).count()
    return jsonify({'total_hoy': total_hoy, 'count_hoy': count_hoy, 'stock_bajo': stock_bajo})
