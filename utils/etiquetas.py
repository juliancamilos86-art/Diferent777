import io
import os
import barcode
from barcode.writer import ImageWriter
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

# Configura el tamaño EXACTO de tu etiqueta en centímetros.
# Ejemplo típico 4x3 cm. ¡Ajusta esto a tu rollo!
ANCHO_ETIQUETA_CM = 4.0
ALTO_ETIQUETA_CM = 3.0


def generar_pdf_etiquetas(productos):
    """
    Recibe una lista de objetos Producto y genera un PDF listo para imprimir.
    Cada página del PDF es exactamente una etiqueta física.
    """
    # Definir el tamaño de página (equivale a 1 etiqueta por página)
    ancho_puntos = ANCHO_ETIQUETA_CM * cm
    alto_puntos = ALTO_ETIQUETA_CM * cm
    page_size = (ancho_puntos, alto_puntos)

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=page_size)

    for prod in productos:
        # 1. Generar la imagen del código de barras (Code128 es el estándar)
        code128 = barcode.get('code128', str(prod.codigo_barras), writer=ImageWriter())

        img_buffer = io.BytesIO()
        code128.write(img_buffer, options={
            'module_width': 0.3,       # Grosor de las barras
            'module_height': 1.0,      # Alto de las barras en cm
            'font_size': 8,            # Tamaño del texto debajo de las barras
            'text_distance': 0.2,      # Distancia del texto a las barras
            'quiet_zone': 0.5          # Espacio en blanco a los lados
        })
        img_buffer.seek(0)

        # Guardar temporalmente la imagen para poder dibujarla en el PDF
        temp_img_path = f"temp_{prod.codigo_barras}.png"
        with open(temp_img_path, "wb") as f:
            f.write(img_buffer.read())

        # 2. Dibujar los elementos en la etiqueta
        # Dibujar Nombre del producto (opcional, truncado a 20 caracteres)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(ancho_puntos / 2, alto_puntos - (0.5 * cm), prod.nombre[:20])

        # Dibujar el código de barras centrado
        img_width = ancho_puntos * 0.85
        img_height = alto_puntos * 0.50
        x_img = (ancho_puntos - img_width) / 2
        y_img = (alto_puntos - img_height) / 2 - (0.2 * cm)
        c.drawImage(temp_img_path, x_img, y_img, width=img_width, height=img_height, preserveAspectRatio=True)

        # Dibujar el precio (opcional, al final de la etiqueta)
        c.setFont("Helvetica", 8)
        c.drawCentredString(ancho_puntos / 2, (0.2 * cm), f"${prod.precio_venta:,.0f}")

        # Guardar página y eliminar la imagen temporal
        c.showPage()
        if os.path.exists(temp_img_path):
            os.remove(temp_img_path)

    c.save()
    buffer.seek(0)
    return buffer
