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
    """Widget for configuring a single monitor's wallpaper."""
    
    def __init__(self, index, geom, initial, on_change_cb, app):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.add_css_class('card')
        self.set_margin_start(5)
        self.set_margin_end(5)
        self.set_margin_top(5)
        self.set_margin_bottom(5)

        self.index = index
        self.on_change_cb = on_change_cb
        self.app = app  # Reference to main application
        self.selected_file = initial.get('file')
        
        logger.debug(f"Creating MonitorRow {index}: {geom.width}x{geom.height}")
        if self.selected_file:
            logger.debug(f"Monitor {index} initial image: {self.selected_file}")

        # Header with monitor info
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

        # Controls in horizontal row
        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.append(controls)

        # === File button ===
        file_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        file_box.set_hexpand(True)
        controls.append(file_box)

        file_label = Gtk.Label(label=i18n.t('monitor.image_label'))
        file_label.set_xalign(0)
        file_label.add_css_class('caption')
        file_box.append(file_label)

        # Horizontal box for file button and clear button
        file_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        file_box.append(file_button_box)

        self.file_button = Gtk.Button()
        self.file_button.set_hexpand(True)
        if self.selected_file:
            self.file_button.set_label(os.path.basename(self.selected_file))
        else:
            self.file_button.set_label(i18n.t('monitor.select_image'))
        self.file_button.connect('clicked', self.on_choose_file)
        file_button_box.append(self.file_button)

        # Clear button
        clear_button = Gtk.Button()
        clear_button.set_icon_name('edit-clear-symbolic')
        clear_button.set_tooltip_text(i18n.t('monitor.clear_image'))
        clear_button.connect('clicked', self.on_clear_image)
        # clear_button.add_css_class('destructive-action')
        clear_button.add_css_class('warning-button')
        file_button_box.append(clear_button)

        # === Mode ===
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

        # === Background color ===
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
        """Callback when wallpaper display mode changes."""
        mode = self.mode_map[combo.get_selected()]
        logger.info(f"Monitor {self.index}: Display mode changed to '{mode}'")
        self.on_change_cb(self.index)

    def on_color_changed(self, color_button):
        """Callback when background color changes."""
        rgba = color_button.get_rgba()
        color_hex = f'#{int(rgba.red*255):02x}{int(rgba.green*255):02x}{int(rgba.blue*255):02x}'
        logger.info(f"Monitor {self.index}: Background color changed to {color_hex}")
        self.on_change_cb(self.index)

    def on_clear_image(self, button):
        """Clear the selected image."""
        logger.info(f"Monitor {self.index}: Clearing image")
        self.selected_file = None
        self.file_button.set_label(i18n.t('monitor.select_image'))
        self.on_change_cb(self.index)

    def on_choose_file(self, button):
        """Open file chooser dialog for selecting an image."""
        logger.debug(f"Monitor {self.index}: Opening file chooser")
        
        dialog = Gtk.FileDialog()
        dialog.set_title(i18n.t('monitor.title', number=self.index+1))
        
        # Set initial directory to last used
        if os.path.exists(self.app.last_directory):
            initial_folder = Gio.File.new_for_path(self.app.last_directory)
            dialog.set_initial_folder(initial_folder)
            logger.debug(f"Initial folder: {self.app.last_directory}")
        
        # Create filter for images
        filter_img = Gtk.FileFilter()
        filter_img.set_name("Images")
        for pattern in IMAGE_FILTERS:
            filter_img.add_pattern(pattern)
        
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_img)
        dialog.set_filters(filters)
        dialog.set_default_filter(filter_img)
        
        # Open dialog
        dialog.open(self.get_root(), None, self.on_file_selected)

    def on_file_selected(self, dialog, result):
        """Callback when file is selected from dialog."""
        try:
            file = dialog.open_finish(result)
            if file:
                self.selected_file = file.get_path()
                
                # Update last used directory
                self.app.last_directory = str(Path(self.selected_file).parent)
                logger.info(f"Monitor {self.index}: Image selected - {os.path.basename(self.selected_file)}")
                logger.debug(f"Last directory updated: {self.app.last_directory}")
                
                self.file_button.set_label(os.path.basename(self.selected_file))
                self.on_change_cb(self.index)
        except Exception as e:
            # User cancelled or error occurred
            logger.debug(f"Monitor {self.index}: File selection cancelled or failed")

    def set_image_file(self, file_path):
        """
        Set image for this monitor (used from sidebar).
        
        Args:
            file_path: Path to image file
        """
        if os.path.exists(file_path):
            self.selected_file = file_path
            self.file_button.set_label(os.path.basename(file_path))
            logger.info(f"Monitor {self.index}: Image set from sidebar - {os.path.basename(file_path)}")
            
            # Update last used directory
            self.app.last_directory = str(Path(file_path).parent)
            logger.debug(f"Last directory updated: {self.app.last_directory}")
        else:
            logger.warning(f"Monitor {self.index}: Attempted to set non-existent file: {file_path}")

    def get_state(self):
        """
        Get current state of monitor configuration.
        
        Returns:
            dict: Configuration state with file, mode, and background
        """
        mode = self.mode_map[self.combo.get_selected()]
        rgba = self.color.get_rgba()
        color_hex = f'#{int(rgba.red*255):02x}{int(rgba.green*255):02x}{int(rgba.blue*255):02x}'
        state = {
            'file': self.selected_file,
            'mode': mode,
            'background': color_hex
        }
        logger.debug(f"Monitor {self.index} state: file={os.path.basename(self.selected_file) if self.selected_file else 'None'}, mode={mode}, bg={color_hex}")
        return state