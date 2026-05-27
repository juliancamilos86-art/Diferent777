# test_app.py
from app import app  # Esto funcionará SOLO si añadiste 'app = create_app()' al final de app.py

def test_home():
    client = app.test_client()
    response = client.get("/")
    # La raíz probablemente redirige al login
    assert response.status_code in [200, 302]

def test_fake_route():
    client = app.test_client()
    response = client.get("/ruta_inexistente")
    assert response.status_code == 404

def test_login_page():
    """Test adicional: verificar que la página de login existe"""
    client = app.test_client()
    response = client.get("/login")
    assert response.status_code == 200

def test_app_creation():
    """Test para verificar que la app se crea correctamente"""
    from app import create_app
    test_app = create_app()
    assert test_app is not None