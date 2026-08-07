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
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        if os.environ.get('RENDER'):
            raise ValueError("SECRET_KEY no configurada en Render. Configúrala en Environment Variables.")
        secret_key = 'dev-secret-key-diferent777-2025'
    
    app.config['SECRET_KEY'] = secret_key
    
    # ── Configuración de Base de Datos ──────────────────────────────────────────
    db_url = os.environ.get('DATABASE_URL', '')
    
    if not db_url:
        if os.environ.get('TESTING') or 'pytest' in os.environ.get('_', ''):
            db_url = 'sqlite:///:memory:'
        else:
            db_url = 'sqlite:///diferent777.db'
    
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
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
    
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    # ── Otras configuraciones desde Environment ──────────────────────────────────
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = int(os.environ.get('SESSION_LIFETIME', 86400))

    # ── Extensions ──────────────────────────────────────────
    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Inicia sesión para continuar'
    login_manager.login_message_category = 'info'

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

    # ============================================================
    # SEED DE USUARIOS
    # ============================================================
    if Usuario.query.count() == 0:
        try:
            db.session.add_all([
                Usuario(nombre='Administrador', email='admin@diferent777.com',
                        password_hash=generate_password_hash('admin123'), rol='admin', activo=True),
                Usuario(nombre='Vendedor 1', email='vendedor@diferent777.com',
                        password_hash=generate_password_hash('vendedor123'), rol='vendedor', activo=True),
                Usuario(nombre='Vendedor 2', email='vendedor2@diferent777.com',
                        password_hash=generate_password_hash('vendedor123'), rol='vendedor', activo=True),
            ])
            db.session.commit()
            print("✅ Usuarios creados")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error seeding usuarios: {e}")

    # ============================================================
    # SEED DE SEDES
    # ============================================================
    if Sede.query.count() == 0:
        try:
            db.session.add_all([
                Sede(nombre='Sede Principal', activa=True),
                Sede(nombre='Sede Norte', activa=True),
                Sede(nombre='Sede Sur', activa=True),
                Sede(nombre='Bodega Central', activa=True),
            ])
            db.session.commit()
            print("✅ Sedes creadas")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error seeding sedes: {e}")

    # ============================================================
    # SEED DE CATEGORÍAS
    # ============================================================
    if Categoria.query.count() == 0:
        try:
            cats = [
                ('Camisetas', '👕', '#7c4dff'),
                ('Pantalones', '👖', '#00e5ff'),
                ('Zapatos', '👟', '#00e676'),
                ('Accesorios', '🧢', '#d4a017'),
                ('Vestidos', '👗', '#ff4081'),
                ('Chaquetas', '🧥', '#ff6d00'),
                ('Deportiva', '🎽', '#29b6f6'),
                ('Ropa Interior', '🩲', '#ab47bc'),
                ('Gorras', '🧢', '#f5c842'),
                ('Bolso', '👜', '#e91e63'),
            ]
            db.session.add_all([Categoria(nombre=n, emoji=e, color=c) for n, e, c in cats])
            db.session.commit()
            print("✅ Categorías creadas")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error seeding categorias: {e}")

    # ============================================================
    # SEED DE RESPONSABLES
    # ============================================================
    if Responsable.query.count() == 0:
        try:
            db.session.add_all([
                Responsable(nombre='Admin D777', activo=True),
                Responsable(nombre='Vendedor Principal', activo=True),
                Responsable(nombre='Vendedor Secundario', activo=True),
                Responsable(nombre='Encargado Bodega', activo=True),
            ])
            db.session.commit()
            print("✅ Responsables creados")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error seeding responsables: {e}")

    # ============================================================
    # SEED DE PRODUCTOS - VERSIÓN MEJORADA CON MÁS PRODUCTOS
    # ============================================================
    if Producto.query.count() == 0:
        try:
            sede1 = Sede.query.filter_by(nombre='Sede Principal').first()
            sede2 = Sede.query.filter_by(nombre='Sede Norte').first()
            sede3 = Sede.query.filter_by(nombre='Sede Sur').first()
            responsable = Responsable.query.first()
            
            # Obtener categorías
            cat_camisetas = Categoria.query.filter_by(nombre='Camisetas').first()
            cat_pantalones = Categoria.query.filter_by(nombre='Pantalones').first()
            cat_zapatos = Categoria.query.filter_by(nombre='Zapatos').first()
            cat_accesorios = Categoria.query.filter_by(nombre='Accesorios').first()
            cat_vestidos = Categoria.query.filter_by(nombre='Vestidos').first()
            cat_chaquetas = Categoria.query.filter_by(nombre='Chaquetas').first()
            cat_deportiva = Categoria.query.filter_by(nombre='Deportiva').first()
            cat_interior = Categoria.query.filter_by(nombre='Ropa Interior').first()
            cat_gorras = Categoria.query.filter_by(nombre='Gorras').first()
            cat_bolsos = Categoria.query.filter_by(nombre='Bolso').first()
            
            if all([sede1, sede2, sede3, responsable]):
                # ================================================
                # LISTA DE PRODUCTOS (20+ productos con stock)
                # ================================================
                productos_data = [
                    # CAMISETAS
                    ('Camiseta Urban Classic', '7501234567890', cat_camisetas, 'M', 25000, 65000, 20, 5, sede1, responsable, 'Camiseta 100% algodón pima'),
                    ('Camiseta D777 Premium', '7501234567891', cat_camisetas, 'L', 30000, 75000, 15, 5, sede1, responsable, 'Camiseta edición limitada'),
                    ('Camiseta Sport Tech', '7501234567892', cat_camisetas, 'XL', 22000, 58000, 12, 5, sede1, responsable, 'Camiseta deportiva transpirable'),
                    ('Camiseta Vintage', '7501234567893', cat_camisetas, 'S', 20000, 55000, 18, 5, sede1, responsable, 'Camiseta estilo retro'),
                    ('Camiseta Oversize', '7501234567894', cat_camisetas, 'M', 28000, 68000, 10, 5, sede2, responsable, 'Camiseta oversize algodón'),
                    
                    # PANTALONES
                    ('Pantalón Cargo Street', '7509876543210', cat_pantalones, '32', 55000, 130000, 8, 5, sede1, responsable, 'Pantalón cargo urbano'),
                    ('Pantalón Jean Clásico', '7509876543211', cat_pantalones, '34', 45000, 110000, 12, 5, sede1, responsable, 'Jean clásico azul'),
                    ('Pantalón Deportivo', '7509876543212', cat_pantalones, 'M', 35000, 85000, 15, 5, sede2, responsable, 'Pantalón jogger deportivo'),
                    ('Pantalón Formal', '7509876543213', cat_pantalones, '36', 60000, 150000, 6, 5, sede1, responsable, 'Pantalón formal para oficina'),
                    ('Short Deportivo', '7509876543214', cat_pantalones, 'L', 28000, 65000, 20, 5, sede3, responsable, 'Short deportivo verano'),
                    
                    # ZAPATOS
                    ('Zapatilla Runner X9', '7504561237890', cat_zapatos, '42', 90000, 220000, 5, 3, sede2, responsable, 'Zapatilla deportiva premium'),
                    ('Zapatilla Urban Style', '7504561237891', cat_zapatos, '40', 75000, 180000, 8, 3, sede1, responsable, 'Zapatilla casual urbana'),
                    ('Zapatilla Running Pro', '7504561237892', cat_zapatos, '41', 110000, 260000, 4, 3, sede2, responsable, 'Zapatilla running profesional'),
                    ('Botas Casual', '7504561237893', cat_zapatos, '43', 85000, 200000, 6, 3, sede3, responsable, 'Botas casual de cuero'),
                    ('Sandalias Verano', '7504561237894', cat_zapatos, '39', 35000, 85000, 15, 3, sede1, responsable, 'Sandalias veraniegas'),
                    
                    # CHAQUETAS
                    ('Chaqueta Bomber', '7503216549870', cat_chaquetas, 'L', 120000, 280000, 4, 2, sede2, responsable, 'Chaqueta bomber edición especial'),
                    ('Chaqueta Impermeable', '7503216549871', cat_chaquetas, 'M', 95000, 220000, 6, 2, sede1, responsable, 'Chaqueta impermeable urbana'),
                    ('Chaqueta Deportiva', '7503216549872', cat_chaquetas, 'XL', 80000, 190000, 8, 2, sede2, responsable, 'Chaqueta deportiva ligera'),
                    
                    # ACCESORIOS Y GORRAS
                    ('Gorra D777 Snapback', '7507890123456', cat_gorras, 'Única', 15000, 45000, 20, 5, sede1, responsable, 'Gorra snapback exclusiva'),
                    ('Gorra Trucker', '7507890123457', cat_gorras, 'Única', 12000, 35000, 25, 5, sede2, responsable, 'Gorra trucker mesh'),
                    ('Bolso D777', '7507890123458', cat_bolsos, 'Única', 45000, 110000, 10, 5, sede1, responsable, 'Bolso de edición limitada'),
                    ('Mochila Urbana', '7507890123459', cat_bolsos, 'Única', 55000, 130000, 8, 5, sede2, responsable, 'Mochila urbana resistente'),
                    
                    # VESTIDOS
                    ('Vestido Floral', '7501234567895', cat_vestidos, 'M', 65000, 160000, 7, 5, sede1, responsable, 'Vestido floral verano'),
                    ('Vestido Formal', '7501234567896', cat_vestidos, 'L', 80000, 190000, 5, 5, sede1, responsable, 'Vestido formal elegante'),
                    ('Vestido Casual', '7501234567897', cat_vestidos, 'S', 55000, 135000, 10, 5, sede3, responsable, 'Vestido casual diario'),
                    
                    # DEPORTIVA
                    ('Conjunto Deportivo', '7501234567898', cat_deportiva, 'M', 70000, 170000, 12, 5, sede2, responsable, 'Conjunto deportivo completo'),
                    ('Camiseta Deportiva', '7501234567899', cat_deportiva, 'L', 30000, 75000, 15, 5, sede2, responsable, 'Camiseta deportiva dry-fit'),
                    ('Pantalón Deportivo', '7509876543215', cat_deportiva, 'M', 40000, 95000, 10, 5, sede2, responsable, 'Pantalón deportivo elástico'),
                    
                    # ROPA INTERIOR
                    ('Boxer Clásico', '7501234567888', cat_interior, 'M', 15000, 35000, 30, 5, sede1, responsable, 'Boxer clásico algodón'),
                    ('Bóxer Deportivo', '7501234567889', cat_interior, 'L', 18000, 42000, 25, 5, sede2, responsable, 'Bóxer deportivo transpirable'),
                    ('Camiseta Interior', '7501234567890', cat_interior, 'M', 12000, 28000, 35, 5, sede1, responsable, 'Camiseta interior algodón'),
                ]
                
                # Filtrar productos donde la categoría existe
                productos_validos = []
                for item in productos_data:
                    nombre, cb, categoria, talla, costo, precio, stock, stock_min, sede, resp, desc = item
                    if categoria:  # Solo si la categoría existe
                        productos_validos.append(
                            Producto(
                                nombre=nombre,
                                codigo_barras=cb,
                                categoria_id=categoria.id,
                                talla=talla,
                                costo=costo,
                                precio_venta=precio,
                                stock=stock,
                                stock_minimo=stock_min,
                                sede_id=sede.id if sede else None,
                                responsable_id=resp.id if resp else None,
                                descripcion=desc,
                                activo=True,
                                fecha_ingreso=datetime.utcnow()
                            )
                        )
                
                db.session.add_all(productos_validos)
                db.session.commit()
                print(f"✅ {len(productos_validos)} productos creados")
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error seeding productos: {e}")
            import traceback
            traceback.print_exc()

    # ============================================================
    # SEED DE CONFIGURACIÓN
    # ============================================================
    try:
        config_data = [
            ('tienda_nombre', 'DIFERENT 777'),
            ('tienda_nit', '900.123.456-7'),
            ('tienda_direccion', 'Cra 45 # 67-89, Medellín'),
            ('tienda_telefono', '300 123 4567'),
            ('tienda_email', 'info@diferent777.com'),
            ('tienda_web', 'www.diferent777.com'),
            ('iva_porcentaje', '19'),
        ]
        for k, v in config_data:
            if not Configuracion.query.filter_by(clave=k).first():
                db.session.add(Configuracion(clave=k, valor=str(v)))
        db.session.commit()
        print("✅ Configuración creada")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error seeding configuracion: {e}")


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
