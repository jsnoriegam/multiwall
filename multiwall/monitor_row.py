import i18n
import os
from pathlib import Path
from gi import require_version
require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, Gio

from .logger import get_logger

logger = get_logger(__name__)

IMAGE_FILTERS = ["*.png", "*.jpg", "*.jpeg", "*.bmp", "*.webp", "*.avif"]
DEFAULT_OPTIONS = {'background': '#000000'}

class MonitorRow(Gtk.Box):
    def __init__(self, index, geom, initial, on_change_cb, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.add_css_class('card')
        self.set_margin_start(5)
        self.set_margin_end(5)
        self.set_margin_top(5)
        self.set_margin_bottom(5)

        self.index = index
        self.on_change_cb = on_change_cb
        self.app = app  # Referencia a la aplicación principal
        self.selected_file = initial.get('file')

        # Header con info del monitor
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.append(header)

        monitor_label = Gtk.Label()
        monitor_label.set_markup(f"<b>{i18n.t('monitor.title', number=index+1)}</b>")
        monitor_label.set_xalign(0)
        header.append(monitor_label)

        info_label = Gtk.Label(label=f"{geom.width}×{geom.height} @ ({geom.x}, {geom.y})")
        info_label.set_xalign(0)
        info_label.add_css_class('dim-label')
        header.append(info_label)

        # Controles en fila horizontal
        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.append(controls)

        # === Botón de archivo ===
        file_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        file_box.set_hexpand(True)
        controls.append(file_box)

        file_label = Gtk.Label(label=i18n.t('monitor.image_label'))
        file_label.set_xalign(0)
        file_label.add_css_class('caption')
        file_box.append(file_label)

        self.file_button = Gtk.Button()
        if self.selected_file:
            self.file_button.set_label(os.path.basename(self.selected_file))
        else:
            self.file_button.set_label(i18n.t('monitor.select_image'))
        self.file_button.connect('clicked', self.on_choose_file)
        file_box.append(self.file_button)

        # === Modo ===
        mode_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        controls.append(mode_box)

        mode_label = Gtk.Label(label=i18n.t('monitor.mode_label'))
        mode_label.set_xalign(0)
        mode_label.add_css_class('caption')
        mode_box.append(mode_label)

        self.mode_map = ['fill', 'fit', 'stretch', 'center', 'tile']
        mode_names = [
            i18n.t('monitor.modes.fill'),
            i18n.t('monitor.modes.fit'),
            i18n.t('monitor.modes.stretch'),
            i18n.t('monitor.modes.center'),
            i18n.t('monitor.modes.tile')
        ]
        combo = Gtk.DropDown.new_from_strings(mode_names)
        mode = initial.get('mode', 'fill')
        mode_index = self.mode_map.index(mode) if mode in self.mode_map else 0
        combo.set_selected(mode_index)
        combo.connect('notify::selected', self.on_mode_changed)
        self.combo = combo
        mode_box.append(combo)

        # === Color de fondo ===
        color_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        controls.append(color_box)

        color_label = Gtk.Label(label=i18n.t('monitor.background_label'))
        color_label.set_xalign(0)
        color_label.add_css_class('caption')
        color_box.append(color_label)

        color = Gtk.ColorButton()
        rgba = Gdk.RGBA()
        rgba.parse(initial.get('background', DEFAULT_OPTIONS['background']))
        color.set_rgba(rgba)
        color.connect('color-set', self.on_color_changed)
        self.color = color
        color_box.append(color)

    def on_mode_changed(self, combo, pspec):
        """Callback cuando cambia el modo del wallpaper."""
        mode = self.mode_map[combo.get_selected()]
        logger.debug(f"Monitor {self.index}: Modo cambiado a '{mode}'")
        self.on_change_cb(self.index)

    def on_color_changed(self, color_button):
        """Callback cuando cambia el color de fondo."""
        rgba = color_button.get_rgba()
        logger.debug(f"Monitor {self.index}: Color cambiado")
        self.on_change_cb(self.index)

    def on_choose_file(self, button):
        dialog = Gtk.FileDialog()
        dialog.set_title(i18n.t('monitor.title', number=self.index+1))
        
        # Establecer el directorio inicial al último usado
        if os.path.exists(self.app.last_directory):
            initial_folder = Gio.File.new_for_path(self.app.last_directory)
            dialog.set_initial_folder(initial_folder)
        
        # Crear filtro para imágenes
        filter_img = Gtk.FileFilter()
        filter_img.set_name("Imágenes")
        for pattern in IMAGE_FILTERS:
            filter_img.add_pattern(pattern)
        
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_img)
        dialog.set_filters(filters)
        dialog.set_default_filter(filter_img)
        
        # Abrir diálogo
        dialog.open(self.get_root(), None, self.on_file_selected)

    def on_file_selected(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            if file:
                self.selected_file = file.get_path()
                
                # Actualizar el último directorio usado
                self.app.last_directory = str(Path(self.selected_file).parent)
                logger.debug(f"Último directorio actualizado: {self.app.last_directory}")
                
                self.file_button.set_label(os.path.basename(self.selected_file))
                logger.debug(f"Monitor {self.index}: Imagen seleccionada - {self.selected_file}")
                self.on_change_cb(self.index)
        except Exception as e:
            # Usuario canceló o hubo error
            pass

    def set_image_file(self, file_path):
        """Establece la imagen para este monitor (usado desde el sidebar)."""
        if os.path.exists(file_path):
            self.selected_file = file_path
            self.file_button.set_label(os.path.basename(file_path))
            logger.debug(f"Monitor {self.index}: Imagen establecida desde sidebar - {file_path}")
            
            # Actualizar el último directorio usado
            self.app.last_directory = str(Path(file_path).parent)

    def get_state(self):
        mode = self.mode_map[self.combo.get_selected()]
        rgba = self.color.get_rgba()
        color_hex = f'#{int(rgba.red*255):02x}{int(rgba.green*255):02x}{int(rgba.blue*255):02x}'
        state = {'file': self.selected_file, 'mode': mode, 'background': color_hex}
        logger.debug(f"Monitor {self.index} get_state: {state}")
        return state