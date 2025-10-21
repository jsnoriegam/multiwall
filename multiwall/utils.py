from gi.repository import GdkPixbuf, GLib


def pil_to_pixbuf(pil_image):
    """
    Convierte una imagen PIL a GdkPixbuf para GTK4.
    
    Args:
        pil_image: PIL.Image object
        
    Returns:
        GdkPixbuf.Pixbuf
    """
    # Asegurar que la imagen esté en RGB
    if pil_image.mode != 'RGB':
        pil_image = pil_image.convert('RGB')
    
    # Obtener dimensiones
    width, height = pil_image.size
    
    # Convertir a bytes
    data = pil_image.tobytes()
    
    # Crear GLib.Bytes
    bytes_data = GLib.Bytes.new(data)
    
    # Crear Pixbuf desde bytes
    # Parámetros: bytes, colorspace, has_alpha, bits_per_sample, width, height, rowstride
    pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(
        bytes_data,
        GdkPixbuf.Colorspace.RGB,
        False,  # No alpha
        8,      # 8 bits por muestra
        width,
        height,
        width * 3  # rowstride: 3 bytes por pixel (RGB)
    )
    
    return pixbuf