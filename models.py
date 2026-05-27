from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), default='vendedor')
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    ventas = db.relationship('Venta', backref='usuario', lazy=True)

class Sede(db.Model):
    __tablename__ = 'sedes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(200))
    activa = db.Column(db.Boolean, default=True)
    productos = db.relationship('Producto', backref='sede', lazy=True)

class Categoria(db.Model):
    __tablename__ = 'categorias'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    emoji = db.Column(db.String(10), default='📦')
    color = db.Column(db.String(20), default='#7c4dff')
    productos = db.relationship('Producto', backref='categoria', lazy=True)

class Responsable(db.Model):
    __tablename__ = 'responsables'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    productos = db.relationship('Producto', backref='responsable', lazy=True)

class Producto(db.Model):
    __tablename__ = 'productos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    codigo_barras = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.Text)
    talla = db.Column(db.String(20))
    color = db.Column(db.String(50))
    costo = db.Column(db.Float, default=0)
    precio_venta = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    stock_minimo = db.Column(db.Integer, default=5)
    activo = db.Column(db.Boolean, default=True)
    fecha_ingreso = db.Column(db.DateTime, default=datetime.utcnow)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'))
    sede_id = db.Column(db.Integer, db.ForeignKey('sedes.id'))
    responsable_id = db.Column(db.Integer, db.ForeignKey('responsables.id'))
    items_venta = db.relationship('ItemVenta', backref='producto', lazy=True)

    @property
    def margen(self):
        if self.precio_venta > 0:
            return round((self.precio_venta - self.costo) / self.precio_venta * 100, 1)
        return 0

    @property
    def estado_stock(self):
        if self.stock == 0:
            return 'sin_stock'
        if self.stock <= self.stock_minimo:
            return 'stock_bajo'
        return 'ok'

class Venta(db.Model):
    __tablename__ = 'ventas'
    id = db.Column(db.Integer, primary_key=True)
    numero_factura = db.Column(db.String(20), unique=True, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    cliente_nombre = db.Column(db.String(150), default='Consumidor Final')
    cliente_doc = db.Column(db.String(20))
    metodo_pago = db.Column(db.String(30), default='efectivo')
    subtotal = db.Column(db.Float, default=0)
    descuento_pct = db.Column(db.Float, default=0)
    descuento_monto = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0)
    notas = db.Column(db.Text)
    estado = db.Column(db.String(20), default='completada')
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    sede_id = db.Column(db.Integer, db.ForeignKey('sedes.id'))
    items = db.relationship('ItemVenta', backref='venta', lazy=True, cascade='all, delete-orphan')
    sede = db.relationship('Sede', foreign_keys=[sede_id])

class ItemVenta(db.Model):
    __tablename__ = 'items_venta'
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('ventas.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    nombre_producto = db.Column(db.String(200))
    codigo_barras = db.Column(db.String(50))
    cantidad = db.Column(db.Integer, default=1)
    precio_unitario = db.Column(db.Float)
    subtotal = db.Column(db.Float)

class Configuracion(db.Model):
    __tablename__ = 'configuracion'
    id = db.Column(db.Integer, primary_key=True)
    clave = db.Column(db.String(100), unique=True, nullable=False)
    valor = db.Column(db.Text)

    @staticmethod
    def get(clave, default=''):
        c = Configuracion.query.filter_by(clave=clave).first()
        return c.valor if c else default

    @staticmethod
    def set(clave, valor):
        c = Configuracion.query.filter_by(clave=clave).first()
        if c:
            c.valor = valor
        else:
            db.session.add(Configuracion(clave=clave, valor=valor))
        db.session.commit()
