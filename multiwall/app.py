import i18n
import os
import sys
from pathlib import Path
from .logger import get_logger, setup_logger
import logging

# Configurar logger con nivel DEBUG si se pasa --debug
if '--debug' in sys.argv:
    setup_logger('multiwall', logging.DEBUG)
    sys.argv.remove('--debug')
else:
    setup_logger('multiwall', logging.INFO)

logger = get_logger(__name__)

# Asegurar UTF-8 para emojis
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Configuración de i18n
translations_path = Path(__file__).parent / 'translations'
i18n.load_path.clear()
i18n.load_path.append(str(translations_path))
i18n.set('filename_format', '{locale}.{format}')
i18n.set('file_format', 'json')
i18n.set('fallback', 'en')
i18n.set('error_on_missing_translation', False)
i18n.set('error_on_missing_placeholder', False)

# Detectar idioma del sistema
def detect_system_language():
    lang = os.getenv('LANGUAGE')
    if lang and lang != 'C':
        detected = lang.split(':')[0][:2]
        logger.debug(f"Language detected from LANGUAGE: {detected}")
        return detected
    
    lang = os.getenv('LANG')
    if lang and lang != 'C':
        detected = lang.split('_')[0]
        logger.debug(f"Language detected from LANG: {detected}")
        return detected
    
    try:
        import locale
        system_lang, _ = locale.getdefaultlocale()
        if system_lang and system_lang != 'C':
            detected = system_lang[:2]
            logger.debug(f"Language detected from locale: {detected}")
            return detected
    except Exception as e:
        logger.error(f"Error detectando locale: {e}")
    
    logger.info("Using default language: en")
    return 'en'

detected_lang = detect_system_language()
i18n.set('locale', detected_lang)

logger.debug(f"Ruta de traducciones: {translations_path}")
logger.debug(f"Ruta existe: {translations_path.exists()}")
if translations_path.exists():
    logger.debug(f"Archivos en translations: {list(translations_path.glob('*.json'))}")

import subprocess
from gi import require_version
require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf, Gio
from .config import load_config, save_config
from .composer import compose_image
from .monitor_row import MonitorRow
from .utils import pil_to_pixbuf
from .image_sidebar import ImageSidebar


# Detectar si estamos en Docker
def is_running_in_docker():
    return os.path.exists('/.dockerenv') or os.path.exists('/run/.containerenv')

# Usar directorio compartido con el host
if is_running_in_docker():
    TMP_OUTPUT = str(Path.home() / ".config" / "multiwall" / "current_wallpaper.jpg")
else:
    TMP_OUTPUT = "/tmp/multiwall_combined.jpg"


def get_default_pictures_directory():
    """Obtiene el directorio de imágenes predeterminado del sistema."""
    try:
        # Intentar obtener desde XDG user dirs
        result = subprocess.run(
            ['xdg-user-dir', 'PICTURES'],
            capture_output=True,
            text=True,
            check=True
        )
        pictures_dir = result.stdout.strip()
        if pictures_dir and os.path.exists(pictures_dir):
            logger.debug(f"Directorio de imágenes del sistema: {pictures_dir}")
            return pictures_dir
    except Exception as e:
        logger.error(f"No se pudo obtener xdg-user-dir: {e}")
    
    # Fallback: intentar ubicaciones comunes según el idioma
    home = Path.home()
    common_names = ['Pictures', 'Imágenes', 'Images', 'Bilder', 'Imagenes']
    
    for name in common_names:
        candidate = home / name
        if candidate.exists():
            logger.debug(f"Directorio de imágenes encontrado: {candidate}")
            return str(candidate)
    
    # Último fallback: HOME
    logger.debug(f"Usando directorio HOME como fallback: {home}")
    return str(home)


class MultiWallApp(Gtk.Application):
    def __init__(self, app = None):
        if not Gdk.Display.get_default():
            raise RuntimeError(
                "No se detectó un display. Asegúrate de:\n"
                "1. Tener DISPLAY configurado (ej: export DISPLAY=:0)\n"
                "2. Ejecutar en un entorno con GUI (no en contenedor sin X11)\n"
                "3. Tener permisos de acceso al display"
            )
        
        super().__init__(application_id='com.multiwall.app')
        self.settings = load_config()
        # Usar el último directorio guardado, o detectar el del sistema
        self.last_directory = self.settings.get('last_directory', get_default_pictures_directory())
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.window = Gtk.ApplicationWindow(
            application=app,
            title=i18n.t('app.title'),
            default_width=1200,
            default_height=700
        )
        self.build_ui()
        self.window.present()

    def build_ui(self):
        # Contenedor principal horizontal: contenido + sidebar
        main_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.window.set_child(main_container)

        # === ÁREA PRINCIPAL ===
        main = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=10,
            margin_top=10,
            margin_bottom=10,
            margin_start=10,
            margin_end=10
        )
        main.set_hexpand(True)
        main_container.append(main)

        header = Gtk.Label(label=f"<b>{i18n.t('app.header')}</b>")
        header.set_use_markup(True)
        header.set_margin_bottom(10)
        main.append(header)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        main.append(content)

        # === ÁREA DE PREVIEW ===
        preview_frame = Gtk.Frame()
        preview_frame.set_label(i18n.t('app.preview_label'))
        preview_frame.set_vexpand(True)
        content.append(preview_frame)

        preview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        preview_box.set_margin_top(10)
        preview_box.set_margin_bottom(10)
        preview_box.set_margin_start(10)
        preview_box.set_margin_end(10)
        preview_frame.set_child(preview_box)

        self.preview = Gtk.Image()
        self.preview.set_vexpand(True)
        preview_box.append(self.preview)

        # === ÁREA DE CONTROLES ===
        controls_frame = Gtk.Frame()
        controls_frame.set_label(i18n.t('app.controls_label'))
        content.append(controls_frame)

        display = Gdk.Display.get_default()
        monitor_list = display.get_monitors()
        self.monitors = [monitor_list.get_item(i) for i in range(monitor_list.get_n_items())]
        saved = self.settings.get('monitors', {})

        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(200)
        scroll.set_max_content_height(250)
        scroll.set_vexpand(False)
        controls_frame.set_child(scroll)

        list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        list_box.set_margin_top(10)
        list_box.set_margin_bottom(10)
        list_box.set_margin_start(10)
        list_box.set_margin_end(10)
        scroll.set_child(list_box)

        self.rows = []
        for i, mon in enumerate(self.monitors):
            geom = mon.get_geometry()
            row = MonitorRow(i, geom, saved.get(str(i), {}), self.on_monitor_changed, self)
            list_box.append(row)
            self.rows.append(row)

        # === BOTONES DE ACCIÓN ===
        btn_box = Gtk.Box(spacing=8, halign=Gtk.Align.CENTER)
        btn_box.set_margin_top(10)
        main.append(btn_box)

        preview_btn = Gtk.Button(label=i18n.t('app.buttons.update'))
        preview_btn.connect('clicked', self.update_preview)
        preview_btn.add_css_class('suggested-action')
        btn_box.append(preview_btn)

        apply_btn = Gtk.Button(label=i18n.t('app.buttons.apply'))
        apply_btn.connect('clicked', self.on_apply)
        apply_btn.add_css_class('suggested-action')
        btn_box.append(apply_btn)

        # === SIDEBAR DE IMÁGENES (al final, a la derecha) ===
        self.sidebar = ImageSidebar(self.last_directory, self.on_image_selected)
        main_container.append(self.sidebar)

        # Evitar que el sidebar compita por espacio: que no expanda horizontalmente
        self.sidebar.set_hexpand(False)
        self.sidebar.set_vexpand(True)
        main.set_hexpand(True)

        # Ajustar ancho del sidebar entre 20% y 30% mediante polling ligero.
        # GTK4 no tiene la señal 'size-allocate' en ApplicationWindow, por eso
        # usamos un pequeño timer que solo actualiza cuando cambia el ancho.
        self._last_window_width = 0

        def _poll_window_size():
            try:
                # GTK4: usar get_allocated_width en lugar de get_size
                total_w = self.window.get_allocated_width()
                if total_w != self._last_window_width and total_w > 0:
                    self._last_window_width = total_w
                    min_px = 180
                    target = int(total_w * 0.25)  # objetivo ~25%
                    target = max(min_px, target)
                    max_allowed = int(total_w * 0.30)
                    if target > max_allowed:
                        target = max_allowed
                    try:
                        self.sidebar.set_size_request(target, -1)
                    except Exception:
                        pass
            except Exception as e:
                logger.error("Error en poll_window_size:", e)
            return True

        GLib.timeout_add(150, _poll_window_size)

        self.update_preview()

    def on_image_selected(self, image_path, button):
        """Callback cuando se selecciona una imagen del sidebar."""
        logger.debug(f"Imagen seleccionada: {image_path}")
        
        # Crear menú popover
        menu = Gio.Menu()
        
        # Agregar opción para cada monitor
        for i in range(len(self.monitors)):
            menu.append(i18n.t('monitor.title', number=i+1), f"app.set-monitor-{i}")
        
        # Crear popover con el menú
        popover = Gtk.PopoverMenu()
        popover.set_menu_model(menu)
        popover.set_parent(button)
        popover.set_has_arrow(True)
        
        # Limpiar acciones previas si existen
        for i in range(len(self.monitors)):
            action_name = f"set-monitor-{i}"
            if self.lookup_action(action_name):
                self.remove_action(action_name)
        
        # Crear acciones para cada monitor
        for i in range(len(self.monitors)):
            action = Gio.SimpleAction.new(f"set-monitor-{i}", None)
            action.connect("activate", lambda a, p, idx=i, path=image_path, pv=popover: self.assign_image_to_monitor(idx, path, pv))
            self.add_action(action)
        
        # Mostrar el popover
        popover.popup()

    def assign_image_to_monitor(self, monitor_idx, image_path, popover):
        """Asigna una imagen a un monitor específico."""
        logger.debug(f"Asignando imagen {image_path} al monitor {monitor_idx}")
        self.rows[monitor_idx].set_image_file(image_path)
        self.on_monitor_changed()
        # Cerrar el popover después de seleccionar
        popover.popdown()

    def gather_states(self):
        return {str(r.index): r.get_state() for r in self.rows}

    def update_preview(self, *_):
        try:
            logger.debug("=== Actualizando preview ===")
            states = self.gather_states()
            logger.debug(f"Estados: {states}")
            logger.debug(f"Monitores: {len(self.monitors)}")
            
            preview = compose_image(self.monitors, states, scale_preview=1000)
            logger.debug(f"Preview generado: {preview.size}")
            
            self.preview.clear()
            
            pix = pil_to_pixbuf(preview.convert('RGB'))
            logger.debug(f"Pixbuf creado: {pix.get_width()}x{pix.get_height()}")
            
            self.preview.set_from_pixbuf(pix)
            logger.debug("Preview actualizado correctamente")
        except Exception as e:
            logger.error('Error en preview:', e)
            import traceback
            traceback.print_exc()

    def on_monitor_changed(self, *_):
        self.update_preview()
        # Guardar configuración automáticamente cuando cambia algo
        save_config({
            'monitors': self.gather_states(),
            'last_directory': self.last_directory
        })

    def on_apply(self, *_):
        try:
            # Importar el módulo de wallpaper
            from .wallpaper_setter import apply_wallpaper, get_wallpaper_path
            
            # Guardar configuración automáticamente antes de aplicar
            save_config({
                'monitors': self.gather_states(),
                'last_directory': self.last_directory
            })
            
            # Generar imagen combinada
            combined = compose_image(self.monitors, self.gather_states())
            
            # Obtener la ruta apropiada según el entorno
            output_path = get_wallpaper_path()
            
            # Asegurar que el directorio existe
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Guardar imagen
            combined.convert('RGB').save(output_path, quality=95)
            logger.debug(f"Wallpaper guardado en: {output_path}")
            
            # Aplicar wallpaper usando el método apropiado
            success, message, script_path = apply_wallpaper(output_path)
            
            if success:
                logger.debug(f"✅ {message}")
                dialog = Gtk.AlertDialog(message=i18n.t('app.dialogs.applied'))
                dialog.show(self.window)
            else:
                logger.debug(f"⚠️ {message}")
                if script_path:
                    full_message = (
                        f"✅ Wallpaper generado en:\n{output_path}\n\n"
                        f"⚠️ {message}"
                    )
                else:
                    full_message = f"⚠️ {message}"
                
                dialog = Gtk.AlertDialog(message=full_message)
                dialog.show(self.window)
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Error al aplicar wallpaper: {error_msg}")
            import traceback
            traceback.print_exc()
            
            dialog = Gtk.AlertDialog(
                message=i18n.t('app.dialogs.error', error=error_msg)
            )
            dialog.show(self.window)

    def run(self, argv=None):
        return super().run(argv)