import io
import os
import barcode
from barcode.writer import ImageWriter
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

# 📌 MEDIDAS EXACTAS PARA TU ETIQUETA (32 mm de ancho x 25 mm de alto)
ANCHO_ETIQUETA_CM = 3.2
ALTO_ETIQUETA_CM = 2.5

def generar_pdf_etiquetas(productos):
    """
    Genera un PDF con etiquetas nítidas de 32x25mm para impresoras 3nStar.
    En este tamaño, solo se imprime el código de barras y su número (esencial para escanear).
    """
    ancho_puntos = ANCHO_ETIQUETA_CM * cm
    alto_puntos = ALTO_ETIQUETA_CM * cm
    page_size = (ancho_puntos, alto_puntos)

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=page_size)

    for prod in productos:
        # 1. Generar el código de barras (Code128) con configuración óptima para 203 DPI
        code128 = barcode.get('code128', str(prod.codigo_barras), writer=ImageWriter())
        
        img_buffer = io.BytesIO()
        code128.write(img_buffer, options={
            'module_width': 0.25,      # Barras finas pero legibles
            'module_height': 0.8,      # Altura de las barras en cm
            'font_size': 5,            # Números muy pequeños pero legibles en 25mm
            'text_distance': 0.15,     # Separación entre barras y números
            'quiet_zone': 0.6          # Espacio en blanco a los lados (necesario para el lector)
        })
        img_buffer.seek(0)

        # Guardar temporalmente la imagen
        temp_img_path = f"temp_{prod.codigo_barras}.png"
        with open(temp_img_path, "wb") as f:
            f.write(img_buffer.read())

        # 2. Dibujar SOLO el código de barras, centrado y sin deformar
        # Ocupamos el 90% del ancho y el 90% del alto para aprovechar al máximo el espacio
        img_width = ancho_puntos * 0.90
        img_height = alto_puntos * 0.90
        x_img = (ancho_puntos - img_width) / 2
        y_img = (alto_puntos - img_height) / 2
        
        # preserveAspectRatio=True asegura que el código NO se deforme
        c.drawImage(temp_img_path, x_img, y_img, width=img_width, height=img_height, preserveAspectRatio=True, anchor='c')

        # Guardar página y limpiar temporal
        c.showPage()
        if os.path.exists(temp_img_path):
            os.remove(temp_img_path)

    c.save()
    buffer.seek(0)
    return buffer
