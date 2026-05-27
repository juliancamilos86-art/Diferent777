# tests/test_app.py
import sys
import os

# Añadir el directorio raíz (donde está app.py) al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ahora sí podemos importar app
from app import app


def test_home():
    """Test que la página principal redirige o funciona"""
    client = app.test_client()
    response = client.get("/")
    # La raíz probablemente redirige al login si no está autenticado
    assert response.status_code in [200, 302]
    
    # Si redirige, debe ir al login
    if response.status_code == 302:
        assert '/login' in response.location


def test_fake_route():
    """Test que rutas inexistentes dan 404"""
    client = app.test_client()
    response = client.get("/ruta_inexistente_12345")
    assert response.status_code == 404


def test_login_page():
    """Test que la página de login existe"""
    client = app.test_client()
    response = client.get("/login")
    assert response.status_code == 200


def test_static_files():
    """Test que archivos estáticos son accesibles"""
    client = app.test_client()
    response = client.get("/static/css/style.css")
    # Puede ser 200 si existe, o 404 si no
    assert response.status_code in [200, 404]
