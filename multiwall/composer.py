import os
from PIL import Image, ImageOps, ImageColor
from .config import DEFAULT_OPTIONS
from .logger import get_logger

logger = get_logger(__name__)

def open_image_try(path):
    """
    Intenta abrir una imagen con soporte robusto para AVIF y otros formatos.
    Usa Pillow directamente con manejo de errores mejorado.
    """
    logger.debug(f"Intentando abrir: {path}")
    logger.debug(f"Archivo existe: {os.path.exists(path)}")
    logger.debug(f"Es archivo: {os.path.isfile(path) if os.path.exists(path) else 'N/A'}")
    logger.debug(f"Tamaño: {os.path.getsize(path) if os.path.exists(path) else 'N/A'} bytes")
    logger.debug(f"Permisos: {oct(os.stat(path).st_mode) if os.path.exists(path) else 'N/A'}")
    
    try:
        # Intentar abrir con Pillow
        logger.debug(f"Abriendo con Image.open()...")
        img = Image.open(path)
        logger.debug(f"Imagen abierta: formato={img.format}, modo={img.mode}, tamaño={img.size}")
        
        # Convertir a RGBA para garantizar consistencia
        logger.debug(f"Convirtiendo a RGBA...")
        rgba_img = img.convert('RGBA')
        logger.debug(f"✅ Conversión exitosa: {rgba_img.mode}, {rgba_img.size}")
        return rgba_img
        
    except Exception as e:
        logger.error(f"❌ Error abriendo imagen {path}" f"Tipo: {type(e).__name__}" "Mensaje: {e}")
        
        import traceback
        traceback.print_exc()
        
        # Si es AVIF específicamente, dar más información
        if path.lower().endswith('.avif'):
            logger.debug(f"⚠️ Problema con archivo AVIF")
            try:
                from PIL import features
                logger.debug(f"AVIF support: %s", features.check('avif'))
                logger.debug(f"Available features: %s", features.get_supported())
            except:
                pass
        return None

def apply_mode_to_image(img, target_size, mode, bgcolor):
    tw, th = target_size
    logger.debug(f"Aplicando modo %s a imagen %s -> %s", mode, img.size, target_size)
    
    if mode == 'fill':
        result = ImageOps.fit(img, (tw, th), method=Image.LANCZOS)
    elif mode == 'fit':
        img_copy = img.copy()
        img_copy.thumbnail((tw, th), Image.LANCZOS)
        out = Image.new('RGBA', (tw, th), bgcolor)
        out.paste(img_copy, ((tw - img_copy.width) // 2, (th - img_copy.height) // 2), img_copy)
        result = out
    elif mode == 'stretch':
        result = img.resize((tw, th), Image.LANCZOS)
    elif mode == 'center':
        out = Image.new('RGBA', (tw, th), bgcolor)
        x = (tw - img.width) // 2
        y = (th - img.height) // 2
        out.paste(img, (x, y), img)
        result = out
    elif mode == 'tile':
        out = Image.new('RGBA', (tw, th), bgcolor)
        for y in range(0, th, img.height):
            for x in range(0, tw, img.width):
                out.paste(img, (x, y), img)
        result = out
    else:
        result = ImageOps.fit(img, (tw, th), method=Image.LANCZOS)
    
    logger.debug(f"Resultado: {result.size}")
    return result

def compose_image(monitors, states, scale_preview=None):
    # Obtener geometrías de los monitores
    rects = []
    for m in monitors:
        geom = m.get_geometry()
        rects.append((geom.x, geom.y, geom.width, geom.height))
        logger.debug(f"Monitor geometría: {geom.x}, {geom.y}, {geom.width}x{geom.height}")
    
    # Normalizar coordenadas
    min_x = min(r[0] for r in rects)
    min_y = min(r[1] for r in rects)
    norm = [(x - min_x, y - min_y, w, h) for (x, y, w, h) in rects]
    
    # Calcular tamaño total del canvas
    total_w = max(x + w for (x, y, w, h) in norm)
    total_h = max(y + h for (x, y, w, h) in norm)

    logger.debug(f"Canvas total: {total_w}x{total_h}")

    canvas = Image.new('RGBA', (total_w, total_h), DEFAULT_OPTIONS['background'])

    for i, (x, y, w, h) in enumerate(norm):
        st = states.get(str(i), {})
        file = st.get('file')
        mode = st.get('mode', DEFAULT_OPTIONS['mode'])
        bcolor = st.get('background', DEFAULT_OPTIONS['background'])
        bg_rgba = ImageColor.getcolor(bcolor, 'RGBA')
        
        img = None
        if file and os.path.exists(file):
            img = open_image_try(file)
            if img:
                logger.debug(f"Monitor {i}: Imagen cargada desde {file} (formato: {img.format if hasattr(img, 'format') else 'unknown'})")
            else:
                logger.warning(f"Monitor {i}: ⚠️ No se pudo cargar imagen desde {file}")
        
        if img:
            img2 = apply_mode_to_image(img, (w, h), mode, bg_rgba)
            canvas.paste(img2, (x, y), img2)
        else:
            # Si no hay imagen, rellenar con color de fondo
            filler = Image.new('RGBA', (w, h), bg_rgba)
            canvas.paste(filler, (x, y))
            if file:
                logger.error(f"Monitor {i}: ❌ Usando color de fondo (imagen falló)")
            else:
                logger.debug(f"Monitor {i}: Usando color de fondo {bcolor}")

    # Escalar para preview
    if scale_preview:
        ratio = min(scale_preview / total_w, scale_preview / total_h)
        if ratio < 1:
            new_w, new_h = int(total_w * ratio), int(total_h * ratio)
            logger.debug(f"Escalando preview a {new_w}x{new_h}")
            scaled = canvas.resize((new_w, new_h), Image.LANCZOS)
            # Debug: Guardar para verificar
            try:
                scaled.save('/tmp/multiwall_debug_preview.png')
                logger.debug(f"Preview guardado en /tmp/multiwall_debug_preview.png")
            except:
                pass
            return scaled
    
    return canvas