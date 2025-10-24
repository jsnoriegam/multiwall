import os
from PIL import Image, ImageOps, ImageColor, ImageDraw, ImageFont
from .config import DEFAULT_OPTIONS
from .logger import get_logger

logger = get_logger(__name__)

def open_image_try(path):
    """
    Try to open an image with robust support for AVIF and other formats.
    Uses Pillow directly with improved error handling.
    
    Args:
        path: Path to the image file
        
    Returns:
        PIL.Image: RGBA image or None if failed
    """
    logger.debug(f"Attempting to open image: {path}")
    
    if not os.path.exists(path):
        logger.error(f"Image file does not exist: {path}")
        return None
    
    logger.debug(f"File exists: size={os.path.getsize(path)} bytes, "
                f"permissions={oct(os.stat(path).st_mode)}")
    
    try:
        # Try to open with Pillow
        logger.debug(f"Opening with Image.open()...")
        img = Image.open(path)
        logger.debug(f"Image opened: format={img.format}, mode={img.mode}, size={img.size}")
        
        # Convert to RGBA for consistency
        logger.debug(f"Converting to RGBA...")
        rgba_img = img.convert('RGBA')
        logger.debug(f"Conversion successful: {rgba_img.mode}, {rgba_img.size}")
        return rgba_img
        
    except Exception as e:
        logger.error(f"Error opening image {path}: {type(e).__name__}: {e}")
        
        # If AVIF specifically, provide detailed diagnostics
        if path.lower().endswith('.avif'):
            logger.warning(f"Problem with AVIF file")
            
            # Check Pillow version and features
            try:
                logger.debug(f"Pillow version: {Image.__version__}")
                logger.debug(f"Pillow location: {Image.__file__}")
                
                from PIL import features
                
                # Check AVIF support
                try:
                    avif_support = features.check('avif')
                    logger.error(f"AVIF support in Pillow: {avif_support}")
                    
                    if not avif_support:
                        logger.error("❌ Pillow was not compiled with AVIF support")
                        logger.error("To fix: pip install --no-binary Pillow Pillow")
                except Exception as feat_err:
                    logger.error(f"Cannot check AVIF feature: {feat_err}")
                
                # List all supported features
                try:
                    supported_features = []
                    for feat in ['webp', 'webp_anim', 'webp_mux', 'libjpeg_turbo', 'avif']:
                        try:
                            if features.check(feat):
                                supported_features.append(feat)
                        except:
                            pass
                    logger.debug(f"Supported features: {supported_features}")
                except Exception:
                    pass
                
                # Check registered extensions
                try:
                    extensions = Image.registered_extensions()
                    avif_registered = any('.avif' in ext for ext in extensions.keys())
                    logger.debug(f"AVIF extension registered: {avif_registered}")
                    if avif_registered:
                        avif_handler = extensions.get('.avif', 'unknown')
                        logger.debug(f"AVIF handler: {avif_handler}")
                except Exception:
                    pass
                    
            except ImportError:
                logger.error("Cannot import PIL.features for diagnostics")
            except Exception as diag_err:
                logger.error(f"Error during AVIF diagnostics: {diag_err}")
        
        return None


def apply_mode_to_image(img, target_size, mode, bgcolor):
    """
    Apply display mode to an image.
    
    Args:
        img: PIL Image
        target_size: Target (width, height)
        mode: Display mode (fill, fit, stretch, center, tile)
        bgcolor: Background color as RGBA tuple
        
    Returns:
        PIL.Image: Processed image
    """
    tw, th = target_size
    logger.debug(f"Applying mode '{mode}' to image {img.size} -> {target_size}")
    
    if mode == 'fill':
        # Crop to fill entire area
        result = ImageOps.fit(img, (tw, th), method=Image.LANCZOS)
        
    elif mode == 'fit':
        # Scale to fit within area, maintaining aspect ratio
        img_copy = img.copy()
        img_copy.thumbnail((tw, th), Image.LANCZOS)
        out = Image.new('RGBA', (tw, th), bgcolor)
        out.paste(img_copy, ((tw - img_copy.width) // 2, (th - img_copy.height) // 2), img_copy)
        result = out
        
    elif mode == 'stretch':
        # Stretch to exact size (may distort)
        result = img.resize((tw, th), Image.LANCZOS)
        
    elif mode == 'center':
        # Center image without scaling
        out = Image.new('RGBA', (tw, th), bgcolor)
        x = (tw - img.width) // 2
        y = (th - img.height) // 2
        out.paste(img, (x, y), img)
        result = out
        
    elif mode == 'tile':
        # Tile image to fill area
        out = Image.new('RGBA', (tw, th), bgcolor)
        for y in range(0, th, img.height):
            for x in range(0, tw, img.width):
                out.paste(img, (x, y), img)
        result = out
        
    else:
        logger.warning(f"Unknown mode '{mode}', using 'fill' as fallback")
        result = ImageOps.fit(img, (tw, th), method=Image.LANCZOS)
    
    logger.debug(f"Result image size: {result.size}")
    return result


def add_monitor_numbers(image, monitor_positions, scale_ratio=1.0, position='top-left'):
    """
    Add monitor numbers to the preview image.
    
    Args:
        image: PIL Image to draw on
        monitor_positions: List of (x, y, w, h) tuples for each monitor
        scale_ratio: Scale ratio applied to the image (for positioning)
        position: Position for the label ('top-left' or 'top-right')
        
    Returns:
        PIL.Image: Image with monitor numbers drawn
    """
    logger.debug(f"Adding monitor numbers, scale_ratio={scale_ratio}, position={position}")
    
    # Create a copy to draw on
    img_with_numbers = image.copy()
    draw = ImageDraw.Draw(img_with_numbers)
    
    # Try to use a good font, fallback to default
    try:
        # Calculate font size based on image size
        avg_dimension = (image.width + image.height) / 2
        font_size = int(avg_dimension * 0.04)  # 4% of average dimension
        font_size = max(24, min(font_size, 72))  # Between 24 and 72 pixels
        
        # Try different font paths
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",  # macOS
        ]
        
        font = None
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    font = ImageFont.truetype(font_path, font_size)
                    logger.debug(f"Using font: {font_path} at size {font_size}")
                    break
                except Exception as e:
                    logger.debug(f"Could not load font {font_path}: {e}")
        
        if font is None:
            logger.debug("Using default font")
            font = ImageFont.load_default()
            
    except Exception as e:
        logger.warning(f"Error loading font: {e}, using default")
        font = ImageFont.load_default()
        font_size = 20
    
    # Draw number for each monitor
    for i, (x, y, w, h) in enumerate(monitor_positions):
        # Scale position according to preview scale
        x_scaled = int(x * scale_ratio)
        y_scaled = int(y * scale_ratio)
        w_scaled = int(w * scale_ratio)
        
        # Monitor number (1-indexed for users)
        text = str(i + 1)
        
        # Get text bounding box for accurate measurements
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Padding around text
        padding = int(font_size * 0.5)
        
        # Position based on preference (top-left by default)
        if position == 'top-right':
            text_x = x_scaled + w_scaled - text_width - padding
        else:  # top-left
            text_x = x_scaled + padding
        
        text_y = y_scaled + padding
        
        # Background padding - más generoso para centrar mejor
        bg_padding_h = int(font_size * 0.4)  # Padding horizontal
        bg_padding_v = int(font_size * 0.5)  # Padding vertical (más grande)
        
        # Calculate background rectangle centered on text
        # bbox puede tener offsets, así que calculamos desde el baseline
        bg_rect = [
            text_x - bg_padding_h,                    # left
            text_y + bbox[1] - bg_padding_v,         # top
            text_x + text_width + bg_padding_h,      # right
            text_y + bbox[3] + bg_padding_v          # bottom
        ]
        
        # Create semi-transparent overlay ONLY for the rounded rectangle area
        overlay = Image.new('RGBA', (
            bg_rect[2] - bg_rect[0],  # width of background
            bg_rect[3] - bg_rect[1]   # height of background
        ), (0, 0, 0, 0))
        
        overlay_draw = ImageDraw.Draw(overlay)
        # Draw rectangle at (0,0) since overlay is sized to background
        overlay_draw.rounded_rectangle(
            [0, 0, overlay.width, overlay.height],
            radius=int(font_size * 0.2),
            fill=(0, 0, 0, 180)  # Semi-transparent black
        )
        
        # Paste the overlay at the correct position
        img_with_numbers.paste(
            overlay,
            (bg_rect[0], bg_rect[1]),  # paste position
            overlay  # use overlay as mask
        )
        
        # Redraw on the composited image
        draw = ImageDraw.Draw(img_with_numbers)
        
        # Draw white text
        draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255, 255))
        
        logger.debug(f"Monitor {i+1} label drawn at ({text_x}, {text_y})")
    
    return img_with_numbers


def compose_image(monitors, states, scale_preview=None):
    """
    Compose the final wallpaper image from monitor configurations.
    
    Args:
        monitors: List of GDK monitor objects
        states: Dict of monitor states (image, mode, background)
        scale_preview: Optional max dimension for preview scaling
        
    Returns:
        PIL.Image: Composed wallpaper image
    """
    logger.info("=== Starting image composition ===")
    
    # Get monitor geometries
    rects = []
    for i, m in enumerate(monitors):
        geom = m.get_geometry()
        rects.append((geom.x, geom.y, geom.width, geom.height))
        logger.debug(f"Monitor {i} geometry: {geom.x}, {geom.y}, {geom.width}x{geom.height}")
    
    # Normalize coordinates
    min_x = min(r[0] for r in rects)
    min_y = min(r[1] for r in rects)
    norm = [(x - min_x, y - min_y, w, h) for (x, y, w, h) in rects]
    logger.debug(f"Normalized coordinates, offset: ({min_x}, {min_y})")
    
    # Calculate total canvas size
    total_w = max(x + w for (x, y, w, h) in norm)
    total_h = max(y + h for (x, y, w, h) in norm)
    logger.info(f"Total canvas size: {total_w}x{total_h}")

    # Create canvas
    canvas = Image.new('RGBA', (total_w, total_h), DEFAULT_OPTIONS['background'])

    # Process each monitor
    for i, (x, y, w, h) in enumerate(norm):
        st = states.get(str(i), {})
        file = st.get('file')
        mode = st.get('mode', DEFAULT_OPTIONS['mode'])
        bcolor = st.get('background', DEFAULT_OPTIONS['background'])
        bg_rgba = ImageColor.getcolor(bcolor, 'RGBA')
        
        logger.debug(f"Processing monitor {i}: mode={mode}, bg={bcolor}")
        
        img = None
        if file and os.path.exists(file):
            img = open_image_try(file)
            if img:
                logger.info(f"Monitor {i}: Image loaded from {os.path.basename(file)}")
            else:
                logger.warning(f"Monitor {i}: Could not load image from {file}")
        
        if img:
            # Apply display mode
            img2 = apply_mode_to_image(img, (w, h), mode, bg_rgba)
            canvas.paste(img2, (x, y), img2)
            logger.debug(f"Monitor {i}: Image pasted at ({x}, {y})")
        else:
            # Fill with background color if no image
            filler = Image.new('RGBA', (w, h), bg_rgba)
            canvas.paste(filler, (x, y))
            if file:
                logger.warning(f"Monitor {i}: Using background color (image load failed)")
            else:
                logger.debug(f"Monitor {i}: Using background color (no image selected)")

    # Scale for preview if requested
    if scale_preview:
        ratio = min(scale_preview / total_w, scale_preview / total_h)
        if ratio < 1:
            new_w, new_h = int(total_w * ratio), int(total_h * ratio)
            logger.debug(f"Scaling preview to {new_w}x{new_h} (ratio: {ratio:.2f})")
            scaled = canvas.resize((new_w, new_h), Image.LANCZOS)
            
            # Add monitor numbers to the scaled preview
            scaled_with_numbers = add_monitor_numbers(scaled, norm, scale_ratio=ratio, position='top-left')
            
            # Debug: save to verify (optional)
            try:
                debug_path = '/tmp/multiwall_debug_preview.png'
                scaled_with_numbers.save(debug_path)
                logger.debug(f"Debug preview saved to {debug_path}")
            except Exception as e:
                logger.debug(f"Could not save debug preview: {e}")
            
            return scaled_with_numbers
    
    logger.info(f"Composition complete: {canvas.size}")
    return canvas