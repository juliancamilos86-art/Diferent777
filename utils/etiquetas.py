import io
import os
import barcode
from barcode.writer import ImageWriter
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

#  MEDIDAS EXACTAS PARA TU ETIQUETA (32 mm ancho x 25 mm alto)
ANCHO_ETIQUETA_CM = 3.2
ALTO_ETIQUETA_CM = 2.5

def generar_pdf_etiquetas(productos):
    """
    Genera un PDF con etiquetas nítidas de 32x25mm para impresoras 3nStar.
    Solo imprime el código de barras y su número, ocupando todo el espacio útil.
    """
    ancho_puntos = ANCHO_ETIQUETA_CM * cm
    alto_puntos = ALTO_ETIQUETA_CM * cm
    page_size = (ancho_puntos, alto_puntos)

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=page_size)

    for prod in productos:
        # Generar el código de barras con configuración para 203 DPI
        code128 = barcode.get('code128', str(prod.codigo_barras), writer=ImageWriter())
        
        img_buffer = io.BytesIO()
        code128.write(img_buffer, options={
            'module_width': 0.2,       # Barras delgadas (203 DPI)
            'module_height': 1.0,      # Alto de las barras en cm
            'font_size': 4,            # Números muy pequeños para 25mm
            'text_distance': 0.1,      # Separación barras/números
            'quiet_zone': 0.3          # Poco espacio en blanco (etiqueta pequeña)
        })
        img_buffer.seek(0)

        # Guardar temporalmente
        temp_img_path = f"temp_{prod.codigo_barras}.png"
        with open(temp_img_path, "wb") as f:
            f.write(img_buffer.read())

        # Dibujar SOLO el código de barras ocupando el 95% del espacio
        img_width = ancho_puntos * 0.95
        img_height = alto_puntos * 0.95
        x_img = (ancho_puntos - img_width) / 2
        y_img = (alto_puntos - img_height) / 2
        
        c.drawImage(temp_img_path, x_img, y_img, width=img_width, height=img_height, preserveAspectRatio=True, anchor='c')

        c.showPage()
        if os.path.exists(temp_img_path):
            os.remove(temp_img_path)

    c.save()
    buffer.seek(0)
    return buffer
