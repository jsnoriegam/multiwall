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
    """Sidebar que muestra miniaturas de imágenes en un grid."""
    
    def __init__(self, pictures_dir, on_image_selected_cb):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.pictures_dir = pictures_dir
        self.on_image_selected_cb = on_image_selected_cb
        self.current_images = []
        
        # Estilo del sidebar - más compacto
        self.set_size_request(220, -1)
        self.add_css_class('sidebar')
        
        # Header del sidebar - más compacto
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
        
        # Botón para cambiar carpeta - más pequeño
        change_btn = Gtk.Button()
        change_btn.set_icon_name('folder-open-symbolic')
        change_btn.set_tooltip_text(i18n.t('sidebar.change_folder'))
        change_btn.connect('clicked', self.on_change_folder)
        change_btn.add_css_class('flat')
        header.append(change_btn)
        
        # Botón de refrescar - más pequeño
        refresh_btn = Gtk.Button()
        refresh_btn.set_icon_name('view-refresh-symbolic')
        refresh_btn.set_tooltip_text(i18n.t('sidebar.refresh'))
        refresh_btn.connect('clicked', lambda _: self.load_images())
        refresh_btn.add_css_class('flat')
        header.append(refresh_btn)
        
        # Separador
        separator = Gtk.Separator()
        self.append(separator)
        
        # Etiqueta de la carpeta actual - más compacta
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
        
        # ScrolledWindow para el grid
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_hexpand(True)
        self.append(scroll)
        
        # FlowBox para el grid de miniaturas - más compacto
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
        
        # Cargar imágenes iniciales
        self.load_images()
    
    def update_folder_label(self):
        """Actualiza la etiqueta con la carpeta actual."""
        folder_name = Path(self.pictures_dir).name
        self.folder_label.set_text(f"📁 {folder_name}")
        self.folder_label.set_tooltip_text(self.pictures_dir)
    
    def load_images(self):
        """Carga las imágenes del directorio actual."""
        # Limpiar flowbox
        while True:
            child = self.flowbox.get_first_child()
            if child is None:
                break
            self.flowbox.remove(child)
        
        self.current_images = []
        
        # Actualizar etiqueta de carpeta
        self.update_folder_label()
        
        # Verificar que el directorio existe
        if not os.path.exists(self.pictures_dir):
            logger.warning(f"El directorio {self.pictures_dir} no existe")
            return
        
        # Buscar archivos de imagen
        try:
            for entry in sorted(Path(self.pictures_dir).iterdir()):
                if entry.is_file() and entry.suffix.lower() in IMAGE_EXTENSIONS:
                    self.current_images.append(str(entry))
        except Exception as e:
            logger.error(f"Error listando imágenes: {e}")
            return
        
        logger.info(f"Encontradas {len(self.current_images)} imágenes en {self.pictures_dir}")
        
        # Crear miniaturas
        for image_path in self.current_images:
            self.create_thumbnail(image_path)
    
    def create_thumbnail(self, image_path):
        """Crea una miniatura para una imagen."""
        # Crear contenedor para la miniatura
        button = Gtk.Button()
        button.add_css_class('flat')
        button.set_tooltip_text(os.path.basename(image_path))
        
        # Box para la imagen y nombre - más compacto
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        
        # Cargar y escalar la imagen
        # Para AVIF y otros formatos que GdkPixbuf puede no soportar,
        # intentar primero con GdkPixbuf, y si falla, usar Pillow
        pixbuf = None
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                image_path,
                THUMBNAIL_SIZE,
                THUMBNAIL_SIZE,
                True  # preserve_aspect_ratio
            )
        except Exception as e:
            logger.error(f"GdkPixbuf no pudo cargar {image_path}, intentando con Pillow...")
            # Fallback a Pillow para formatos no soportados por GdkPixbuf
            try:
                # Cargar con Pillow
                pil_img = Image.open(image_path)
                pil_img.thumbnail((THUMBNAIL_SIZE, THUMBNAIL_SIZE), Image.Resampling.LANCZOS)
                
                # Convertir a RGB si es necesario
                if pil_img.mode != 'RGB':
                    pil_img = pil_img.convert('RGB')
                
                # Convertir PIL a bytes PNG
                img_bytes = io.BytesIO()
                pil_img.save(img_bytes, format='PNG')
                img_data = img_bytes.getvalue()
                
                # Crear GdkPixbuf desde bytes usando GLib.Bytes
                bytes_obj = GLib.Bytes.new(img_data)
                stream = Gio.MemoryInputStream.new_from_bytes(bytes_obj)
                pixbuf = GdkPixbuf.Pixbuf.new_from_stream(stream, None)
                
                logger.info(f"✅ Imagen AVIF cargada con Pillow: {os.path.basename(image_path)}")
            except Exception as e2:
                logger.error(f"❌ Error cargando imagen con Pillow {image_path}: {e2}")
                import traceback
                traceback.print_exc()
                return
        
        if pixbuf is None:
            logger.warning(f"⚠️ No se pudo cargar la imagen: {image_path}")
            return
        
        image = Gtk.Image.new_from_pixbuf(pixbuf)
        image.set_size_request(THUMBNAIL_SIZE, THUMBNAIL_SIZE)
        box.append(image)
        
        # Nombre del archivo (truncado) - texto más pequeño
        label = Gtk.Label()
        filename = os.path.basename(image_path)
        if len(filename) > 15:
            filename = filename[:12] + "..."
        label.set_text(filename)
        label.add_css_class('caption')
        label.set_ellipsize(3)  # ELLIPSIZE_END
        box.append(label)
        
        button.set_child(box)
        
        # Conectar click - pasar el botón como parámetro adicional
        button.connect('clicked', self.on_thumbnail_clicked, image_path)
        
        # Agregar al flowbox
        self.flowbox.append(button)
    
    def on_thumbnail_clicked(self, button, image_path):
        """Callback cuando se hace clic en una miniatura."""
        logger.debug(f"Clic en miniatura: {image_path}")
        # Pasar tanto la ruta de la imagen como el botón
        self.on_image_selected_cb(image_path, button)
    
    def on_change_folder(self, button):
        """Muestra un diálogo personalizado para cambiar la carpeta de imágenes."""
        # Crear ventana de diálogo
        dialog = Gtk.Window()
        dialog.set_title(i18n.t('sidebar.select_folder'))
        dialog.set_modal(True)
        dialog.set_transient_for(self.get_root())
        dialog.set_default_size(500, 400)
        
        # Box principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_top(10)
        main_box.set_margin_bottom(10)
        main_box.set_margin_start(10)
        main_box.set_margin_end(10)
        dialog.set_child(main_box)
        
        # Label de instrucciones
        label = Gtk.Label(label=i18n.t('sidebar.select_folder_instruction'))
        label.set_xalign(0)
        main_box.append(label)
        
        # Área con scroll para el árbol de carpetas
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_hexpand(True)
        main_box.append(scroll)
        
        # TreeView con modelo
        store = Gtk.TreeStore(str, str)  # (nombre visible, ruta completa)
        tree = Gtk.TreeView(model=store)
        tree.set_headers_visible(False)
        scroll.set_child(tree)
        
        # Columna de texto
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Carpeta", renderer, text=0)
        tree.append_column(column)
        
        # Variable para guardar la carpeta seleccionada
        selected_folder = [self.pictures_dir]  # Lista mutable para closure
        
        def on_tree_selection_changed(selection):
            model, treeiter = selection.get_selected()
            if treeiter:
                selected_folder[0] = model[treeiter][1]
        
        selection = tree.get_selection()
        selection.connect("changed", on_tree_selection_changed)
        
        # Poblar árbol con carpetas comunes y sus subdirectorios
        def add_folder_to_tree(parent_iter, folder_path, max_depth=2, current_depth=0):
            try:
                if current_depth >= max_depth:
                    return
                    
                for entry in sorted(Path(folder_path).iterdir()):
                    if entry.is_dir() and not entry.name.startswith('.'):
                        folder_iter = store.append(parent_iter, [f"📁 {entry.name}", str(entry)])
                        # Agregar subdirectorios recursivamente
                        if current_depth < max_depth - 1:
                            add_folder_to_tree(folder_iter, entry, max_depth, current_depth + 1)
            except PermissionError:
                pass
            except Exception as e:
                logger.error(f"Error listando {folder_path}: {e}")
        
        # Agregar carpetas principales
        home = Path.home()
        
        # Home
        home_iter = store.append(None, [f"🏠 {home.name}", str(home)])
        add_folder_to_tree(home_iter, home, max_depth=3)
        
        # Carpetas comunes
        common_folders = ['Documents', 'Downloads', 'Pictures', 'Music', 'Videos', 
                         'Documentos', 'Descargas', 'Imágenes', 'Música', 'Vídeos']
        
        for folder_name in common_folders:
            folder_path = home / folder_name
            if folder_path.exists() and folder_path.is_dir():
                folder_iter = store.append(None, [f"📁 {folder_name}", str(folder_path)])
                add_folder_to_tree(folder_iter, folder_path, max_depth=2)
        
        # Expandir home por defecto
        tree.expand_row(Gtk.TreePath.new_first(), False)
        
        # Seleccionar carpeta actual si está en el árbol
        def select_current_folder():
            def search_and_select(model, path, iter, search_path):
                if model[iter][1] == search_path:
                    tree.get_selection().select_iter(iter)
                    tree.scroll_to_cell(path, None, True, 0.5, 0.5)
                    return True
                return False
            
            store.foreach(search_and_select, self.pictures_dir)
        
        GLib.idle_add(select_current_folder)
        
        # Botones
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
        
        dialog.present()
    
    def on_folder_dialog_select(self, dialog, folder_path):
        """Callback cuando se confirma la selección de carpeta."""
        if folder_path and os.path.exists(folder_path):
            self.pictures_dir = folder_path
            logger.debug(f"Nueva carpeta seleccionada: {self.pictures_dir}")
            self.load_images()
        dialog.close()