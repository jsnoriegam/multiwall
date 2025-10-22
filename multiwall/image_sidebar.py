import os
import i18n
from pathlib import Path
from gi import require_version
require_version('Gtk', '4.0')
from gi.repository import Gtk, GdkPixbuf, GLib, Gio

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
            print(f"El directorio {self.pictures_dir} no existe")
            return
        
        # Buscar archivos de imagen
        try:
            for entry in sorted(Path(self.pictures_dir).iterdir()):
                if entry.is_file() and entry.suffix.lower() in IMAGE_EXTENSIONS:
                    print(f"Agregando imagen: {entry}")
                    self.current_images.append(str(entry))
        except Exception as e:
            print(f"Error listando imágenes: {e}")
            return
        
        print(f"Encontradas {len(self.current_images)} imágenes en {self.pictures_dir}")
        
        # Crear miniaturas
        for image_path in self.current_images:
            self.create_thumbnail(image_path)
    
    def create_thumbnail(self, image_path):
        """Crea una miniatura para una imagen."""
        try:
            # Crear contenedor para la miniatura
            button = Gtk.Button()
            button.add_css_class('flat')
            button.set_tooltip_text(os.path.basename(image_path))
            
            # Box para la imagen y nombre - más compacto
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            
            # Cargar y escalar la imagen
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    image_path,
                    THUMBNAIL_SIZE,
                    THUMBNAIL_SIZE,
                    True  # preserve_aspect_ratio
                )
            except Exception as e:
                print(f"Error al cargar la imagen {image_path}: {e}")
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
            
        except Exception as e:
            print(f"Error creando miniatura para {image_path}: {e}")
    
    def on_thumbnail_clicked(self, button, image_path):
        """Callback cuando se hace clic en una miniatura."""
        print(f"Clic en miniatura: {image_path}")
        # Pasar tanto la ruta de la imagen como el botón
        self.on_image_selected_cb(image_path, button)
    
    def on_change_folder(self, button):
        """Muestra un diálogo para cambiar la carpeta de imágenes."""
        dialog = Gtk.FileDialog()
        dialog.set_title(i18n.t('sidebar.select_folder'))
        
        # Establecer carpeta inicial
        if os.path.exists(self.pictures_dir):
            initial_folder = Gio.File.new_for_path(self.pictures_dir)
            dialog.set_initial_folder(initial_folder)
        
        # Abrir diálogo de selección de carpeta
        dialog.select_folder(self.get_root(), None, self.on_folder_selected)
    
    def on_folder_selected(self, dialog, result):
        """Callback cuando se selecciona una nueva carpeta."""
        try:
            folder = dialog.select_folder_finish(result)
            if folder:
                self.pictures_dir = folder.get_path()
                print(f"Nueva carpeta seleccionada: {self.pictures_dir}")
                self.load_images()
        except Exception as e:
            # Usuario canceló o error
            print(f"Selección de carpeta cancelada o error: {e}")