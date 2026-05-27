from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from models import db, Producto, Categoria, Sede, Responsable
from datetime import datetime
import random

productos_bp = Blueprint('productos', __name__)

@productos_bp.route('/inventario')
@login_required
def inventario():
    q       = request.args.get('q', '')
    cat_id  = request.args.get('categoria', '')
    sede_id = request.args.get('sede', '')
    estado  = request.args.get('estado', '')

    query = Producto.query.filter_by(activo=True)
    if q:
        query = query.filter(db.or_(Producto.nombre.ilike(f'%{q}%'), Producto.codigo_barras.ilike(f'%{q}%')))
    if cat_id:
        query = query.filter_by(categoria_id=int(cat_id))
    if sede_id:
        query = query.filter_by(sede_id=int(sede_id))
    if estado == 'sin_stock':
        query = query.filter(Producto.stock == 0)
    elif estado == 'stock_bajo':
        query = query.filter(Producto.stock > 0, Producto.stock <= Producto.stock_minimo)
    elif estado == 'ok':
        query = query.filter(Producto.stock > Producto.stock_minimo)

    productos  = query.order_by(Producto.nombre).all()
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    sedes      = Sede.query.filter_by(activa=True).all()

    return render_template('inventario.html',
        productos=productos, categorias=categorias, sedes=sedes, q=q,
        total=len(productos),
        en_stock=sum(1 for p in productos if p.stock > p.stock_minimo),
        bajo=sum(1 for p in productos if 0 < p.stock <= p.stock_minimo),
        sin=sum(1 for p in productos if p.stock == 0))

@productos_bp.route('/producto/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_producto():
    cats   = Categoria.query.order_by(Categoria.nombre).all()
    sedes  = Sede.query.filter_by(activa=True).all()
    resps  = Responsable.query.filter_by(activo=True).all()

    if request.method == 'POST':
        codigo = request.form.get('codigo_barras', '').strip()
        if not codigo:
            flash('El código de barras es obligatorio', 'error')
            return render_template('producto_form.html', categorias=cats, sedes=sedes, responsables=resps, producto=None)
        if Producto.query.filter_by(codigo_barras=codigo).first():
            flash('Ese código de barras ya existe en el sistema', 'error')
            return render_template('producto_form.html', categorias=cats, sedes=sedes, responsables=resps, producto=None)

        p = Producto(
            nombre=request.form.get('nombre', '').strip(),
            codigo_barras=codigo,
            descripcion=request.form.get('descripcion', '').strip(),
            talla=request.form.get('talla', '').strip(),
            color=request.form.get('color', '').strip(),
            costo=float(request.form.get('costo', 0) or 0),
            precio_venta=float(request.form.get('precio_venta', 0) or 0),
            stock=int(request.form.get('stock', 0) or 0),
            stock_minimo=int(request.form.get('stock_minimo', 5) or 5),
            categoria_id=int(request.form['categoria_id']) if request.form.get('categoria_id') else None,
            sede_id=int(request.form['sede_id']) if request.form.get('sede_id') else None,
            responsable_id=int(request.form['responsable_id']) if request.form.get('responsable_id') else None,
            activo=True, fecha_ingreso=datetime.utcnow()
        )
        db.session.add(p)
        db.session.commit()
        flash(f'✅ Activo "{p.nombre}" registrado exitosamente', 'success')
        return redirect(url_for('productos.inventario'))

    return render_template('producto_form.html', categorias=cats, sedes=sedes, responsables=resps, producto=None)

@productos_bp.route('/producto/<int:pid>/editar', methods=['GET', 'POST'])
@login_required
def editar_producto(pid):
    p     = Producto.query.get_or_404(pid)
    cats  = Categoria.query.order_by(Categoria.nombre).all()
    sedes = Sede.query.filter_by(activa=True).all()
    resps = Responsable.query.filter_by(activo=True).all()

    if request.method == 'POST':
        p.nombre        = request.form.get('nombre', '').strip()
        p.descripcion   = request.form.get('descripcion', '').strip()
        p.talla         = request.form.get('talla', '').strip()
        p.color         = request.form.get('color', '').strip()
        p.costo         = float(request.form.get('costo', 0) or 0)
        p.precio_venta  = float(request.form.get('precio_venta', 0) or 0)
        p.stock         = int(request.form.get('stock', 0) or 0)
        p.stock_minimo  = int(request.form.get('stock_minimo', 5) or 5)
        p.categoria_id  = int(request.form['categoria_id']) if request.form.get('categoria_id') else None
        p.sede_id       = int(request.form['sede_id']) if request.form.get('sede_id') else None
        p.responsable_id= int(request.form['responsable_id']) if request.form.get('responsable_id') else None
        db.session.commit()
        flash(f'✅ Producto "{p.nombre}" actualizado', 'success')
        return redirect(url_for('productos.inventario'))

    return render_template('producto_form.html', producto=p, categorias=cats, sedes=sedes, responsables=resps)

@productos_bp.route('/producto/<int:pid>/eliminar', methods=['POST'])
@login_required
def eliminar_producto(pid):
    p = Producto.query.get_or_404(pid)
    p.activo = False
    db.session.commit()
    flash(f'Producto "{p.nombre}" eliminado del inventario', 'success')
    return redirect(url_for('productos.inventario'))

@productos_bp.route('/api/generar-codigo')
@login_required
def generar_codigo():
    for _ in range(20):
        c = '750' + str(random.randint(1000000000, 9999999999))
        if not Producto.query.filter_by(codigo_barras=c).first():
            return jsonify({'codigo': c})
    return jsonify({'codigo': str(random.randint(10**12, 10**13 - 1))})
