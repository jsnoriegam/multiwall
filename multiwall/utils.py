import os
from gi.repository import GdkPixbuf, GLib, Gtk
from .logger import get_logger

logger = get_logger(__name__)


def is_running_in_docker():
    """Check if running inside Docker container."""
    return os.path.exists('/.dockerenv') or os.path.exists('/run/.containerenv')


def is_running_in_appimage():
    """Check if running inside an AppImage."""
    return os.getenv('APPIMAGE') is not None


def set_icon_with_fallback(button, icon_name, fallback_label='📁'):
    """
    Set icon on button with fallback to emoji if icon theme not available.
    
    This handles cases where symbolic icons are not available in Docker/AppImage
    due to missing system icon themes. Also handles custom GNOME icon themes
    that may not be available in containerized environments.
    
    Args:
        button: Gtk.Button instance
        icon_name: Name of the symbolic icon to try
        fallback_label: Emoji or text to use if icon fails to load
    """
    # Always use fallback in Docker/AppImage for consistency
    if is_running_in_docker() or is_running_in_appimage():
        logger.debug(f"Running in containerized environment, using emoji fallback for '{icon_name}'")
        button.set_label(fallback_label)
    else:
        try:
            # Try to set the symbolic icon for native installations
            button.set_icon_name(icon_name)
            logger.debug(f"Icon '{icon_name}' set successfully")
        except Exception as e:
            logger.debug(f"Failed to set icon '{icon_name}': {e}, using fallback")
            # Fallback: use label with emoji instead of icon
            button.set_label(fallback_label)


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