import i18n
import os
import sys
from pathlib import Path
from .logger import get_logger, setup_logger
import logging

# Setup logger with DEBUG level if --debug flag is passed
if '--debug' in sys.argv:
    setup_logger('multiwall', logging.DEBUG)
    sys.argv.remove('--debug')
else:
    setup_logger('multiwall', logging.INFO)

logger = get_logger(__name__)

# Ensure UTF-8 for emojis
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# i18n configuration
translations_path = Path(__file__).parent / 'translations'
i18n.load_path.clear()
i18n.load_path.append(str(translations_path))
i18n.set('filename_format', '{locale}.{format}')
i18n.set('file_format', 'json')
i18n.set('fallback', 'en')
i18n.set('error_on_missing_translation', False)
i18n.set('error_on_missing_placeholder', False)

# Detect system language
def detect_system_language():
    """Detect system language from environment variables."""
    lang = os.getenv('LANGUAGE')
    if lang and lang != 'C':
        detected = lang.split(':')[0][:2]
        logger.debug(f"Language detected from LANGUAGE env: {detected}")
        return detected
    
    lang = os.getenv('LANG')
    if lang and lang != 'C':
        detected = lang.split('_')[0]
        logger.debug(f"Language detected from LANG env: {detected}")
        return detected
    
    try:
        import locale
        system_lang, _ = locale.getdefaultlocale()
        if system_lang and system_lang != 'C':
            detected = system_lang[:2]
            logger.debug(f"Language detected from locale: {detected}")
            return detected
    except Exception as e:
        logger.error(f"Error detecting locale: {e}")
    
    logger.info("Using default language: en")
    return 'en'

detected_lang = detect_system_language()
i18n.set('locale', detected_lang)

logger.debug(f"Translations path: {translations_path}")
logger.debug(f"Translations path exists: {translations_path.exists()}")
if translations_path.exists():
    logger.debug(f"Translation files: {list(translations_path.glob('*.json'))}")

import subprocess
from gi import require_version
require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf, Gio
from .config import load_config, save_config
from .composer import compose_image
from .monitor_row import MonitorRow
from .utils import pil_to_pixbuf
from .image_sidebar import ImageSidebar


def is_running_in_docker():
    """Check if running inside Docker container."""
    return os.path.exists('/.dockerenv') or os.path.exists('/run/.containerenv')


# Use shared directory with host if in Docker
if is_running_in_docker():
    TMP_OUTPUT = str(Path.home() / ".config" / "multiwall" / "current_wallpaper.jpg")
else:
    TMP_OUTPUT = "/tmp/multiwall_combined.jpg"


def get_default_pictures_directory():
    """Get default system pictures directory."""
    try:
        # Try to get from XDG user dirs
        result = subprocess.run(
            ['xdg-user-dir', 'PICTURES'],
            capture_output=True,
            text=True,
            check=True
        )
        pictures_dir = result.stdout.strip()
        if pictures_dir and os.path.exists(pictures_dir):
            logger.debug(f"System pictures directory: {pictures_dir}")
            return pictures_dir
    except Exception as e:
        logger.warning(f"Could not get xdg-user-dir: {e}")
    
    # Fallback: try common locations based on language
    home = Path.home()
    common_names = ['Pictures', 'Imágenes', 'Images', 'Bilder', 'Imagenes']
    
    for name in common_names:
        candidate = home / name
        if candidate.exists():
            logger.debug(f"Pictures directory found: {candidate}")
            return str(candidate)
    
    # Last fallback: HOME
    logger.debug(f"Using HOME directory as fallback: {home}")
    return str(home)


class MultiWallApp(Gtk.Application):
    def __init__(self, app=None):
        if not Gdk.Display.get_default():
            raise RuntimeError(
                "No display detected. Make sure to:\n"
                "1. Have DISPLAY configured (e.g., export DISPLAY=:0)\n"
                "2. Run in a GUI environment (not in a container without X11)\n"
                "3. Have permissions to access the display"
            )
        
        super().__init__(application_id='com.multiwall.app')
        logger.info("Initializing MultiWall application")

        css_provider = Gtk.CssProvider()
        css_provider.load_from_string("""
        .rounded-box {
            border-radius: 20px;
            background-color: #f0f0f0;
            background-clip: padding-box;
            -gtk-clip-to-allocation: true;
        }
        button.warning-button {
            border: solid 1px #FFA500;
            color: #FFA500;
        }
        button.warning-button:hover {
            border: solid 1px #FF8C00;
        }
        button.warning-button:active {
            border: solid 1px #FF7F50;
        }
        """)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        self.settings = load_config()
        # Use last saved directory, or detect system default
        self.last_directory = self.settings.get('last_directory', get_default_pictures_directory())
        logger.debug(f"Initial pictures directory: {self.last_directory}")
        
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        logger.info("Activating application window")
        self.window = Gtk.ApplicationWindow(
            application=app,
            title=i18n.t('app.title'),
            default_width=1200,
            default_height=700
        )
        self.build_ui()
        self.window.present()
        logger.info("Application window presented")

    def show_about_dialog(self, button):
        """Show About dialog."""
        logger.debug("Opening About dialog")
        
        about = Gtk.AboutDialog()
        about.set_transient_for(self.window)
        about.set_modal(True)
        
        # Basic info
        about.set_program_name("MultiWall")
        about.set_version("0.3.5")
        about.set_comments(i18n.t('app.about.description'))
        about.set_copyright("© 2025 Juan Salvador Noriega Madrid")
        about.set_website("https://github.com/jsnoriegam/multiwall")
        about.set_website_label(i18n.t('app.about.website'))
        about.set_license_type(Gtk.License.MIT_X11)
        
        # Authors
        about.set_authors(["Juan Salvador Noriega Madrid"])
        
        # Logo (if exists)
        try:
            icon_path = Path(__file__).parent / "icon.png"
            if icon_path.exists():
                texture = Gdk.Texture.new_from_filename(str(icon_path))

                about.set_logo(texture)
            else:
                logger.debug(f"Icon not found at {icon_path}")
        except Exception as e:
            logger.warning(f"Could not load icon for About dialog: {e}")
        
        about.present()

    def build_ui(self):
        logger.debug("Building UI components")
        
        # Main container with header bar
        header = Gtk.HeaderBar()
        header.set_show_title_buttons(True)
        self.window.set_titlebar(header)
        
        # About button in header
        about_button = Gtk.Button()
        about_button.set_icon_name("help-about-symbolic")
        about_button.set_tooltip_text(i18n.t('app.about.title'))
        about_button.connect("clicked", self.show_about_dialog)
        header.pack_end(about_button)
        
        # Main horizontal container: content + sidebar
        main_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.window.set_child(main_container)

        # === MAIN AREA ===
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

        header_label = Gtk.Label(label=f"<b>{i18n.t('app.header')}</b>")
        header_label.set_use_markup(True)
        header_label.set_margin_bottom(10)
        main.append(header_label)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        main.append(content)

        # === PREVIEW AREA ===
        preview_frame = Gtk.Frame()
        preview_frame.set_label(i18n.t('app.preview_label'))
        preview_frame.set_vexpand(True)
        preview_frame.set_hexpand(True)
        content.append(preview_frame)

        scrolled_window = Gtk.ScrolledWindow()
        preview_frame.set_child(scrolled_window)

        preview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        preview_box.add_css_class('rounded-box')
        preview_box.set_margin_top(20)
        preview_box.set_margin_bottom(20)
        preview_box.set_margin_start(20)
        preview_box.set_margin_end(20)

        scrolled_window.set_child(preview_box)       

        self.preview = Gtk.Picture()

        preview_box.append(self.preview)

        # === CONTROLS AREA ===
        controls_frame = Gtk.Frame()
        controls_frame.set_label(i18n.t('app.controls_label'))
        content.append(controls_frame)

        display = Gdk.Display.get_default()
        monitor_list = display.get_monitors()
        self.monitors = [monitor_list.get_item(i) for i in range(monitor_list.get_n_items())]
        logger.info(f"Detected {len(self.monitors)} monitors")
        
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
            logger.debug(f"Monitor {i}: {geom.width}x{geom.height} @ ({geom.x}, {geom.y})")
            row = MonitorRow(i, geom, saved.get(str(i), {}), self.on_monitor_changed, self)
            list_box.append(row)
            self.rows.append(row)

        # === ACTION BUTTONS ===
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

        # === IMAGE SIDEBAR (at the end, on the right) ===
        logger.debug("Creating image sidebar")
        self.sidebar = ImageSidebar(self.last_directory, self.on_image_selected)
        main_container.append(self.sidebar)

        # Prevent sidebar from competing for space
        self.sidebar.set_hexpand(False)
        self.sidebar.set_vexpand(True)
        main.set_hexpand(True)

        # Adjust sidebar width between 20% and 30% via light polling
        self._last_window_width = 0

        def _poll_window_size():
            try:
                total_w = self.window.get_allocated_width()
                if total_w != self._last_window_width and total_w > 0:
                    self._last_window_width = total_w
                    min_px = 180
                    target = int(total_w * 0.25)  # ~25%
                    target = max(min_px, target)
                    max_allowed = int(total_w * 0.30)
                    if target > max_allowed:
                        target = max_allowed
                    try:
                        self.sidebar.set_size_request(target, -1)
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Error in window size polling: {e}")
            return True

        GLib.timeout_add(150, _poll_window_size)

        logger.debug("UI build complete, updating initial preview")
        self.update_preview()

    def on_image_selected(self, image_path, button):
        """Callback when an image is selected from sidebar."""
        logger.debug(f"Image selected from sidebar: {image_path}")
        
        # Create popover menu
        menu = Gio.Menu()
        
        # Add option for each monitor
        for i in range(len(self.monitors)):
            menu.append(i18n.t('monitor.title', number=i+1), f"app.set-monitor-{i}")
        
        # Create popover with menu
        popover = Gtk.PopoverMenu()
        popover.set_menu_model(menu)
        popover.set_parent(button)
        popover.set_has_arrow(True)
        
        # Clean previous actions if they exist
        for i in range(len(self.monitors)):
            action_name = f"set-monitor-{i}"
            if self.lookup_action(action_name):
                self.remove_action(action_name)
        
        # Create actions for each monitor
        for i in range(len(self.monitors)):
            action = Gio.SimpleAction.new(f"set-monitor-{i}", None)
            action.connect("activate", lambda a, p, idx=i, path=image_path, pv=popover: self.assign_image_to_monitor(idx, path, pv))
            self.add_action(action)
        
        # Show popover
        popover.popup()

    def assign_image_to_monitor(self, monitor_idx, image_path, popover):
        """Assign an image to a specific monitor."""
        logger.info(f"Assigning image to monitor {monitor_idx}: {os.path.basename(image_path)}")
        self.rows[monitor_idx].set_image_file(image_path)
        self.on_monitor_changed()
        # Close popover after selection
        popover.popdown()

    def gather_states(self):
        """Gather current state of all monitors."""
        states = {str(r.index): r.get_state() for r in self.rows}
        logger.debug(f"Gathered states for {len(states)} monitors")
        return states

    def update_preview(self, *_):
        """Update the wallpaper preview."""
        try:
            logger.debug("=== Updating preview ===")
            states = self.gather_states()
            
            preview = compose_image(self.monitors, states, scale_preview=1200)
            logger.debug(f"Preview generated: {preview.size}")
            
            self.preview.set_pixbuf(None)  # Clear previous
            
            pix = pil_to_pixbuf(preview.convert('RGB'))
            logger.debug(f"Pixbuf created: {pix.get_width()}x{pix.get_height()}")
            
            self.preview.set_pixbuf(pix)
            logger.debug("Preview updated successfully")
        except Exception as e:
            logger.error(f"Error updating preview: {e}", exc_info=True)

    def on_monitor_changed(self, *_):
        """Callback when monitor configuration changes."""
        self.update_preview()
        # Auto-save configuration on change
        save_config({
            'monitors': self.gather_states(),
            'last_directory': self.last_directory
        })

    def on_apply(self, *_):
        """Apply the wallpaper configuration."""
        try:
            logger.info("=== Applying wallpaper ===")
            
            # Import wallpaper module
            from .wallpaper_setter import apply_wallpaper, get_wallpaper_path
            
            # Auto-save configuration before applying
            save_config({
                'monitors': self.gather_states(),
                'last_directory': self.last_directory
            })
            
            # Generate combined image
            combined = compose_image(self.monitors, self.gather_states())
            logger.debug(f"Combined image generated: {combined.size}")
            
            # Get appropriate path based on environment
            output_path = get_wallpaper_path()
            
            # Ensure directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Save image
            combined.convert('RGB').save(output_path, quality=95)
            logger.info(f"Wallpaper saved to: {output_path}")
            
            # Apply wallpaper using appropriate method
            success, message, script_path = apply_wallpaper(output_path)
            
            if success:
                logger.info(f"Wallpaper applied successfully")
                dialog = Gtk.AlertDialog(message=i18n.t('app.dialogs.applied'))
                dialog.show(self.window)
            else:
                logger.warning(f"Wallpaper could not be applied automatically: {message}")
                if script_path:
                    full_message = (
                        f"✅ Wallpaper generated at:\n{output_path}\n\n"
                        f"⚠️ {message}"
                    )
                else:
                    full_message = f"⚠️ {message}"
                
                dialog = Gtk.AlertDialog(message=full_message)
                dialog.show(self.window)
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error applying wallpaper: {error_msg}", exc_info=True)
            
            dialog = Gtk.AlertDialog(
                message=i18n.t('app.dialogs.error', error=error_msg)
            )
            dialog.show(self.window)

    def run(self, argv=None):
        logger.info("Starting application main loop")
        return super().run(argv)