from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from models import db, Usuario, Sede, Categoria, Responsable, Configuracion, Producto
from werkzeug.security import generate_password_hash

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def deco(*a, **kw):
        if not current_user.is_authenticated or current_user.rol != 'admin':
            flash('Se requieren permisos de administrador', 'error')
            return redirect(url_for('dashboard.index'))
        return f(*a, **kw)
    return deco

@admin_bp.route('/admin')
@login_required
@admin_required
def panel():
    usuarios     = Usuario.query.order_by(Usuario.nombre).all()
    sedes        = Sede.query.order_by(Sede.nombre).all()
    categorias   = Categoria.query.order_by(Categoria.nombre).all()
    responsables = Responsable.query.order_by(Responsable.nombre).all()
    productos    = Producto.query.filter_by(activo=True).all()
    config = {k: Configuracion.get(f'tienda_{k}', d) for k, d in [
        ('nombre','DIFERENT 777'),('nit',''),('direccion',''),
        ('telefono',''),('email',''),('web','')]}
    return render_template('admin.html', usuarios=usuarios, sedes=sedes,
        categorias=categorias, responsables=responsables, config=config, productos=productos)

@admin_bp.route('/admin/config', methods=['POST'])
@login_required
@admin_required
def guardar_config():
    for campo in ['nombre','nit','direccion','telefono','email','web']:
        Configuracion.set(f'tienda_{campo}', request.form.get(campo, '').strip())
    flash('✅ Configuración guardada', 'success')
    return redirect(url_for('admin.panel'))

@admin_bp.route('/admin/sede/nueva', methods=['POST'])
@login_required
@admin_required
def nueva_sede():
    n = request.form.get('nombre', '').strip()
    if n and not Sede.query.filter_by(nombre=n).first():
        db.session.add(Sede(nombre=n, activa=True))
        db.session.commit()
        flash(f'Sede "{n}" creada', 'success')
    return redirect(url_for('admin.panel'))

@admin_bp.route('/admin/sede/<int:sid>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_sede(sid):
    s = Sede.query.get_or_404(sid)
    s.activa = not s.activa
    db.session.commit()
    return redirect(url_for('admin.panel'))

@admin_bp.route('/admin/responsable/nuevo', methods=['POST'])
@login_required
@admin_required
def nuevo_responsable():
    n = request.form.get('nombre', '').strip()
    if n and not Responsable.query.filter_by(nombre=n).first():
        db.session.add(Responsable(nombre=n, activo=True))
        db.session.commit()
        flash(f'Responsable "{n}" agregado', 'success')
    return redirect(url_for('admin.panel'))

@admin_bp.route('/admin/usuario/nuevo', methods=['POST'])
@login_required
@admin_required
def nuevo_usuario():
    nombre   = request.form.get('nombre', '').strip()
    email    = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    rol      = request.form.get('rol', 'vendedor')
    if not all([nombre, email, password]):
        flash('Todos los campos son obligatorios', 'error')
        return redirect(url_for('admin.panel'))
    if len(password) < 6:
        flash('La contraseña debe tener mínimo 6 caracteres', 'error')
        return redirect(url_for('admin.panel'))
    if Usuario.query.filter_by(email=email).first():
        flash('El email ya está registrado', 'error')
        return redirect(url_for('admin.panel'))
    db.session.add(Usuario(nombre=nombre, email=email,
        password_hash=generate_password_hash(password), rol=rol, activo=True))
    db.session.commit()
    flash(f'✅ Usuario "{nombre}" creado', 'success')
    return redirect(url_for('admin.panel'))

@admin_bp.route('/admin/usuario/<int:uid>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_usuario(uid):
    u = Usuario.query.get_or_404(uid)
    if u.id != current_user.id:
        u.activo = not u.activo
        db.session.commit()
    return redirect(url_for('admin.panel'))
