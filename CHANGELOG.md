# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [0.3.5] - Sin Fecha

### Añadido
- Diálogo "Acerca de" con información de la aplicación
- Botones para limpiar fondos de pantalla de cada monitor
- Números de monitor en el preview para identificación visual

### Mejorado
- Interfaz de usuario más intuitiva con opciones de limpieza rápida

## [0.3.0] - Sin Fecha

### Añadido
- Números de monitor en el preview con fondo semitransparente
- Fuente embebida (DejaVuSans-Bold.ttf) para compatibilidad universal
- Escalado inteligente de etiquetas según tamaño del preview
- Manejo robusto de errores con mensajes detallados
- Diagnósticos mejorados para formatos de imagen problemáticos

### Mejorado
- Visualización más clara de la configuración de monitores
- Mejor legibilidad de números en previews oscuros y claros

## [0.2.6] - Sin Fecha

### Añadido
- Panel lateral con miniaturas de imágenes
- Navegación visual de carpetas para selección de wallpapers
- Soporte inicial para imágenes en formato AVIF
- Selector de carpetas personalizado con árbol de directorios
- Botones de actualización y cambio de carpeta en sidebar

### Mejorado
- Experiencia de usuario más fluida con selección visual
- Detección automática del directorio de imágenes del sistema

## [0.2.0] - Sin Fecha

### Añadido
- Soporte multi-monitor completo
- Vista previa en tiempo real de la configuración
- Múltiples modos de visualización:
  - Rellenar (Fill)
  - Ajustar (Fit)
  - Estirar (Stretch)
  - Centrar (Center)
  - Mosaico (Tile)
- Selector de color de fondo personalizado
- Auto-guardado de configuración
- Soporte multi-idioma (Español e Inglés)

### Soporte de Formatos
- PNG, JPG, JPEG
- BMP, WebP
- GIF, AVIF

## [0.1.0] - Sin Fecha

### Añadido
- Primera versión funcional
- Interfaz GTK4 básica
- Configuración de un monitor
- Aplicación de wallpaper via gsettings

---

## Notas de Desarrollo

### Empaquetado
- **AppImage**: Paquete universal para distribuciones Linux
- **Flatpak**: Sandbox con aislamiento completo
- **Docker**: Soporte para desarrollo y testing

### Dependencias
- Python 3.10+
- GTK4
- PyGObject
- Pillow (con soporte AVIF)
- pyyaml
- python-i18n

### Plataformas Soportadas
- Linux con GNOME (X11/Wayland)
- Otros escritorios con soporte gsettings

---

## Enlaces

- [Repositorio](https://github.com/jsnoriegam/multiwall)
- [Reportar Issues](https://github.com/jsnoriegam/multiwall/issues)
- [Buy Me A Coffee](https://www.buymeacoffee.com/jsnoriegam)