from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import db, Usuario

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = Usuario.query.filter_by(email=email, activo=True).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            nxt = request.args.get('next')
            return redirect(nxt if nxt and nxt.startswith('/') else url_for('dashboard.index'))
        flash('Correo o contraseña incorrectos', 'error')
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/cambiar-password', methods=['POST'])
@login_required
def cambiar_password():
    actual = request.form.get('actual', '')
    nueva = request.form.get('nueva', '')
    if not check_password_hash(current_user.password_hash, actual):
        flash('Contraseña actual incorrecta', 'error')
    elif len(nueva) < 6:
        flash('La nueva contraseña debe tener mínimo 6 caracteres', 'error')
    else:
        current_user.password_hash = generate_password_hash(nueva)
        db.session.commit()
        flash('Contraseña actualizada exitosamente', 'success')
    return redirect(url_for('admin.panel'))
