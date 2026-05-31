from flask import Flask
from flask_login import LoginManager
from models import db
from datetime import datetime
import os
import secrets

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)

    # ── Configuración de Seguridad desde Environment ──────────────────────────────
    # Obtener SECRET_KEY desde variable de entorno o generar una segura
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        # En producción, Render debe tener esta variable
        if os.environ.get('RENDER'):
            raise ValueError("SECRET_KEY no configurada en Render. Configúrala en Environment Variables.")
        # Solo para desarrollo local
        secret_key = 'dev-secret-key-diferent777-2025'
    
    app.config['SECRET_KEY'] = secret_key
    
    # ── Configuración de Base de Datos ──────────────────────────────────────────
    db_url = os.environ.get('DATABASE_URL', '')
    
    # Si no hay URL de base de datos, usar SQLite para pruebas
    if not db_url:
        # Para pruebas locales o cuando no hay DB configurada
        if os.environ.get('TESTING') or 'pytest' in os.environ.get('_', ''):
            db_url = 'sqlite:///:memory:'
        else:
            # Fallback para desarrollo local
            db_url = 'sqlite:///diferent777.db'
    
    # Render da postgres:// - SQLAlchemy necesita postgresql://
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configuración de conexión solo para PostgreSQL
    if 'postgresql' in db_url:
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'connect_args': {
                'connect_timeout': 10,
                'keepalives': 1,
                'keepalives_idle': 30,
                'keepalives_interval': 10,
                'keepalives_count': 5
            }
        }
    else:
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {}
    
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

    # ── Otras configuraciones desde Environment ──────────────────────────────────
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = int(os.environ.get('SESSION_LIFETIME', 86400))  # 24 horas

    # ── Extensions ──────────────────────────────────────────
    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Inicia sesión para continuar'
    login_manager.login_message_category = 'info'

    # User loader — MUST be after login_manager.init_app
    from models import Usuario
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Usuario, int(user_id))

    # ── Blueprints ──────────────────────────────────────────
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.productos import productos_bp
    from routes.ventas import ventas_bp
    from routes.reportes import reportes_bp
    from routes.admin import admin_bp
    from routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(productos_bp)
    app.register_blueprint(ventas_bp)
    app.register_blueprint(reportes_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # ── DB + seed ───────────────────────────────────────────
    with app.app_context():
        db.create_all()
        _seed()

    return app


def _seed():
    from models import Usuario, Sede, Categoria, Responsable, Producto, Configuracion
    from werkzeug.security import generate_password_hash

    # Solo seed si no hay usuarios (base de datos nueva)
    if Usuario.query.count() == 0:
        try:
            db.session.add_all([
                Usuario(nombre='Administrador', email='admin@diferent777.com',
                        password_hash=generate_password_hash('admin123'), rol='admin', activo=True),
                Usuario(nombre='Vendedor 1', email='vendedor@diferent777.com',
                        password_hash=generate_password_hash('vendedor123'), rol='vendedor', activo=True),
            ])
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error seeding usuarios: {e}")

    if Sede.query.count() == 0:
        try:
            db.session.add_all([Sede(nombre=n, activa=True)
                                for n in ['Sede Principal', 'Sede Norte', 'Sede Sur', 'Bodega']])
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error seeding sedes: {e}")

    if Categoria.query.count() == 0:
        try:
            cats = [('Camisetas','👕','#7c4dff'),('Pantalones','👖','#00e5ff'),
                    ('Zapatos','👟','#00e676'),('Accesorios','🧢','#d4a017'),
                    ('Vestidos','👗','#ff4081'),('Chaquetas','🧥','#ff6d00'),
                    ('Deportiva','🎽','#29b6f6'),('Ropa Interior','🩲','#ab47bc')]
            db.session.add_all([Categoria(nombre=n, emoji=e, color=c) for n,e,c in cats])
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error seeding categorias: {e}")

    if Responsable.query.count() == 0:
        try:
            db.session.add_all([Responsable(nombre=n, activo=True)
                                for n in ['Admin D777','Vendedor 1','Vendedor 2','Encargado Bodega']])
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error seeding responsables: {e}")

    if Producto.query.count() == 0:
        try:
            s1 = Sede.query.filter_by(nombre='Sede Principal').first()
            s2 = Sede.query.filter_by(nombre='Sede Norte').first()
            c1 = Categoria.query.filter_by(nombre='Camisetas').first()
            c2 = Categoria.query.filter_by(nombre='Pantalones').first()
            c3 = Categoria.query.filter_by(nombre='Zapatos').first()
            c4 = Categoria.query.filter_by(nombre='Accesorios').first()
            r1 = Responsable.query.first()
            
            if all([s1, s2, c1, c2, c3, c4, r1]):
                items = [
                    ('Camiseta Urban Classic','7501234567890',c1,'M',25000,65000,12,5,s1,r1,'Camiseta 100% algodón pima'),
                    ('Pantalón Cargo Street','7509876543210',c2,'32',55000,130000,8,5,s1,r1,'Pantalón cargo urbano'),
                    ('Zapatilla Runner X9','7504561237890',c3,'42',90000,220000,5,3,s2,r1,'Zapatilla deportiva premium'),
                    ('Gorra D777 Snapback','7507890123456',c4,'Única',15000,45000,20,5,s1,r1,'Gorra snapback exclusiva'),
                    ('Chaqueta Bomber','7503216549870',Categoria.query.filter_by(nombre='Chaquetas').first(),'L',120000,280000,4,2,s2,r1,'Chaqueta bomber edición especial'),
                ]
                db.session.add_all([
                    Producto(nombre=nm, codigo_barras=cb, categoria_id=cat.id, talla=t,
                             costo=co, precio_venta=pv, stock=st, stock_minimo=sm,
                             sede_id=sd.id, responsable_id=rp.id, descripcion=ds,
                             activo=True, fecha_ingreso=datetime.utcnow())
                    for nm,cb,cat,t,co,pv,st,sm,sd,rp,ds in items if cat
                ])
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error seeding productos: {e}")

    # Default store config
    try:
        for k, v in [('tienda_nombre','DIFERENT 777'),('tienda_nit',''),
                     ('tienda_direccion',''),('tienda_telefono',''),
                     ('tienda_email',''),('tienda_web','')]:
            if not Configuracion.query.filter_by(clave=k).first():
                db.session.add(Configuracion(clave=k, valor=v))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error seeding configuracion: {e}")


# ============================================================
# 👇 IMPORTANTE: Esta es la variable global que Gunicorn busca
# ============================================================
app = create_app()

# ============================================================
# 👇 Esto solo se ejecuta si corres el script directamente
# ============================================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)
