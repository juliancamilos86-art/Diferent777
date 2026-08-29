from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required
from models import db, Producto, Categoria, Sede, Responsable
from datetime import datetime
import random
from utils.etiquetas import generar_pdf_etiquetas

productos_bp = Blueprint('productos', __name__)

# ============================================================
# 🔥 FUNCIÓN AUXILIAR PARA EVITAR ERRORES DE CONVERSIÓN (INT vs STR)
# ============================================================
def _parse_id(val):
    """Convierte un valor a ID numérico. Si es texto (ej. 'ropa'), busca el ID en la BD."""
    if not val or val == 'None' or val == '':
        return None
    # Si ya es un número, lo convierte directo
    if str(val).isdigit():
        return int(val)
    # Si es texto, busca la categoría, sede o responsable por nombre
    cat = Categoria.query.filter_by(nombre=val).first()
    if cat:
        return cat.id
    sede = Sede.query.filter_by(nombre=val).first()
    if sede:
        return sede.id
    resp = Responsable.query.filter_by(nombre=val).first()
    if resp:
        return resp.id
    return None

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

        # 🔥 Usamos la función auxiliar para no romper nunca
        categoria_val = request.form.get('categoria_id')
        sede_val = request.form.get('sede_id')
        responsable_val = request.form.get('responsable_id')

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
            categoria_id=_parse_id(categoria_val),
            sede_id=_parse_id(sede_val),
            responsable_id=_parse_id(responsable_val),
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
        
        # 🔥 Usamos la función auxiliar para no romper nunca
        categoria_val = request.form.get('categoria_id')
        sede_val = request.form.get('sede_id')
        responsable_val = request.form.get('responsable_id')

        p.categoria_id  = _parse_id(categoria_val)
        p.sede_id       = _parse_id(sede_val)
        p.responsable_id= _parse_id(responsable_val)
        
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

# =====================================================================
# 👇 NUEVA RUTA PARA IMPRIMIR ETIQUETAS EN LOTE (SIN DESPERDICIAR ROLLO)
# =====================================================================
@productos_bp.route('/imprimir/etiquetas', methods=['POST'])
@login_required
def imprimir_etiquetas_lote():
    # 1. Recibir los IDs de los productos seleccionados en el HTML
    ids_productos = request.form.getlist('productos_seleccionados')
    
    if not ids_productos:
        flash('No seleccionaste ningún producto para imprimir.', 'warning')
        return redirect(url_for('productos.inventario'))
    
    # 2. Convertir a enteros y consultar a la base de datos
    try:
        ids_int = [int(i) for i in ids_productos]
    except ValueError:
        flash('Selección inválida.', 'danger')
        return redirect(url_for('productos.inventario'))

    productos = Producto.query.filter(Producto.id.in_(ids_int)).all()
    
    if not productos:
        flash('No se encontraron los productos seleccionados.', 'danger')
        return redirect(url_for('productos.inventario'))

    # 3. Generar el PDF en memoria
    pdf_buffer = generar_pdf_etiquetas(productos)
    
    # 4. Enviar el PDF al navegador para abrir el visor e imprimir
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=False,  # False abre el visor de PDF en el navegador
        download_name='etiquetas_productos.pdf'
    )
