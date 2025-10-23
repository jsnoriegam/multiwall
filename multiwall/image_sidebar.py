import os
import i18n
from pathlib import Path
from PIL import Image
import io
from gi import require_version
require_version('Gtk', '4.0')
from gi.repository import Gtk, GdkPixbuf, GLib, Gio
from .logger import get_logger

logger = get_logger(__name__)

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.webp', '.gif', '.avif'}
THUMBNAIL_SIZE = 100


class ImageSidebar(Gtk.Box):
    """Sidebar displaying image thumbnails in a grid."""
    
    def __init__(self, pictures_dir, on_image_selected_cb):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.pictures_dir = pictures_dir
        self.on_image_selected_cb = on_image_selected_cb
        self.current_images = []
        
        logger.info(f"Initializing ImageSidebar with directory: {pictures_dir}")
        
        # Sidebar styling - compact
        self.set_size_request(220, -1)
        self.add_css_class('sidebar')
        
        # Header - compact
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        header.set_margin_top(8)
        header.set_margin_bottom(8)
        header.set_margin_start(8)
        header.set_margin_end(8)
        self.append(header)
        
        title = Gtk.Label()
        title.set_markup(f"<b>{i18n.t('sidebar.title')}</b>")
        title.set_hexpand(True)
        title.set_xalign(0)
        header.append(title)
        
        # Change folder button
        change_btn = Gtk.Button()
        change_btn.set_icon_name('folder-open-symbolic')
        change_btn.set_tooltip_text(i18n.t('sidebar.change_folder'))
        change_btn.connect('clicked', self.on_change_folder)
        change_btn.add_css_class('flat')
        header.append(change_btn)
        
        # Refresh button
        refresh_btn = Gtk.Button()
        refresh_btn.set_icon_name('view-refresh-symbolic')
        refresh_btn.set_tooltip_text(i18n.t('sidebar.refresh'))
        refresh_btn.connect('clicked', lambda _: self.load_images())
        refresh_btn.add_css_class('flat')
        header.append(refresh_btn)
        
        # Separator
        separator = Gtk.Separator()
        self.append(separator)
        
        # Current folder label - compact
        self.folder_label = Gtk.Label()
        self.folder_label.set_ellipsize(3)  # ELLIPSIZE_END
        self.folder_label.set_xalign(0)
        self.folder_label.set_margin_start(8)
        self.folder_label.set_margin_end(8)
        self.folder_label.set_margin_top(4)
        self.folder_label.set_margin_bottom(6)
        self.folder_label.add_css_class('dim-label')
        self.folder_label.add_css_class('caption')
        self.append(self.folder_label)
        
        # ScrolledWindow for grid
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_hexpand(True)
        self.append(scroll)
        
        # FlowBox for thumbnail grid - compact
        self.flowbox = Gtk.FlowBox()
        self.flowbox.set_valign(Gtk.Align.START)
        self.flowbox.set_max_children_per_line(2)
        self.flowbox.set_min_children_per_line(2)
        self.flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flowbox.set_homogeneous(True)
        self.flowbox.set_column_spacing(6)
        self.flowbox.set_row_spacing(6)
        self.flowbox.set_margin_start(8)
        self.flowbox.set_margin_end(8)
        self.flowbox.set_margin_top(4)
        self.flowbox.set_margin_bottom(8)
        scroll.set_child(self.flowbox)
        
        # Load initial images
        self.load_images()
    
    def update_folder_label(self):
        """Update label with current folder name."""
        folder_name = Path(self.pictures_dir).name
        self.folder_label.set_text(f"📁 {folder_name}")
        self.folder_label.set_tooltip_text(self.pictures_dir)
        logger.debug(f"Folder label updated: {folder_name}")
    
    def load_images(self):
        """Load images from current directory."""
        logger.info(f"Loading images from: {self.pictures_dir}")
        
        # Clear flowbox
        while True:
            child = self.flowbox.get_first_child()
            if child is None:
                break
            self.flowbox.remove(child)
        
        self.current_images = []
        
        # Update folder label
        self.update_folder_label()
        
        # Verify directory exists
        if not os.path.exists(self.pictures_dir):
            logger.warning(f"Directory does not exist: {self.pictures_dir}")
            return
        
        # Search for image files
        try:
            for entry in sorted(Path(self.pictures_dir).iterdir()):
                if entry.is_file() and entry.suffix.lower() in IMAGE_EXTENSIONS:
                    self.current_images.append(str(entry))
        except PermissionError as e:
            logger.error(f"Permission denied listing images: {e}")
            return
        except Exception as e:
            logger.error(f"Error listing images: {e}")
            return
        
        logger.info(f"Found {len(self.current_images)} images in {self.pictures_dir}")
        
        # Create thumbnails
        for image_path in self.current_images:
            self.create_thumbnail(image_path)
    
    def create_thumbnail(self, image_path):
        """
        Create a thumbnail for an image.
        
        Args:
            image_path: Path to image file
        """
        logger.debug(f"Creating thumbnail for: {os.path.basename(image_path)}")
        
        # Create container for thumbnail
        button = Gtk.Button()
        button.add_css_class('flat')
        button.set_tooltip_text(os.path.basename(image_path))
        
        # Box for image and name - compact
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        
        # Load and scale image
        # Try GdkPixbuf first, fallback to Pillow for unsupported formats
        pixbuf = None
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                image_path,
                THUMBNAIL_SIZE,
                THUMBNAIL_SIZE,
                True  # preserve_aspect_ratio
            )
            logger.debug(f"Thumbnail loaded with GdkPixbuf: {os.path.basename(image_path)}")
        except Exception as e:
            logger.debug(f"GdkPixbuf failed for {os.path.basename(image_path)}, trying Pillow...")
            # Fallback to Pillow for formats not supported by GdkPixbuf (e.g., AVIF)
            try:
                # Load with Pillow
                pil_img = Image.open(image_path)
                pil_img.thumbnail((THUMBNAIL_SIZE, THUMBNAIL_SIZE), Image.Resampling.LANCZOS)
                
                # Convert to RGB if necessary
                if pil_img.mode != 'RGB':
                    pil_img = pil_img.convert('RGB')
                
                # Convert PIL to PNG bytes
                img_bytes = io.BytesIO()
                pil_img.save(img_bytes, format='PNG')
                img_data = img_bytes.getvalue()
                
                # Create GdkPixbuf from bytes using GLib.Bytes
                bytes_obj = GLib.Bytes.new(img_data)
                stream = Gio.MemoryInputStream.new_from_bytes(bytes_obj)
                pixbuf = GdkPixbuf.Pixbuf.new_from_stream(stream, None)
                
                logger.info(f"Thumbnail loaded with Pillow: {os.path.basename(image_path)}")
            except Exception as e2:
                logger.error(f"Failed to load thumbnail for {os.path.basename(image_path)}: {e2}")
                return
        
        if pixbuf is None:
            logger.warning(f"Could not load thumbnail: {os.path.basename(image_path)}")
            return
        
        image = Gtk.Image.new_from_pixbuf(pixbuf)
        image.set_size_request(THUMBNAIL_SIZE, THUMBNAIL_SIZE)
        box.append(image)
        
        # Filename (truncated) - smaller text
        label = Gtk.Label()
        filename = os.path.basename(image_path)
        if len(filename) > 15:
            filename = filename[:12] + "..."
        label.set_text(filename)
        label.add_css_class('caption')
        label.set_ellipsize(3)  # ELLIPSIZE_END
        box.append(label)
        
        button.set_child(box)
        
        # Connect click - pass button as additional parameter
        button.connect('clicked', self.on_thumbnail_clicked, image_path)
        
        # Add to flowbox
        self.flowbox.append(button)
    
    def on_thumbnail_clicked(self, button, image_path):
        """Callback when thumbnail is clicked."""
        logger.info(f"Thumbnail clicked: {os.path.basename(image_path)}")
        # Pass both image path and button
        self.on_image_selected_cb(image_path, button)
    
    def on_change_folder(self, button):
        """Show custom dialog for changing image folder."""
        logger.info("Opening folder selection dialog")
        
        # Create dialog window
        dialog = Gtk.Window()
        dialog.set_title(i18n.t('sidebar.select_folder'))
        dialog.set_modal(True)
        dialog.set_transient_for(self.get_root())
        dialog.set_default_size(500, 400)
        
        # Main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_top(10)
        main_box.set_margin_bottom(10)
        main_box.set_margin_start(10)
        main_box.set_margin_end(10)
        dialog.set_child(main_box)
        
        # Instruction label
        label = Gtk.Label(label=i18n.t('sidebar.select_folder_instruction'))
        label.set_xalign(0)
        main_box.append(label)
        
        # Scrolled area for folder tree
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_hexpand(True)
        main_box.append(scroll)
        
        # TreeView with model
        store = Gtk.TreeStore(str, str)  # (display name, full path)
        tree = Gtk.TreeView(model=store)
        tree.set_headers_visible(False)
        scroll.set_child(tree)
        
        # Text column
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Folder", renderer, text=0)
        tree.append_column(column)
        
        # Variable to store selected folder
        selected_folder = [self.pictures_dir]  # Mutable list for closure
        
        def on_tree_selection_changed(selection):
            model, treeiter = selection.get_selected()
            if treeiter:
                selected_folder[0] = model[treeiter][1]
                logger.debug(f"Folder selected in tree: {selected_folder[0]}")
        
        selection = tree.get_selection()
        selection.connect("changed", on_tree_selection_changed)
        
        # Populate tree with common folders and subdirectories
        def add_folder_to_tree(parent_iter, folder_path, max_depth=2, current_depth=0):
            try:
                if current_depth >= max_depth:
                    return
                    
                for entry in sorted(Path(folder_path).iterdir()):
                    if entry.is_dir() and not entry.name.startswith('.'):
                        folder_iter = store.append(parent_iter, [f"📁 {entry.name}", str(entry)])
                        # Add subdirectories recursively
                        if current_depth < max_depth - 1:
                            add_folder_to_tree(folder_iter, entry, max_depth, current_depth + 1)
            except PermissionError:
                logger.debug(f"Permission denied accessing: {folder_path}")
            except Exception as e:
                logger.debug(f"Error listing folder {folder_path}: {e}")
        
        # Add main folders
        home = Path.home()
        
        # Home
        home_iter = store.append(None, [f"🏠 {home.name}", str(home)])
        add_folder_to_tree(home_iter, home, max_depth=3)
        
        # Common folders
        common_folders = ['Documents', 'Downloads', 'Pictures', 'Music', 'Videos', 
                         'Documentos', 'Descargas', 'Imágenes', 'Música', 'Vídeos']
        
        for folder_name in common_folders:
            folder_path = home / folder_name
            if folder_path.exists() and folder_path.is_dir():
                folder_iter = store.append(None, [f"📁 {folder_name}", str(folder_path)])
                add_folder_to_tree(folder_iter, folder_path, max_depth=2)
        
        # Expand home by default
        tree.expand_row(Gtk.TreePath.new_first(), False)
        
        # Select current folder if in tree
        def select_current_folder():
            def search_and_select(model, path, iter, search_path):
                if model[iter][1] == search_path:
                    tree.get_selection().select_iter(iter)
                    tree.scroll_to_cell(path, None, True, 0.5, 0.5)
                    return True
                return False
            
            store.foreach(search_and_select, self.pictures_dir)
        
        GLib.idle_add(select_current_folder)
        
        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_halign(Gtk.Align.END)
        main_box.append(button_box)
        
        cancel_btn = Gtk.Button(label=i18n.t('app.dialogs.cancel'))
        cancel_btn.connect('clicked', lambda w: dialog.close())
        button_box.append(cancel_btn)
        
        select_btn = Gtk.Button(label=i18n.t('sidebar.select'))
        select_btn.add_css_class('suggested-action')
        select_btn.connect('clicked', lambda w: self.on_folder_dialog_select(dialog, selected_folder[0]))
        button_box.append(select_btn)
        
        logger.debug("Folder selection dialog presented")
        dialog.present()
    
    def on_folder_dialog_select(self, dialog, folder_path):
        """Callback when folder selection is confirmed."""
        if folder_path and os.path.exists(folder_path):
            logger.info(f"New folder selected: {folder_path}")
            self.pictures_dir = folder_path
            self.load_images()
        else:
            logger.warning(f"Invalid folder selected: {folder_path}")
        dialog.close()