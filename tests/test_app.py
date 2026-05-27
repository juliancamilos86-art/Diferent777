# tests/test_app.py
import sys
import os

# Añadir el directorio raíz al path de Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ahora importar app
from app import app

def test_home():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code in [200, 302]

def test_fake_route():
    client = app.test_client()
    response = client.get("/ruta_inexistente")
    assert response.status_code == 404
