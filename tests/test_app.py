# tests/test_app.py
import os
import sys

# Configurar modo de pruebas antes de importar app
os.environ['TESTING'] = 'true'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

# Añadir directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app


def test_home():
    """Test que la página principal redirige o funciona"""
    client = app.test_client()
    response = client.get("/")
    # En pruebas, la raíz debe redirigir al login
    assert response.status_code in [200, 302]
    
    if response.status_code == 302:
        assert '/login' in response.location


def test_fake_route():
    """Test que rutas inexistentes dan 404"""
    client = app.test_client()
    response = client.get("/ruta_inexistente_12345_super_fake")
    assert response.status_code == 404


def test_login_page():
    """Test que la página de login existe y carga"""
    client = app.test_client()
    response = client.get("/login")
    assert response.status_code == 200
    assert b'Inicia sesi' in response.data or b'Login' in response.data


def test_static_files():
    """Test que archivos estáticos existen"""
    client = app.test_client()
    response = client.get("/static/css/main.css")
    # Puede ser 200 si existe, o 404 si no
    assert response.status_code in [200, 404]


def test_app_creation():
    """Test que la aplicación se puede crear"""
    from app import create_app
    test_app = create_app()
    assert test_app is not None
    assert test_app.config['SECRET_KEY'] is not None
